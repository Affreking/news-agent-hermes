"""One-shot SMTP sender. Dry-run by default. No scheduling, no automatic retries."""
import argparse
import hashlib
import json
import os
import re
import smtplib
import sqlite3
import ssl
import sys
from datetime import datetime, timezone
from email.utils import format_datetime, make_msgid
from pathlib import Path
import welispeak as w


def preflight(data, config, now):
    end = w.validate(data)
    age = (now-end).total_seconds()
    if not 0 <= age <= 7200:
        raise ValueError('Edition stale or future; generate a new edition')
    if data.get('archive_example') or data.get('approved_for_send') is not True:
        raise ValueError('Archive or unapproved edition cannot be sent')
    if config.get('send_authorized') is not True:
        raise ValueError('Sending not authorized')
    if config.get('recipient') != w.RECIPIENT or config.get('smtp_port') != 587:
        raise ValueError('Recipient or SMTP port rejected')
    if not isinstance(config.get('smtp_host'), str) or not re.fullmatch(r'[A-Za-z0-9.-]+', config['smtp_host']):
        raise ValueError('SMTP host required')
    sender = config.get('sender_email')
    if not isinstance(sender, str) or not re.fullmatch(r'[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+', sender):
        raise ValueError('Valid configured sender required')
    if sender.lower() == 'newsletter@welispeak.com':
        raise ValueError('Future sender disabled in V6')


def reserve(db_path, data):
    # Key one send per Abidjan/UTC edition date and recipient, even if content changes.
    key = datetime.fromisoformat(data['cutoff']).astimezone(timezone.utc).date().isoformat()+':'+w.RECIPIENT
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    descriptor = os.open(db_path, os.O_CREAT | os.O_RDWR, 0o600)
    os.close(descriptor)
    os.chmod(db_path, 0o600)
    db = sqlite3.connect(db_path, timeout=15)
    db.execute('CREATE TABLE IF NOT EXISTS deliveries (edition TEXT PRIMARY KEY, digest TEXT NOT NULL, status TEXT NOT NULL, updated TEXT NOT NULL)')
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO deliveries VALUES (?, ?, ?, ?)', (key, digest, 'attempting', datetime.now(timezone.utc).isoformat()))
        db.commit()  # Durable reservation before any SMTP side effect.
    except sqlite3.IntegrityError:
        db.rollback(); db.close()
        raise ValueError('Edition already attempted; no automatic retry') from None
    return db, key


def deliver(data, config, db_path, password, smtp_factory=smtplib.SMTP):
    preflight(data, config, datetime.now(timezone.utc))
    if not password:
        raise ValueError('Required environment secret missing')
    # Build before reserving: deterministic local render errors should not consume a send.
    from email.parser import BytesParser
    from email.policy import SMTP
    msg = BytesParser(policy=SMTP).parsebytes(w.build(data, config)['mime'])
    del msg['X-Unsent']; msg['Date'] = format_datetime(datetime.now(timezone.utc)); msg['Message-ID'] = make_msgid()
    db, key = reserve(db_path, data)
    try:
        # Every exception after durable reservation is conservatively ambiguous.
        preflight(data, config, datetime.now(timezone.utc))
        with smtp_factory(config['smtp_host'], 587, timeout=30) as client:
            client.ehlo()
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
            client.login(config.get('smtp_username') or config['sender_email'], password)
            preflight(data, config, datetime.now(timezone.utc))
            refused = client.send_message(msg, from_addr=config['sender_email'], to_addrs=[w.RECIPIENT])
            if refused:
                raise RuntimeError('Recipient refused')
        db.execute('UPDATE deliveries SET status=?, updated=? WHERE edition=?', ('accepted', datetime.now(timezone.utc).isoformat(), key)); db.commit()
    except Exception:
        db.execute('UPDATE deliveries SET status=?, updated=? WHERE edition=?', ('ambiguous', datetime.now(timezone.utc).isoformat(), key)); db.commit()
        raise RuntimeError('SMTP outcome ambiguous or failed; details masked. No blind retry; inspect provider delivery state.') from None
    finally:
        db.close()
    return {'status': 'accepted_by_smtp', 'inbox_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input'); parser.add_argument('--config', default=str(w.ROOT/'config.example.json'))
    parser.add_argument('--state', default=str(w.ROOT/'runtime/delivery.sqlite3'))
    parser.add_argument('--send', action='store_true')
    args = parser.parse_args()
    try:
        config = w.load_config(args.config)
        data = json.loads(Path(args.input).read_text())
        if not args.send:
            result = w.build(data, config)
            print(json.dumps({'dry_run': True, 'sent': False, 'mime_bytes': len(result['mime']), 'archive_example': bool(data.get('archive_example')), 'freshness_checked_for_send': False}))
            return 0
        preflight(data, config, datetime.now(timezone.utc))
        password = os.environ.get('WELISPEAK_SMTP_PASSWORD')
        if not password:
            raise ValueError('Required environment secret missing')
        state = Path(args.state); state.parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(deliver(data, config, state, password)))
        return 0
    except Exception:
        # Never echo exceptions/input/server replies/credentials to CLI output.
        print('Blocked or unsuccessful; no automatic retry. Check authorization, freshness and persistent ledger; SMTP details masked.', file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())

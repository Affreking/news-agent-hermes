"""Read-only secret/policy audit of Git candidates; never prints secret values.

Run before staging/commit. Report is local and ignored by Git. A pattern scan
is defense in depth, not proof that every confidential datum is absent.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from email.parser import BytesParser
from email.policy import default

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'github_token': rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
    'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'aws_key_id': rb'\bAKIA[A-Z0-9]{16}\b',
    'api_key': rb'\bsk-[A-Za-z0-9_-]{30,}',
    'credential_url': rb'https?://[^\s/<>\"\x27]+:[^\s/<>\"\x27]+@',
    'literal_secret': rb'(?im)^\s*(?:MAIL_PASSWORD|WELISPEAK_SMTP_PASSWORD|api_key|password|secret|oauth_token|access_token)\s*[:=]\s*[\x22\x27](?!\$\{)[^\x22\x27\r\n]{8,}[\x22\x27]',
}


def git_list(*args):
    result = subprocess.run(['git', '-C', str(ROOT), *args, '-z'], check=True, capture_output=True)
    return [os.fsdecode(name) for name in result.stdout.split(b'\0') if name]


def main():
    names = sorted(set(git_list('ls-files', '--cached')) | set(git_list('ls-files', '--others', '--exclude-standard')))
    ignored = git_list('ls-files', '--others', '--ignored', '--exclude-standard')
    findings, inventory, path_notes, contact_paths = [], [], [], []
    # Compare actual environment credentials in memory only; never save or echo them.
    known_secrets = [v.encode() for k, v in os.environ.items()
                     if len(v) >= 8 and any(x in k.upper() for x in ('PASSWORD', 'TOKEN', 'API_KEY', 'SECRET'))]
    for name in names:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            findings.append({'path': name, 'rule': 'nonregular_or_symlink'})
            continue
        lower = name.lower()
        if path.name.startswith('.env') and path.name not in ('.env.example', '.env.template'):
            findings.append({'path': name, 'rule': 'environment_file'})
        if path.name == 'mail_settings.json' or '.runtime/' in name or re.search(r'\.(sqlite\d*|db|log|jsonl)(-|$)', lower):
            findings.append({'path': name, 'rule': 'private_runtime_file'})
        blob = path.read_bytes()
        inventory.append({'path': name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
        for rule, pattern in RULES.items():
            count = len(re.findall(pattern, blob))
            if count:
                findings.append({'path': name, 'rule': rule, 'count': count})
        if any(secret in blob for secret in known_secrets):
            findings.append({'path': name, 'rule': 'matches_live_environment_secret'})
        if b'/Users/' in blob or b'127.0.0.1' in blob:
            path_notes.append(name)
        if re.search(rb'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', blob):
            contact_paths.append(name)
        if path.suffix.lower() == '.eml':
            msg = BytesParser(policy=default).parsebytes(blob)
            audited_fixture = (name == 'portable_welispeak/example_output/newsletter_unsent.eml'
                               and msg.get('X-Unsent') == '1'
                               and msg.get('To') == 'ndriaffre@gmail.com'
                               and not any(msg.get(h) for h in ('Cc', 'Bcc', 'From', 'Authorization')))
            if any(msg.get(header) for header in ('To', 'Cc', 'Bcc', 'From', 'Authorization')) and not audited_fixture:
                findings.append({'path': name, 'rule': 'addressed_or_authenticated_eml'})
        # PNG artwork is kept, but not unexpected metadata with private information.
        if path.suffix.lower() == '.png' and any(x in blob for x in (b'GPSLatitude', b'GPSLongitude', b'/Users/')):
            findings.append({'path': name, 'rule': 'image_private_metadata'})
    report = {
        'candidate_count': len(inventory), 'ignored_count': len(ignored),
        'blocking_findings': findings, 'inventory': inventory, 'excluded_paths': sorted(ignored),
        'portability_review_paths': path_notes, 'email_like_content_paths': contact_paths,
        'limitations': ['Pattern scan plus in-memory comparison, not an exhaustive confidentiality guarantee.',
                        'No Keychain, Hermes credentials, raw secrets or private settings were read.',
                        'Contact literals and local paths require owner review even in a private repository.'],
        'remote_created': False, 'pushed': False,
    }
    out = ROOT / '.repo-audit'
    out.mkdir(exist_ok=True)
    (out / 'security_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (out / 'FILES_TO_VERSION.txt').write_text('\n'.join(entry['path'] for entry in inventory) + '\n')
    (out / 'FILES_EXCLUDED.txt').write_text('\n'.join(sorted(ignored)) + '\n')
    print(json.dumps({'candidate_count': len(inventory), 'ignored_count': len(ignored),
                      'blocking_findings': findings, 'local_report': str(out / 'security_report.json'),
                      'contact_review_files': len(contact_paths), 'portability_review_files': len(path_notes)}, ensure_ascii=False))
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())

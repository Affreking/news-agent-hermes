"""Offline durable publication numbering. No transport and no scheduler."""
import sqlite3
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, date as Date
from zoneinfo import ZoneInfo

LAUNCH = Date(2026, 11, 1)


class Registry:
    def __init__(self, path, *, environment, now=None):
        self.path = str(path)
        if self.path == ':memory:' or self.path.startswith('file:'):
            raise ValueError('Durable filesystem path required')
        if environment == 'production' and now is not None:
            raise ValueError('Production must use the real clock')
        if environment not in ('test', 'production'):
            raise ValueError('Explicit test or production environment required')
        self.environment = environment
        self.now = now or (lambda: datetime.now(timezone.utc))
        with self._transaction() as db:
            for statement in '''
                CREATE TABLE IF NOT EXISTS environment (id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), last INTEGER NOT NULL);
                INSERT OR IGNORE INTO state VALUES (1,0);
                CREATE TABLE IF NOT EXISTS editions (
                    bulletin TEXT NOT NULL, date TEXT NOT NULL, number INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL, status TEXT NOT NULL,
                    PRIMARY KEY (bulletin,date), UNIQUE(bulletin,number));
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY, token TEXT, event TEXT, evidence TEXT,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
            '''.split(';'):
                if statement.strip():
                    db.execute(statement)
            db.execute('INSERT OR IGNORE INTO environment VALUES(1,?)', (environment,))
            if db.execute('SELECT name FROM environment WHERE id=1').fetchone()[0] != environment:
                raise ValueError('Database environment mismatch')

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def journal(self):
        with self._transaction() as db:
            return [dict(row) for row in db.execute('SELECT * FROM journal ORDER BY id')]

    def last_number(self):
        with self._transaction() as db:
            return db.execute('SELECT last FROM state WHERE id=1').fetchone()[0]

    def edition(self, date):
        with self._transaction() as db:
            row = db.execute('SELECT * FROM editions WHERE bulletin=? AND date=?', ('WELISPEAK', date)).fetchone()
            return dict(row, label=f'Nº{row["number"]:03d}') if row else None

    def reserve(self, date, *, approved_for_send=False):
        day = Date.fromisoformat(date)
        if day.isoformat() != date:
            raise ValueError('Canonical YYYY-MM-DD required')
        clock = self.now()
        if clock.utcoffset() is None:
            raise ValueError('Timezone-aware clock required')
        if approved_for_send is not True or day < LAUNCH or day > clock.astimezone(ZoneInfo('Africa/Abidjan')).date():
            raise ValueError('Human approval and non-future official date required')
        token = uuid.uuid4().hex
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM editions WHERE status IN ('reserved','ambiguous')").fetchone():
                raise ValueError('Durable publication lock held; no automatic retry')
            if db.execute('SELECT 1 FROM editions WHERE date=?', (date,)).fetchone():
                raise ValueError('Edition already exists; use resend/correction metadata')
            n = db.execute('SELECT last+1 FROM state WHERE id=1').fetchone()[0]
            if n == 1 and day != LAUNCH:
                raise ValueError('First official edition must be 2026-11-01')
            db.execute('INSERT INTO editions VALUES (?,?,?,?,?)', ('WELISPEAK', date, n, token, 'reserved'))
            db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)',
                       (token, 'reserved', json.dumps({'bulletin': 'WELISPEAK', 'date': date, 'number': n,
                                                     'environment': self.environment, 'approved_for_send': True})))
        return self.edition(date)

    def metadata(self, date, *, mode='resend', language=None, destination=None, correction_reason=''):
        row = self.edition(date)
        if mode not in ('resend', 'correction') or not row or row['status'] != 'published':
            raise ValueError('Existing published edition required')
        if mode == 'correction':
            if not correction_reason.strip():
                raise ValueError('Correction reason required')
            with self._transaction() as db:
                db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)',
                           (row['token'], 'correction', correction_reason))
        return dict(row, mode=mode, corrected=mode == 'correction', language=language,
                    destination=destination, timezone='Africa/Abidjan', correction_reason=correction_reason)

    def ambiguous(self, token, *, evidence):
        with self._transaction() as db:
            row = db.execute('SELECT * FROM editions WHERE token=?', (token,)).fetchone()
            if not row or row['status'] != 'reserved' or not evidence.strip():
                raise ValueError('Reserved token and evidence required')
            db.execute("UPDATE editions SET status='ambiguous' WHERE token=?", (token,))
            db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)', (token, 'ambiguous', evidence))

    def reconcile(self, token, *, published, operator, evidence):
        if type(published) is not bool or not operator.strip() or not evidence.strip():
            raise ValueError('Explicit manual decision, operator and evidence required')
        with self._transaction() as db:
            row = db.execute('SELECT * FROM editions WHERE token=?', (token,)).fetchone()
            if not row or row['status'] not in ('ambiguous', 'reserved'):
                raise ValueError('Only blocked attempts can be manually reconciled')
            if published:
                db.execute("UPDATE editions SET status='published' WHERE token=?", (token,))
                db.execute('UPDATE state SET last=? WHERE id=1', (row['number'],))
            else:
                db.execute('DELETE FROM editions WHERE token=?', (token,))
            db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)',
                       (token, 'reconciled_published' if published else 'reconciled_released', operator + ': ' + evidence))

    def fail(self, token, *, evidence):
        with self._transaction() as db:
            row = db.execute('SELECT * FROM editions WHERE token=?', (token,)).fetchone()
            if not row or row['status'] != 'reserved' or not evidence.strip():
                raise ValueError('Only definite unpublished failures may release a reservation')
            db.execute('DELETE FROM editions WHERE token=?', (token,))
            db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)', (token, 'released', evidence))

    def confirm(self, token, *, evidence):
        with self._transaction() as db:
            row = db.execute('SELECT * FROM editions WHERE token=?', (token,)).fetchone()
            if not row:
                raise ValueError('Unknown token')
            if row['status'] == 'published':
                return
            if row['status'] != 'reserved' or not evidence.strip():
                raise ValueError('Only reserved editions with evidence can be confirmed')
            db.execute('UPDATE editions SET status=? WHERE token=?', ('published', token))
            db.execute('UPDATE state SET last=? WHERE id=1', (row['number'],))
            db.execute('INSERT INTO journal(token,event,evidence) VALUES (?,?,?)', (token, 'published', evidence))

import importlib
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

NOW = datetime(2026, 11, 2, tzinfo=timezone.utc)


import sqlite3
import multiprocessing
from datetime import timedelta


def compete(path, event, queue):
    from registry import Registry
    r = Registry(path, environment='test', now=lambda: NOW)
    event.wait(10)
    try:
        queue.put(('won', r.reserve('2026-11-01', approved_for_send=True)['token']))
    except ValueError:
        queue.put(('blocked', None))


def die_mid_transaction(path):
    import os
    db = sqlite3.connect(path, isolation_level=None)
    db.execute('BEGIN IMMEDIATE')
    db.execute('UPDATE state SET last=999 WHERE id=1')
    os._exit(23)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'test.sqlite3'

    def registry(self):
        return importlib.import_module('registry').Registry(self.path, environment='test', now=lambda: NOW)

    def test_reserve_durable_number_but_confirm_alone_advances_counter(self):
        r = self.registry()
        attempt = r.reserve('2026-11-01', approved_for_send=True)
        self.assertEqual(attempt['label'], 'Nº001')
        self.assertEqual(r.last_number(), 0)
        self.assertEqual(self.registry().edition('2026-11-01')['token'], attempt['token'])
        r.confirm(attempt['token'], evidence='publication receipt 001')
        self.assertEqual(self.registry().last_number(), 1)
        self.assertEqual(r.edition('2026-11-01')['status'], 'published')

    def test_gates_first_date_actual_abidjan_clock_and_human_approval(self):
        module = importlib.import_module('registry')
        r = self.registry()
        for day, approval in [('2026-10-31', True), ('2026-11-02', True), ('2026-11-01', False)]:
            with self.assertRaises(ValueError):
                r.reserve(day, approved_for_send=approval)
        early = module.Registry(self.path, environment='test', now=lambda: datetime(2026, 10, 22, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            early.reserve('2026-11-01', approved_for_send=True)
        self.assertEqual(r.last_number(), 0)
        self.assertIsNone(r.edition('2026-11-01'))

    def test_durable_lock_blocks_other_dates_and_duplicate_publication_is_idempotent(self):
        r = self.registry()
        a = r.reserve('2026-11-01', approved_for_send=True)
        with self.assertRaises(ValueError):
            self.registry().reserve('2026-11-02', approved_for_send=True)
        with self.assertRaises(ValueError):
            self.registry().reserve('2026-11-01', approved_for_send=True)
        r.confirm(a['token'], evidence='DATA accepted')
        second = r.reserve('2026-11-02', approved_for_send=True)
        r.confirm(second['token'], evidence='second accepted')
        r.confirm(a['token'], evidence='repeat callback')
        self.assertEqual(r.last_number(), 2)
        with self.assertRaises(ValueError):
            r.reserve('2026-11-01', approved_for_send=True)
        self.assertEqual(len([j for j in r.journal() if j['event'] == 'published']), 2)

    def test_failure_before_publication_releases_number_and_audits_old_token(self):
        r = self.registry()
        a = r.reserve('2026-11-01', approved_for_send=True)
        r.fail(a['token'], evidence='definite failure before DATA acceptance')
        b = self.registry().reserve('2026-11-01', approved_for_send=True)
        self.assertNotEqual(a['token'], b['token'])
        self.assertEqual(b['label'], 'Nº001')
        self.assertEqual(r.last_number(), 0)
        self.assertIn('released', [j['event'] for j in r.journal()])
        with self.assertRaises(ValueError):
            r.confirm(a['token'], evidence='stale acceptance')

    def test_ambiguous_freezes_until_audited_manual_reconciliation(self):
        r = self.registry()
        a = r.reserve('2026-11-01', approved_for_send=True)
        r.ambiguous(a['token'], evidence='connection lost during DATA')
        reopened = self.registry()
        self.assertEqual(reopened.edition('2026-11-01')['status'], 'ambiguous')
        for operation in [lambda: reopened.reserve('2026-11-02', approved_for_send=True),
                          lambda: reopened.confirm(a['token'], evidence='retry'),
                          lambda: reopened.fail(a['token'], evidence='retry')]:
            with self.assertRaises(ValueError):
                operation()
        with self.assertRaises(ValueError):
            r.reconcile(a['token'], published=True, operator='', evidence='checked')
        r.reconcile(a['token'], published=True, operator='human editor', evidence='server log confirms acceptance')
        self.assertEqual(r.last_number(), 1)
        self.assertIn('reconciled_published', [j['event'] for j in r.journal()])
        b = r.reserve('2026-11-02', approved_for_send=True)
        r.ambiguous(b['token'], evidence='crashed')
        r.reconcile(b['token'], published=False, operator='human editor', evidence='server confirms no publication')
        self.assertEqual(r.reserve('2026-11-02', approved_for_send=True)['number'], 2)

    def test_environment_marker_prevents_production_database_in_tests(self):
        self.registry()
        with self.assertRaises(ValueError):
            importlib.import_module('registry').Registry(self.path, environment='production')
        with self.assertRaises(ValueError):
            importlib.import_module('registry').Registry(self.path, environment='typo')

    def test_eight_processes_one_winner_durable_lock_and_crash_rollback(self):
        r = self.registry()
        ctx = multiprocessing.get_context('spawn')
        event, queue = ctx.Event(), ctx.Queue()
        workers = [ctx.Process(target=compete, args=(str(self.path), event, queue)) for _ in range(8)]
        for worker in workers:
            worker.start()
        event.set()
        results = [queue.get(timeout=30) for _ in workers]
        for worker in workers:
            worker.join(30)
            self.assertEqual(worker.exitcode, 0)
        self.assertEqual(sum(result[0] == 'won' for result in results), 1)
        self.assertEqual(r.last_number(), 0)
        self.assertEqual(r.edition('2026-11-01')['status'], 'reserved')
        crashed = ctx.Process(target=die_mid_transaction, args=(str(self.path),))
        crashed.start(); crashed.join(30)
        self.assertEqual(crashed.exitcode, 23)
        self.assertEqual(self.registry().last_number(), 0)
        self.assertEqual(len(r.journal()), 1)

    def test_resend_correction_language_destination_share_number_without_consumption(self):
        r = self.registry()
        a = r.reserve('2026-11-01', approved_for_send=True)
        r.confirm(a['token'], evidence='accepted')
        for language in ('fr', 'en'):
            for destination in ('web', 'archive', 'recipient-a', 'recipient-b'):
                m = r.metadata('2026-11-01', mode='resend', language=language, destination=destination)
                self.assertEqual(m['label'], 'Nº001')
        corrected = r.metadata('2026-11-01', mode='correction', correction_reason='Corrected source attribution')
        self.assertEqual(corrected['number'], 1)
        self.assertTrue(corrected['corrected'])
        self.assertEqual(r.last_number(), 1)
        self.assertEqual(r.reserve('2026-11-02', approved_for_send=True)['number'], 2)

    def test_minimum_three_digits_with_real_thousand_publications(self):
        module = importlib.import_module('registry')
        far = datetime(2030, 1, 1, tzinfo=timezone.utc)
        r = module.Registry(self.path, environment='test', now=lambda: far)
        for index in range(1000):
            day = (datetime(2026, 11, 1) + timedelta(days=index)).date().isoformat()
            a = r.reserve(day, approved_for_send=True)
            r.confirm(a['token'], evidence='test publication receipt')
        self.assertEqual(a['label'], 'Nº1000')
        self.assertEqual(r.last_number(), 1000)
        self.assertEqual(r.metadata(day, mode='resend')['label'], 'Nº1000')

    def test_rejects_noncanonical_dates_and_fake_production_clock(self):
        r = self.registry()
        with self.assertRaises(ValueError):
            r.reserve('20261101', approved_for_send=True)
        with self.assertRaises(ValueError):
            importlib.import_module('registry').Registry(self.path, environment='production', now=lambda: NOW)
        with self.assertRaises(ValueError):
            importlib.import_module('registry').Registry(':memory:', environment='test')

    def test_sqlite_abort_rolls_back_reservation_and_confirmation_as_single_transactions(self):
        r = self.registry()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_reserve BEFORE INSERT ON journal WHEN NEW.event='reserved' BEGIN SELECT RAISE(ABORT,'test fault'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            r.reserve('2026-11-01', approved_for_send=True)
        self.assertIsNone(r.edition('2026-11-01'))
        self.assertEqual(r.last_number(), 0)
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER reject_reserve')
        a = r.reserve('2026-11-01', approved_for_send=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_confirm BEFORE INSERT ON journal WHEN NEW.event='published' BEGIN SELECT RAISE(ABORT,'test fault'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            r.confirm(a['token'], evidence='test acceptance')
        self.assertEqual(r.edition('2026-11-01')['status'], 'reserved')
        self.assertEqual(r.last_number(), 0)
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER reject_confirm')
        r.confirm(a['token'], evidence='same acceptance after storage recovery')
        self.assertEqual(r.last_number(), 1)

    def test_release_journal_retains_identity_and_reason_after_deleted_reservation(self):
        import json
        r = self.registry()
        a = r.reserve('2026-11-01', approved_for_send=True)
        r.fail(a['token'], evidence='definite DATA rejection')
        reserved = next(j for j in r.journal() if j['event'] == 'reserved')
        identity = json.loads(reserved['evidence'])
        self.assertEqual(identity['date'], '2026-11-01')
        self.assertEqual(identity['number'], 1)
        self.assertEqual(identity['environment'], 'test')
        self.assertTrue(reserved['created_at'])


if __name__ == '__main__':
    unittest.main()

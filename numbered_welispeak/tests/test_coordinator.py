import importlib
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timezone


class CoordinatorTests(unittest.TestCase):
    def registry(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return importlib.import_module('registry').Registry(Path(temp.name)/'test.sqlite3', environment='test', now=lambda: datetime(2026, 11, 2, tzinfo=timezone.utc))
    def test_commit_at_data_acceptance_before_quit_error_and_recipients_share_identity(self):
        r = self.registry()
        Coordinator = importlib.import_module('coordinator').PublicationCoordinator
        c = Coordinator(r)
        a = c.prepare('2026-11-01', approved_for_send=True)
        for lang in ('fr', 'en'):
            for recipient in ('a@example.invalid', 'b@example.invalid'):
                self.assertEqual(c.identity(a['token'], language=lang, destination=recipient)['label'], 'Nº001')
        c.smtp_result(a['token'], outcome='accepted', evidence='250 DATA queued id=123')
        self.assertEqual(r.last_number(), 1)
        c.quit_failed(a['token'], evidence='disconnect after accepted DATA')
        self.assertEqual(r.edition('2026-11-01')['status'], 'published')
        c.smtp_result(a['token'], outcome='accepted', evidence='duplicate callback')
        self.assertEqual(r.last_number(), 1)

    def test_explicit_failure_releases_but_disconnect_during_data_freezes(self):
        r = self.registry()
        c = importlib.import_module('coordinator').PublicationCoordinator(r)
        a = c.prepare('2026-11-01', approved_for_send=True)
        c.smtp_result(a['token'], outcome='failure', evidence='550 DATA rejected')
        b = c.prepare('2026-11-01', approved_for_send=True)
        self.assertEqual(b['number'], 1)
        c.smtp_result(b['token'], outcome='ambiguous', evidence='disconnect while awaiting DATA result')
        self.assertEqual(r.edition('2026-11-01')['status'], 'ambiguous')
        with self.assertRaises(ValueError):
            c.prepare('2026-11-01', approved_for_send=True)
        self.assertEqual(r.last_number(), 0)


if __name__ == '__main__':
    import unittest
    unittest.main()

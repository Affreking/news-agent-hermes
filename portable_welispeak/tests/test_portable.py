import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from email import policy
from email.parser import BytesParser

ROOT = Path(__file__).resolve().parents[1]

class RenderTests(unittest.TestCase):
    def test_scene_selection_and_audience_urls(self):
        import welispeak as w
        data = json.loads((ROOT/'examples/archive_20261022.json').read_text())
        data['articles'][0]['scene_index'] = 5
        config = w.load_config(ROOT/'config.example.json')
        config.update(whatsapp_channel_url='https://whatsapp.com/channel/TEST_ONLY', linkedin_url='https://www.linkedin.com/company/TEST_ONLY', linkedin_kind='page')
        out = w.build(data, config)
        first = out['html'].split('id="english"')[0]
        self.assertIn('src="cid:welispeak-art5"', first.split('Illustration générique')[0])
        self.assertIn('href="https://whatsapp.com/channel/TEST_ONLY"', first)
        self.assertIn('Page LinkedIn', first)
        for value in ('http://invalid.test', 'javascript:alert(1)', ''):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'config.json'
                path.write_text(json.dumps(dict(config, whatsapp_channel_url=value)))
                with self.assertRaises(ValueError): w.load_config(path)

    def test_reject_invalid_scene_and_temporal_inputs(self):
        import welispeak as w
        original = json.loads((ROOT/'examples/archive_20261022.json').read_text())
        for value in (-1, 6, 'not-index'):
            data = json.loads(json.dumps(original)); data['articles'][0]['scene_index'] = value
            with self.assertRaises(ValueError): w.validate(data)
        data = json.loads(json.dumps(original)); data['articles'][0]['published_at'] = '2026-10-22T12:00:00'
        with self.assertRaises(ValueError): w.validate(data)
        data = json.loads(json.dumps(original)); data['articles'][1]['url'] = data['articles'][0]['url']
        with self.assertRaises(ValueError): w.validate(data)
        data = json.loads(json.dumps(original)); data['articles'][0]['en']['summary'] = data['articles'][0]['fr']['summary']
        with self.assertRaises(ValueError): w.validate(data)

    def test_real_archive_bilingual_mime(self):
        self.assertTrue((ROOT / 'welispeak.py').exists(), 'portable renderer not implemented')
        import welispeak as w
        data = json.loads((ROOT / 'examples/archive_20261022.json').read_text())
        config = w.load_config(ROOT / 'config.example.json')
        self.assertIsNone(config['linkedin_kind'])
        out = w.build(data, config)
        msg = BytesParser(policy=policy.default).parsebytes(out['mime'])
        html = msg.get_body(preferencelist=('html',)).get_content()
        text = msg.get_body(preferencelist=('plain',)).get_content()
        self.assertEqual(len([p for p in msg.walk() if p.get_content_maintype() == 'image']), 7)
        self.assertEqual(html.count('src="cid:welispeak-logo"'), 1)
        self.assertLess(html.index('id="francais"'), html.index('id="english"'))
        self.assertIn('href="#english"', html)
        self.assertIn('href="#francais"', html)
        self.assertIn('Why it matters', html)
        self.assertIn('Votre essentiel de l’actualité, en français et en anglais.', html)
        self.assertIn('background:#0F2A60;color:#FFFFFF;border-left:5px solid #F0B100', html)
        self.assertNotIn('href="None"', html)
        self.assertNotIn('/Users/', html)
        self.assertLess(len(html.encode()), 102000)
        for a in data['articles']:
            for lang in ('fr', 'en'):
                for field in ('summary', 'relevance', 'caveat'):
                    self.assertIn(a[lang][field], text)
            self.assertIn(a['url'], text)
        self.assertEqual(msg['To'], 'ndriaffre@gmail.com')
        self.assertIsNone(msg['Cc'])
        self.assertIsNone(msg['Bcc'])

class PackageTests(unittest.TestCase):
    def test_release_whitelist_and_secret_markers(self):
        self.assertTrue((ROOT/'package_release.py').exists(), 'whitelist packager missing')
        import package_release as p
        self.assertNotIn('config.local.json', p.WHITELIST)
        self.assertNotIn('runtime/delivery.sqlite3', p.WHITELIST)
        for bad in (b'/Users/'+b'romaric', b'MAIL_'+b'PASSWORD', b'-----BEGIN '+b'PRIVATE KEY-----'):
            with self.assertRaises(ValueError): p.scan('fixture', bad)
        p.scan('fixture', b'public editorial data')

class SenderTests(unittest.TestCase):
    def test_send_gates_and_freshness(self):
        self.assertTrue((ROOT / 'sender.py').exists(), 'secure sender not implemented')
        import sender as s
        import welispeak as w
        from datetime import datetime, timezone, timedelta
        data = json.loads((ROOT / 'examples/archive_20261022.json').read_text())
        config = w.load_config(ROOT / 'config.example.json')
        now = datetime(2026, 10, 22, 14, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            s.preflight(data, config, now)
        data.pop('archive_example'); data['approved_for_send'] = True
        config.update(send_authorized=True, smtp_host='smtp.example.org', sender_email='sender@example.org')
        s.preflight(data, config, now)
        for cutoff in (now-timedelta(hours=2, seconds=1), now+timedelta(seconds=1)):
            copy = dict(data, cutoff=cutoff.isoformat())
            with self.assertRaises(ValueError):
                s.preflight(copy, config, now)
        for patch in ({'send_authorized':False}, {'smtp_port':465}, {'recipient':'other@example.org'}, {'sender_email':'newsletter@welispeak.com'}):
            with self.assertRaises(ValueError):
                s.preflight(data, dict(config, **patch), now)
        with self.assertRaises(ValueError):
            s.preflight(dict(data, approved_for_send=False), config, now)

    def test_ledger_private_durable_duplicate_guard(self):
        import sender as s
        import os
        import sqlite3
        data = json.loads((ROOT/'examples/archive_20261022.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'ledger.sqlite3'
            db, key = s.reserve(path, data)
            db.close()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with sqlite3.connect(path) as check:
                self.assertEqual(check.execute('SELECT status FROM deliveries').fetchone()[0], 'attempting')
            with self.assertRaises(ValueError):
                s.reserve(path, data)
            changed = json.loads(json.dumps(data)); changed['articles'][0]['fr']['title'] += ' corrected'
            with self.assertRaises(ValueError):
                s.reserve(path, changed)

    def test_transport_tls_and_ambiguous_no_retry(self):
        import sender as s
        import sqlite3
        import ssl
        from datetime import datetime, timezone
        data = json.loads((ROOT/'examples/archive_20261022.json').read_text())
        # Test data only: move timestamps together to exercise freshness without changing archive on disk.
        old = datetime.fromisoformat(data['cutoff'])
        now = datetime.now(timezone.utc)
        delta = now-old
        data['cutoff'] = now.isoformat(); data.pop('archive_example'); data['approved_for_send'] = True
        for article in data['articles']:
            article['published_at'] = (datetime.fromisoformat(article['published_at'])+delta).isoformat()
        import welispeak as w
        config = w.load_config(ROOT/'config.example.json')
        config.update(send_authorized=True, smtp_host='smtp.example.org', sender_email='sender@example.org')
        events = []
        testcase = self
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'ledger.sqlite3'
            class Transport:
                def __init__(self, host, port, timeout):
                    testcase.assertEqual(port, 587)
                    with sqlite3.connect(path) as check:
                        testcase.assertEqual(check.execute('SELECT status FROM deliveries').fetchone()[0], 'attempting')
                    events.append('connect')
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def ehlo(self): events.append('ehlo')
                def starttls(self, context):
                    testcase.assertTrue(context.check_hostname)
                    testcase.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
                    events.append('tls')
                def login(self, user, password):
                    testcase.assertIn('tls', events)
                    events.append('login')
                def send_message(self, msg, from_addr, to_addrs):
                    testcase.assertEqual(to_addrs, ['ndriaffre@gmail.com'])
                    testcase.assertIsNone(msg['X-Unsent'])
                    raise OSError('simulated response must never leak')
            with self.assertRaisesRegex(RuntimeError, 'masked') as caught:
                s.deliver(data, config, path, 'NONSECRET_TEST_FIXTURE', smtp_factory=Transport)
            self.assertNotIn('simulated response', str(caught.exception))
            with sqlite3.connect(path) as check:
                self.assertEqual(check.execute('SELECT status FROM deliveries').fetchone()[0], 'ambiguous')
            with self.assertRaises(ValueError):
                s.deliver(data, config, path, 'NONSECRET_TEST_FIXTURE', smtp_factory=Transport)
            self.assertEqual(events.count('connect'), 1)

if __name__ == '__main__':
    unittest.main()

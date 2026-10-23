"""Stdlib-only acceptance tests; run python3 -m unittest -v."""
import importlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
SPEC = ROOT.parent / 'docs' / 'destinations_reference.md'

class RegistryTests(unittest.TestCase):
    def test_exact_section18_registry_and_separate_ci(self):
        self.assertTrue((ROOT / 'registry.py').exists(), 'Registry parser missing')
        registry = importlib.import_module('registry')
        expected = registry.parse_spec(SPEC.read_text())
        stored = json.loads((ROOT / 'destinations.json').read_text())
        self.assertEqual(expected, stored)
        self.assertEqual(len(stored['destinations']), 30)
        self.assertEqual(len({d['code'] for d in stored['destinations']}), 30)
        self.assertEqual(stored['base']['code'], 'CI')
        self.assertNotIn('CI', [d['code'] for d in stored['destinations']])
        self.assertEqual([d['number'] for d in stored['destinations']], list(range(1, 31)))
        with self.assertRaises(ValueError):
            registry.parse_spec('## 18. invalid\n| 1 | Test | Test | US | International |')

class ServerTests(unittest.TestCase):
    def test_server_entitlement_journey(self):
        self.assertTrue((ROOT / 'server.py').exists(), 'Local session server missing')
        import server
        import tempfile
        import threading
        import urllib.request
        import urllib.error
        import http.cookiejar
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            httpd = server.create_server(0, pathlib.Path(tmp) / 'sessions.sqlite', demo_enabled=True)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = 'http://127.0.0.1:' + str(httpd.server_port)
            jar = http.cookiejar.CookieJar()
            client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            def call(path, data=None, token=None):
                headers = {'Content-Type': 'application/json'}
                if token:
                    headers['X-CSRF-Token'] = token
                req = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
                try:
                    with client.open(req) as response:
                        return response.status, json.loads(response.read())
                except urllib.error.HTTPError as error:
                    return error.code, json.loads(error.read())
            try:
                status, session = call('/api/session')
                self.assertEqual(status, 200)
                self.assertFalse(session['paid'])
                csrf = session['csrf']
                self.assertEqual(call('/api/catalogue')[0], 403)
                self.assertEqual(len(call('/api/overview')[1]['destinations']), 30)
                self.assertEqual(call('/api/register', {'discover_world': True}, csrf)[0], 200)
                self.assertFalse(call('/api/session')[1]['paid'])
                self.assertEqual(call('/api/preferences', {'destinations': ['US'], 'language': 'en'}, csrf)[0], 403)
                self.assertEqual(call('/api/demo/activate', {'confirm': True})[0], 403)
                self.assertEqual(call('/api/webhook', {'paid': True}, csrf)[0], 501)
                self.assertFalse(call('/api/session')[1]['paid'])
                self.assertEqual(call('/api/demo/activate', {'confirm': True}, csrf)[0], 200)
                self.assertEqual(call('/api/preferences', {'destinations': ['US', 'US'], 'language': 'en'}, csrf)[0], 400)
                self.assertEqual(call('/api/preferences', {'destinations': ['XX'], 'language': 'en'}, csrf)[0], 400)
                self.assertEqual(call('/api/preferences', {'destinations': ['US'], 'language': 'en'}, csrf)[0], 200)
                self.assertEqual(call('/api/session')[1]['destinations'], ['US'])
                catalogue = call('/api/catalogue')[1]['editions']
                self.assertEqual(len(catalogue), 31)
                self.assertEqual(len({e['code'] for e in catalogue}), 31)
                self.assertTrue(all(e['demonstration'] for e in catalogue))
                self.assertEqual(call('/api/register', {'email': 'not-saved@example.test'}, csrf)[0], 400)
                self.assertNotIn(b'not-saved@example.test', (pathlib.Path(tmp) / 'sessions.sqlite').read_bytes())
                with urllib.request.urlopen(base + '/api/session') as fresh:
                    self.assertFalse(json.load(fresh)['paid'])
                cookies = list(jar)
                self.assertTrue(cookies[0].has_nonstandard_attr('HttpOnly'))
                self.assertEqual(cookies[0].get_nonstandard_attr('SameSite'), 'Strict')
                httpd.demo_enabled = False
                self.assertEqual(call('/api/demo/activate', {'confirm': True}, csrf)[0], 403)
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join()

class InterfaceTests(unittest.TestCase):
    def test_seven_screen_bilingual_local_artifact(self):
        self.assertTrue((ROOT / 'index.html').exists(), 'Seven-screen interface missing')
        from html.parser import HTMLParser
        class Screens(HTMLParser):
            def __init__(self):
                super().__init__()
                self.screens = []
                self.remote = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'section' and 'data-screen' in attrs:
                    self.screens.append(attrs['data-screen'])
                if tag in ('script', 'img', 'link'):
                    for attr in ('src', 'href'):
                        if attrs.get(attr, '').startswith(('http:', 'https:')):
                            self.remote.append(attrs[attr])
        parser = Screens()
        parser.feed((ROOT / 'index.html').read_text())
        self.assertEqual(parser.screens, ['welcome', 'signup', 'offers', 'preview', 'activation', 'preferences', 'catalogue'])
        self.assertEqual(parser.remote, [])
        self.assertIn('data-language="fr"', (ROOT / 'index.html').read_text())
        self.assertIn('data-language="en"', (ROOT / 'index.html').read_text())
        self.assertTrue((ROOT / 'assets/logo.png').is_file())
        self.assertIn('min-height:44px', (ROOT / 'style.css').read_text())
        self.assertIn('/api/catalogue', (ROOT / 'app.js').read_text())

class MailTests(unittest.TestCase):
    def test_short_bilingual_multipart_mail_without_invented_read_url(self):
        self.assertTrue((ROOT / 'mailMonde.eml').exists(), 'Unsent MIME template missing')
        from email import policy
        from email.parser import BytesParser
        message = BytesParser(policy=policy.default).parsebytes((ROOT / 'mailMonde.eml').read_bytes())
        self.assertIsNone(message['To'])
        self.assertIsNone(message['Cc'])
        self.assertIsNone(message['Bcc'])
        plain = message.get_body(preferencelist=('plain',)).get_content()
        html = message.get_body(preferencelist=('html',)).get_content()
        for value in (plain, html):
            self.assertIn('DÉMONSTRATION', value)
            self.assertIn('DEMONSTRATION', value)
            self.assertIn('URL', value)
            self.assertNotIn('http://', value)
            self.assertNotIn('https://', value)
            self.assertNotIn('localhost', value)
        self.assertNotIn('href=', html)
        self.assertLess(len(plain), 2500)

if __name__ == '__main__':
    unittest.main()

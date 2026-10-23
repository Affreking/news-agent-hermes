import base64
import importlib
import json
import tempfile
import unittest
from pathlib import Path

PORTABLE = Path(__file__).resolve().parents[2] / 'portable_welispeak'


class RendererTests(unittest.TestCase):
    def test_empty_launch_preview_is_explicit_unpublished_and_keeps_original_logo_palette(self):
        renderer = importlib.import_module('renderer')
        with tempfile.TemporaryDirectory() as temp:
            output = renderer.launch_preview(Path(temp), portable_root=PORTABLE)
            for lang in ('fr', 'en'):
                html = (Path(temp)/f'launch_{lang}.html').read_text()
                self.assertIn('Nº001', html)
                self.assertIn('1er novembre 2026' if lang == 'fr' else '1 November 2026', html)
                self.assertIn('APERÇU DU LANCEMENT' if lang == 'fr' else 'LAUNCH PREVIEW', html)
                self.assertNotIn('<article', html)
                self.assertIn(base64.b64encode((PORTABLE/'assets/logo.png').read_bytes()).decode(), html)
                for color in ('#0F2A60', '#F0B100'):
                    self.assertIn(color, html)
            manifest = json.loads((Path(temp)/'manifest.json').read_text())
            self.assertEqual(manifest['number'], 1)
            self.assertEqual(manifest['status'], 'preview')
            self.assertFalse(manifest['published'])
            self.assertFalse(manifest['approved_for_send'])
            self.assertEqual(manifest['article_count'], 0)
            self.assertEqual(manifest['timezone'], 'Africa/Abidjan')
            self.assertFalse(list(Path(temp).glob('*.sqlite*')))
            self.assertEqual(output['sent'], False)

    def test_archive_wrapper_numbers_subject_banners_manifest_without_publishing(self):
        renderer = importlib.import_module('renderer')
        data = json.loads((PORTABLE/'examples/archive_20261022.json').read_text())
        config = json.loads((PORTABLE/'config.example.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            from registry import Registry
            from datetime import datetime, timezone
            r = Registry(Path(temp)/'test.sqlite3', environment='test', now=lambda: datetime(2026, 11, 2, tzinfo=timezone.utc))
            a = r.reserve('2026-11-01', approved_for_send=True)
            r.confirm(a['token'], evidence='test receipt')
            m = r.metadata('2026-11-01', mode='correction', correction_reason='test correction')
            with self.assertRaises(ValueError):
                renderer.build_numbered(data, config, m, portable_root=PORTABLE)
            # Historical input is allowed only as an explicitly labelled context preview.
            out = renderer.build_numbered(data, config, m, portable_root=PORTABLE, context_preview=True)
            from email import policy
            from email.parser import BytesParser
            msg = BytesParser(policy=policy.default).parsebytes(out['mime'])
            self.assertIn('Nº001', str(msg['Subject']))
            self.assertIn('ÉDITION CORRIGÉE', out['text'])
            self.assertIn('CORRECTED EDITION', out['text'])
            self.assertIn('2026-10-22', out['preview'])
            self.assertIn('CONTEXTE HISTORIQUE', out['preview'])
            self.assertIn('2026-11-01', out['preview'])
            self.assertFalse(out['manifest']['approved_for_send'])
            self.assertFalse(out['manifest']['published'])
            self.assertEqual(out['manifest']['number'], 1)
            self.assertEqual(r.last_number(), 1)
            for lang in ('fr', 'en'):
                self.assertIn('Nº001', out['languages'][lang]['web'])
                self.assertIn('ÉDITION CORRIGÉE' if lang == 'fr' else 'CORRECTED EDITION', out['languages'][lang]['web'])

    def test_archive_writer_persists_numbered_manifest_without_overwriting(self):
        renderer = importlib.import_module('renderer')
        with tempfile.TemporaryDirectory() as temp:
            artifact = {'preview': '<html>preview Nº001</html>', 'text': 'Nº001', 'mime': b'X-Unsent: 1\r\n',
                        'languages': {lang: {'web': '<html>Nº001</html>'} for lang in ('fr', 'en')},
                        'manifest': {'number': 1, 'label': 'Nº001', 'published': False, 'sent': False}}
            root = Path(temp)/'archive'
            renderer.write_archive(artifact, root)
            manifest = json.loads((root/'manifest.json').read_text())
            self.assertEqual(manifest['number'], 1)
            self.assertEqual(len(manifest['files']), 5)
            self.assertTrue((root/'newsletter_unsent.eml').exists())
            with self.assertRaises(FileExistsError):
                renderer.write_archive(artifact, root)


if __name__ == '__main__':
    unittest.main()

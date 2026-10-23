"""Offline acceptance tests for the reader-facing redesign."""
import importlib.util
import json
from pathlib import Path
import unittest
from email.parser import BytesParser
from email.policy import default
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent

class Images(HTMLParser):
    def __init__(self):
        super().__init__(); self.images = []; self.scripts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'img': self.images.append(dict(attrs))
        if tag == 'script': self.scripts.append(attrs)

class NewsletterTests(unittest.TestCase):
    def test_complete_bilingual_preview_and_cid_mime(self):
        self.assertIsNotNone(importlib.util.find_spec('newsletter_design'), 'redesign module is required')
        from newsletter_design import build
        data = json.loads((ROOT/'data/artifacts/edition_20261022_editorial.json').read_text())
        result = build(data)
        for lang in ('fr', 'en'):
            out = result[lang]
            preview = out['html']
            p = Images(); p.feed(preview)
            self.assertEqual(len(p.images), 6)
            self.assertTrue(all(i.get('alt') for i in p.images))
            self.assertTrue(all(i['src'].startswith('data:image/png;base64,') for i in p.images))
            self.assertFalse(p.scripts)
            self.assertIn('#102A43', preview)
            self.assertIn('#F58220', preview)
            self.assertIn('#16865B', preview)
            self.assertIn('@media', preview)
            self.assertIn('Arial', preview)
            self.assertIn('CC0', preview)
            self.assertIn('13', preview)
            self.assertIn('12', preview)
            for article in data['articles']:
                self.assertIn(article[lang]['summary'], out['text'])
                self.assertIn(article[lang]['verification'], out['text'])
                self.assertIn(article['url'], out['text'])
                self.assertIn(article['url'].replace('&','&amp;'), preview)
            self.assertIn(data['articles'][1]['primary_url'], out['text'])
            self.assertNotIn('/Users/', preview)
            self.assertNotIn('artifacts/', preview)
            msg = BytesParser(policy=default).parsebytes(out['mime'])
            self.assertIsNone(msg.get('To'))
            self.assertEqual(msg['X-Unsent'], '1')
            self.assertEqual(msg.get_body(preferencelist=('plain',)).get_content().replace('\r\n', '\n').strip(), out['text'].strip())
            email_html = msg.get_body(preferencelist=('html',)).get_content()
            ep = Images(); ep.feed(email_html)
            self.assertTrue(all(i['src'].startswith('cid:') for i in ep.images))
            self.assertNotIn('data:image', email_html)
            self.assertNotIn('file:', email_html)
            image_parts = [part for part in msg.walk() if part.get_content_maintype() == 'image']
            self.assertEqual(len(image_parts), 6)
            cids = {part['Content-ID'].strip('<>') for part in image_parts}
            self.assertEqual({im['src'][4:] for im in ep.images}, cids)
            self.assertTrue(all(part.get_payload(decode=True).startswith(b'\x89PNG') for part in image_parts))
        self.assertIn('Brouillon — à valider', result['fr']['text'])
        self.assertIn('exclus', result['fr']['text'])
        self.assertIn('excluded', result['en']['text'])

if __name__ == '__main__': unittest.main()

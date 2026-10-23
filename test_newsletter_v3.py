import importlib.util
import json
from pathlib import Path
import unittest
from html.parser import HTMLParser
from email.parser import BytesParser
from email.policy import default
from datetime import datetime, timedelta

ROOT=Path(__file__).resolve().parent
class Inspect(HTMLParser):
    def __init__(self): super().__init__(); self.images=[]; self.scripts=[]
    def handle_starttag(self,t,a):
        if t=='img': self.images.append(dict(a))
        if t=='script': self.scripts.append(a)
class V3Tests(unittest.TestCase):
    def test_compact_readable_and_complete(self):
        self.assertIsNotNone(importlib.util.find_spec('newsletter_v3'), 'V3 renderer required')
        from newsletter_v3 import build
        data=json.loads((ROOT/'data/artifacts/edition_20261022_v3.json').read_text())
        end=datetime.fromisoformat(data['cutoff'])
        for a in data['articles']:
            stamp=datetime.fromisoformat(a['published_at'])
            self.assertTrue(end-timedelta(hours=24)<=stamp<=end)
            self.assertTrue(stamp.utcoffset() is not None)
            for lang in ('fr','en'): self.assertTrue(60<=len(a[lang]['summary'].split())<=90, (a['story_id'],lang,len(a[lang]['summary'].split())))
        out=build(data)
        for lang in ('fr','en'):
            p=Inspect(); p.feed(out[lang]['html'])
            self.assertEqual(len(p.images),len(data['articles']))
            self.assertTrue(all(int(i['width'])<=112 and i.get('alt') for i in p.images))
            self.assertFalse(p.scripts)
            self.assertIn('@media',out[lang]['html'])
            self.assertNotIn('13:32:44',out[lang]['html'].split('id="method"')[0])
            msg=BytesParser(policy=default).parsebytes(out[lang]['mime'])
            self.assertIsNone(msg.get('To'))
            self.assertEqual(msg['X-Unsent'],'1')
            body=msg.get_body(preferencelist=('plain',)).get_content().replace('\r\n','\n')
            for a in data['articles']:
                self.assertIn(a[lang]['summary'],body)
                self.assertIn(a[lang]['caveat'],body)
                self.assertIn(a['url'],body)
            eh=msg.get_body(preferencelist=('html',)).get_content()
            self.assertNotIn('data:image',eh)
            self.assertNotIn('/Users/',eh)
            self.assertLess(len(eh.encode()),100000)
            self.assertEqual(sum(part.get_content_maintype()=='image' for part in msg.walk()),len(data['articles']))
if __name__=='__main__': unittest.main()

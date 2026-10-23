import unittest,json,importlib.util
from pathlib import Path
from html.parser import HTMLParser
from email.parser import BytesParser
from email.policy import default
class Images(HTMLParser):
    def __init__(self):super().__init__();self.items=[]
    def handle_starttag(self,t,a):
        if t=='img':self.items.append(dict(a))
class V4Tests(unittest.TestCase):
    def test_large_lead_and_complete_cid_draft(self):
        self.assertIsNotNone(importlib.util.find_spec('newsletter_v4'))
        from newsletter_v4 import build
        data=json.loads((Path(__file__).parent/'data/artifacts/edition_20261022_v3.json').read_text())
        for lang,out in build(data).items():
            p=Images();p.feed(out['html'])
            self.assertEqual(len(p.items),6)
            self.assertEqual(p.items[0]['width'],'584')
            self.assertTrue(all(i['width']=='96' for i in p.items[1:]))
            self.assertTrue(all(i['alt'] for i in p.items))
            self.assertNotIn('<script',out['html'])
            msg=BytesParser(policy=default).parsebytes(out['mime'])
            self.assertIsNone(msg.get('To'))
            self.assertEqual(msg['X-Unsent'],'1')
            body=msg.get_body(preferencelist=('plain',)).get_content()
            for a in data['articles']:
                self.assertIn(a[lang]['summary'],body)
                self.assertIn(a[lang]['caveat'],body)
                self.assertIn(a['url'],body)
            eh=msg.get_body(preferencelist=('html',)).get_content()
            self.assertNotIn('data:image',eh)
            self.assertNotIn('/Users/',eh)
            self.assertEqual(sum(x.get_content_maintype()=='image' for x in msg.walk()),6)
            self.assertLess(len(eh.encode()),100000)
if __name__=='__main__':unittest.main()

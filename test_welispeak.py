import unittest,json,importlib.util
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
from html.parser import HTMLParser
class Tags(HTMLParser):
 def __init__(self):super().__init__();self.img=[];self.links=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='img':self.img.append(d)
  if t=='a':self.links.append(d.get('href',''))
class BrandTests(unittest.TestCase):
 def test_brand_and_safe_email(self):
  self.assertIsNotNone(importlib.util.find_spec('welispeak_v4'))
  from welispeak_v4 import build
  root=Path(__file__).parent
  data=json.loads((root/'data/artifacts/edition_20261022_v3.json').read_text())
  for lang,out in build(data).items():
   text=out['html'];p=Tags();p.feed(text)
   self.assertEqual(len(p.img),7)
   self.assertEqual(p.img[0]['alt'],'WELISPEAK — logo original')
   self.assertTrue(all(i.get('alt') for i in p.img))
   self.assertIn('#0F2A60',text);self.assertIn('#F0B100',text)
   self.assertNotIn('#F58220',text);self.assertNotIn('#16865B',text)
   self.assertNotIn('<script',text)
   self.assertIn('Français',text);self.assertIn('English',text)
   self.assertTrue(any('camera' in i['alt'].lower() or 'caméra' in i['alt'].lower() for i in p.img))
   msg=BytesParser(policy=default).parsebytes(out['mime'])
   self.assertIsNone(msg.get('To'));self.assertEqual(msg['X-Unsent'],'1')
   eh=msg.get_body(preferencelist=('html',)).get_content()
   self.assertNotIn('file:',eh);self.assertNotIn('data:image',eh)
   self.assertNotIn('href="newsletter_',eh)
   self.assertEqual(sum(x.get_content_maintype()=='image' for x in msg.walk()),7)
   self.assertLess(len(eh.encode()),100000)
   plain=msg.get_body(preferencelist=('plain',)).get_content()
   for a in data['articles']:
    self.assertIn(a[lang]['summary'],plain);self.assertIn(a[lang]['caveat'],plain)
   self.assertIn('WhatsApp',plain);self.assertIn('LinkedIn',plain)
if __name__=='__main__':unittest.main()

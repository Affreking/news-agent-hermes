import unittest,importlib.util,json
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
class V5Tests(unittest.TestCase):
 def test_structure_content_images_and_mime(self):
  self.assertIsNotNone(importlib.util.find_spec('welispeak_v5'))
  from welispeak_v5 import build
  root=Path(__file__).parent
  data=json.loads((root/'data/artifacts/edition_20261022_v3.json').read_text())
  for lang,out in build(data).items():
   self.assertIn('max-width:720px',out['web'])
   self.assertNotIn('overflow-x:hidden',out['web'])
   self.assertEqual(out['web'].count('<article'),6)
   self.assertEqual(out['web'].count('</article>'),6)
   self.assertIn('max-width:640px',out['email'])
   self.assertNotIn('<script',out['web'])
   self.assertNotIn('display:grid',out['email'])
   self.assertNotIn('data:image',out['email'])
   self.assertNotIn('file:',out['email'])
   msg=BytesParser(policy=default).parsebytes(out['mime'])
   self.assertEqual(msg['X-Unsent'],'1');self.assertIsNone(msg.get('To'))
   plain=msg.get_body(preferencelist=('plain',)).get_content()
   for a in data['articles']:
    self.assertIn(a[lang]['summary'],plain);self.assertIn(a[lang]['caveat'],plain)
   parts=[p for p in msg.walk() if p.get_content_maintype()=='image']
   self.assertEqual(len(parts),7)
   for part in parts[1:]:self.assertLess(len(part.get_payload(decode=True)),120*1024)
   self.assertLess(len(out['email'].encode()),100000)
if __name__=='__main__':unittest.main()

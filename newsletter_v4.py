"""V4 presentation refinement, preserving V2/V3 and all editorial content."""
import json
from pathlib import Path
from html import escape
from email.parser import BytesParser
from email.policy import SMTP
import newsletter_v3

ROOT=Path(__file__).resolve().parent

def enhance(markup,lang):
    # Only the lead icon is enlarged; no article photo is claimed or reused.
    marker='<td width="112" valign="top" style="width:112px;padding:0 16px 10px 0;">'
    pos=markup.index(marker)
    close=markup.index('</tr></table>',pos)+len('</tr></table>')
    header=markup[pos:close]
    imgstart=header.index('<img ');imgend=header.index('>',imgstart)+1
    image=header[imgstart:imgend]
    image=image.replace('width="96" height="36"','width="584" height="219"').replace('width:96px;height:36px;','width:100%;max-width:584px;height:auto;')
    category=header[header.index('</td><td ')+5:]
    caption='Illustration générique originale — pas une photographie de l’événement.' if lang=='fr' else 'Original generic illustration — not a photograph of the event.'
    replacement=f'<td valign="top">{image}<p style="margin:8px 0 16px;font-size:12px;color:#526574;line-height:1.6;">{escape(caption)}</p></td></tr><tr>'+category
    markup=markup[:pos]+replacement+markup[close:]
    markup=markup.replace(' — V3 — ',' — V4 — ')
    return markup

def build(data):
    base=newsletter_v3.build(data)
    for lang,out in base.items():
        out['html']=enhance(out['html'],lang)
        msg=BytesParser(policy=SMTP).parsebytes(out['mime'])
        part=msg.get_body(preferencelist=('html',))
        original=part.get_content()
        part.set_content(enhance(original,lang),subtype='html',charset='utf-8',cte='quoted-printable')
        out['mime']=msg.as_bytes()
    return base

def main():
    data=json.loads((ROOT/'data/artifacts/edition_20261022_v3.json').read_text())
    for lang,out in build(data).items():
        (ROOT/f'data/frontend/newsletter_20261022_{lang}_v4.html').write_text(out['html'])
        (ROOT/f'data/briefs/newsletter_20261022_{lang}_v4.txt').write_text(out['text'])
        (ROOT/f'data/artifacts/newsletter_20261022_{lang}_v4_unsent.eml').write_bytes(out['mime'])
    print(json.dumps({'stories':len(data['articles']),'media':len({a['source'] for a in data['articles']}),'sent':False,'smtp_accessed':False}))
if __name__=='__main__':main()

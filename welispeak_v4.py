"""WELISPEAK branded V4, offline previews and CID MIME; no SMTP."""
import base64,copy,json,re,struct,zlib
from pathlib import Path
from email.message import EmailMessage
from email.policy import SMTP
import newsletter_v3
from newsletter_design import illustration
ROOT=Path(__file__).resolve().parent
BLUE='#0F2A60';GOLD='#F0B100'

def png_pack(raw,w=640,h=240):
 def chunk(n,d):return struct.pack('!I',len(d))+n+d+struct.pack('!I',zlib.crc32(n+d)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def brand_icon(kind,camera=False):
 if camera:
  pixels=bytearray((247,247,247)*(640*240))
  def rect(x1,y1,x2,y2,c):
   for y in range(y1,y2):
    for x in range(x1,x2):pixels[(y*640+x)*3:(y*640+x)*3+3]=bytes(c)
  blue=(15,42,96);gold=(240,177,0)
  rect(202,65,378,163,blue);rect(215,78,365,150,(247,247,247));rect(222,85,358,144,gold)
  for x in range(380,433):
   inset=int((433-x)*.42)
   rect(x,62+inset,x+1,164-inset,blue)
  rect(282,163,294,194,blue);rect(250,192,325,200,blue)
  raw=b''.join(b'\0'+pixels[y*1920:(y+1)*1920] for y in range(240))
  return png_pack(raw)
 png=illustration(kind);pos=8;compressed=b''
 while pos<len(png):
  size=int.from_bytes(png[pos:pos+4],'big');name=png[pos+4:pos+8]
  if name==b'IDAT':compressed+=png[pos+8:pos+8+size]
  pos+=size+12
 raw=bytearray(zlib.decompress(compressed))
 mapping={(16,42,67):(15,42,96),(22,134,91):(15,42,96),(245,130,32):(240,177,0),(232,240,244):(247,247,247)}
 for y in range(240):
  for x in range(640):
   i=y*1921+1+x*3;t=tuple(raw[i:i+3])
   if t in mapping:raw[i:i+3]=bytes(mapping[t])
 return png_pack(raw)

def build(data):
 base=newsletter_v3.build(data);logo=(ROOT/'data/frontend/welispeak_original_logo.png').read_bytes()
 result={}
 for lang,out in base.items():
  fr=lang=='fr';title='WELISPEAK — L’essentiel' if fr else 'WELISPEAK — The Brief'
  signature='L’actualité en français et en anglais.' if fr else 'News in French and English.'
  markup=out['html']
  for old,new in {'#102A43':BLUE,'#16865B':BLUE,'#F58220':GOLD,'#243B53':'#0F182B','#334E68':'#0F182B','#F3F6F8':'#F7F7F7','#E8EEF2':'#F7F7F7','#FFF2E5':'#FFF8E1'}.items():markup=markup.replace(old,new)
  markup=re.sub(r'<title>.*?</title>',f'<title>{title} — 22 octobre 2026</title>',markup)
  # Replace only the masthead cell; no editorial copy changes.
  start=markup.index('<tr><td class="pad" bgcolor="'+BLUE+'"')
  end=markup.index('</td></tr>',start)+len('</td></tr>')
  def language_controls(email=False):
   cells=[]
   for code,label in [('fr','Français'),('en','English')]:
    active=code==lang; bg=GOLD if active else '#FFFFFF'
    style=f'display:inline-block;padding:12px 18px;color:{BLUE};background:{bg};font-weight:bold;font-size:14px;text-decoration:none;border:1px solid {GOLD};'
    if email:node=f'<span style="{style}"'+(' aria-current="true"' if active else '')+f'>{label}</span>'
    else:node=f'<a href="welispeak_20261022_{code}_v4.html" style="{style}"'+(' aria-current="page"' if active else '')+f'>{label}</a>'
    cells.append('<td>'+node+'</td>')
   return '<table role="presentation" cellspacing="0" cellpadding="0"><tr>'+''.join(cells)+'</tr></table>'
  header=f'''<tr><td class="pad" bgcolor="#FFFFFF" style="padding:25px 28px;color:{BLUE};"><img src="@@LOGO@@" width="240" height="60" alt="WELISPEAK — logo original" style="display:block;width:240px;max-width:100%;height:auto;border:0;margin:0 0 18px;">@@LANGUAGES@@<h1 style="margin:24px 0 9px;color:{BLUE};font-size:30px;line-height:1.2;">{title}</h1><p style="margin:0 0 18px;font-size:16px;color:#0F182B;line-height:1.6;">{signature}</p><p style="margin:0 0 14px;font-size:13px;color:#526574;">{'22 octobre 2026 · FRANÇAIS' if fr else '22 October 2026 · ENGLISH'}</p><span style="display:inline-block;background:{GOLD};color:{BLUE};padding:6px 10px;font-weight:bold;font-size:12px;">{'Brouillon — à valider' if fr else 'Draft — pending review'}</span></td></tr>'''
  markup=markup[:start]+header+markup[end:]
  # Update source buttons, retaining secondary source anchors.
  markup=markup.replace(f'bgcolor="{BLUE}" style="border-radius:4px;"',f'bgcolor="{GOLD}" style="border-radius:4px;"')
  markup=markup.replace('padding:13px 20px;color:#FFFFFF;','padding:13px 20px;color:'+BLUE+';')
  imgs=list(re.finditer(r'<img\b[^>]*>',markup))
  assets=[logo]
  # Reverse replacement prevents offset shifts. First image is logo.
  for i in range(len(data['articles'])-1,-1,-1):
   a=data['articles'][i];camera=a['story_id']=='mancala-studios';png=brand_icon(a.get('icon',i%6),camera);assets.insert(1,png)
   tag=imgs[i+1].group();tag=re.sub(r'src="[^"]+"',f'src="@@IMAGE{i}@@"',tag)
   alt=('Caméra de studio — illustration générique' if fr else 'Studio camera — generic illustration') if camera else ('Illustration générique : ' if fr else 'Generic illustration: ')+a[lang]['category']
   tag=re.sub(r'alt="[^"]*"',f'alt="{alt}"',tag)
   markup=markup[:imgs[i+1].start()]+tag+markup[imgs[i+1].end():]
  # Assets inserted in reverse order above now match article order.
  social=("Chaîne WhatsApp — lien à configurer. Newsletter LinkedIn — lien à configurer." if fr else "WhatsApp channel — link not configured. LinkedIn newsletter — link not configured.")
  note=('Logo officiel : fichier original du site WELISPEAK, conversion PNG pour compatibilité e-mail, proportions intactes. Marque non couverte par la licence CC0 des pictogrammes. Les sélecteurs de langue du fichier local ouvrent les deux aperçus ; aucun lien public de version linguistique n’est configuré pour l’e-mail.' if fr else 'Official logo: original WELISPEAK website asset, converted to PNG for email compatibility with unchanged proportions. The brand is not covered by the pictograms’ CC0 licence. Local language controls open the two previews; no public language-version links are configured for email.')
  socialblock=f'<tr><td class="pad" bgcolor="#FFFFFF" style="padding:22px 28px;"><p style="margin:0 0 10px;color:{BLUE};font-size:16px;font-weight:bold;">'+('Suivre la revue' if fr else 'Follow the brief')+f'</p><p style="margin:0;font-size:14px;line-height:1.8;color:#0F182B;">{social}</p></td></tr>'
  footerpos=markup.index('<tr><td id="method"')
  markup=markup[:footerpos]+socialblock+markup[footerpos:]
  markup=markup.replace('</body>',f'<p style="max-width:600px;margin:0 auto 25px;padding:0 20px;font:12px/1.6 Arial;color:#526574;">{note}</p></body>')
  # Match the site's declared slate body tokens, not the initial approximations.
  markup=markup.replace('#0F182B','#0F172B').replace('#F7F7F7','#F1F5F9')
  # Correct inherited large-photo policy copy: this brand uses small pictograms.
  markup=markup.replace('Les grandes images sont réservées aux photographies pertinentes dont les droits de réutilisation sont établis.','').replace('Large images are reserved for relevant photographs with established reuse rights.','')
  preview=markup.replace('@@LANGUAGES@@',language_controls())
  email=markup.replace('@@LANGUAGES@@',language_controls(email=True))
  preview=preview.replace('@@LOGO@@','data:image/png;base64,'+base64.b64encode(logo).decode());email=email.replace('@@LOGO@@','cid:welispeak-logo@draft.local')
  for i,png in enumerate(assets[1:]):
   preview=preview.replace(f'@@IMAGE{i}@@','data:image/png;base64,'+base64.b64encode(png).decode())
   email=email.replace(f'@@IMAGE{i}@@',f'cid:welispeak-{i}@draft.local')
  plain=title+'\n'+signature+'\nFrançais | English\n\n'+out['text'].split('\n\n',1)[1]+'\n\n'+social+'\n\n'+note+'\n'
  msg=EmailMessage(policy=SMTP);msg['Subject']=title+' — '+('22 octobre 2026' if fr else '22 October 2026');msg['X-Unsent']='1';msg.set_content(plain);msg.add_alternative(email,subtype='html');related=msg.get_payload()[-1]
  for i,png in enumerate(assets):related.add_related(png,maintype='image',subtype='png',cid='<welispeak-logo@draft.local>' if i==0 else f'<welispeak-{i-1}@draft.local>',filename='welispeak-original.png' if i==0 else f'illustration-{i}.png',disposition='inline')
  result[lang]={'html':preview,'text':plain,'mime':msg.as_bytes()}
 return result

def main():
 data=json.loads((ROOT/'data/artifacts/edition_20261022_v3.json').read_text())
 for lang,out in build(data).items():
  (ROOT/f'data/frontend/welispeak_20261022_{lang}_v4.html').write_text(out['html'])
  (ROOT/f'data/briefs/welispeak_20261022_{lang}_v4.txt').write_text(out['text'])
  (ROOT/f'data/artifacts/welispeak_20261022_{lang}_v4_unsent.eml').write_bytes(out['mime'])
 print(json.dumps({'languages':['fr','en'],'stories':len(data['articles']),'sent':False,'logo_source':'https://www.welispeak.com/svg/wls-logo-long.svg','palette':{'blue':BLUE,'gold':GOLD,'text':'#0F172B','background':'#F1F5F9'}}))
if __name__=='__main__':main()

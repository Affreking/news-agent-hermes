"""Separate web/email layouts, original 16:9 editorial scenes, offline only."""
import base64,json,subprocess
from pathlib import Path
from html import escape as e
from email.message import EmailMessage
from email.policy import SMTP
from newsletter_v3 import C,date_label,event_label
ROOT=Path(__file__).resolve().parent
ASSET=ROOT/'data/frontend/welispeak_v5_assets'
BLUE='#0F2A60'; GOLD='#F0B100'; INK='#0F172B'; BG='#F1F5F9'

SCENES=[
# Fish market: stall, crates and products, not a location photograph.
'''<path d="M0 230H640V360H0Z" fill="#D6E2EC"/><path d="M55 93H580L552 45H82Z" fill="#0F2A60"/><path d="M55 93H580V113H55Z" fill="#F0B100"/><path d="M80 113V279M553 113V279" stroke="#0F2A60" stroke-width="12"/><path d="M90 220H550L565 290H75Z" fill="#B7CADA"/><path d="M95 220H550V239H95Z" fill="#0F2A60"/><g fill="#FFFFFF" stroke="#0F2A60" stroke-width="3"><path d="M137 170Q175 130 222 170Q176 209 137 170L115 150V190Z"/><path d="M269 173Q310 132 354 173Q308 209 269 173L246 151V193Z"/><path d="M399 170Q443 130 488 170Q441 207 399 170L376 148V191Z"/></g><g fill="#0F2A60"><circle cx="202" cy="166" r="4"/><circle cx="334" cy="169" r="4"/><circle cx="469" cy="166" r="4"/></g><path d="M125 261H244V314H125ZM277 261H397V314H277ZM430 261H530V314H430Z" fill="#F0B100"/><path d="M138 279H231M290 279H383M443 279H518" stroke="#FFFFFF" stroke-width="7"/>''',
# Full studio scene: camera, backdrop, lighting and monitor.
'''<path d="M0 270H640V360H0Z" fill="#D6E2EC"/><path d="M266 55H560V256H266Z" fill="#0F2A60"/><path d="M280 70H546V242H280Z" fill="#B7CADA"/><path d="M385 70V242" stroke="#FFFFFF" stroke-width="3"/><path d="M130 198L103 307M130 198L158 307M130 198V316" stroke="#0F2A60" stroke-width="9"/><rect x="73" y="134" width="123" height="72" rx="9" fill="#0F2A60"/><path d="M196 151L236 134V206L196 190Z" fill="#F0B100"/><circle cx="111" cy="126" r="28" fill="#F0B100"/><circle cx="162" cy="126" r="22" fill="#B7CADA"/><path d="M55 45L105 69L85 111L35 89Z" fill="#F0B100"/><path d="M58 102V271M538 91V292" stroke="#0F2A60" stroke-width="6"/><path d="M501 43H579V92H501Z" fill="#F0B100"/><rect x="375" y="270" width="113" height="65" rx="4" fill="#0F2A60"/><rect x="385" y="280" width="93" height="38" fill="#FFFFFF"/>''',
# Forest and traceability: forest, tagged log and record device.
'''<path d="M0 240Q190 180 340 244T640 230V360H0Z" fill="#D6E2EC"/><g fill="#0F2A60"><path d="M82 241V116H94V241Z M48 153L88 52L130 153Z M130 238V128H142V238Z M104 162L137 79L175 162Z M200 233V103H211V233Z M162 145L206 38L254 145Z M304 250V119H316V250Z M271 159L310 62L350 159Z"/></g><path d="M87 170H139M206 139H248" stroke="#F0B100" stroke-width="6"/><rect x="108" y="264" width="250" height="57" rx="27" fill="#B7CADA" stroke="#0F2A60" stroke-width="4"/><ellipse cx="333" cy="292" rx="23" ry="28" fill="#F0B100"/><ellipse cx="333" cy="292" rx="13" ry="18" fill="none" stroke="#0F2A60" stroke-width="3"/><rect x="177" y="274" width="60" height="33" fill="#FFFFFF"/><path d="M185 278V301M193 278V301M202 278V301M216 278V301M226 278V301" stroke="#0F2A60" stroke-width="3"/><rect x="416" y="102" width="133" height="207" rx="15" fill="#0F2A60"/><rect x="427" y="119" width="111" height="163" rx="6" fill="#FFFFFF"/><path d="M442 145H520M442 167H506M442 190H520" stroke="#B7CADA" stroke-width="8"/><path d="M450 238L468 254L510 216" fill="none" stroke="#F0B100" stroke-width="10"/>''',
# Investment sectors: urban industry, energy, healthcare, financial chart.
'''<path d="M0 281H640V360H0Z" fill="#D6E2EC"/><g fill="#B7CADA"><path d="M60 118H149V280H60Z M173 177H250V280H173Z M283 143H362V280H283Z M396 177H486V280H396Z M519 103H586V280H519Z"/></g><g fill="#0F2A60"><path d="M73 138H89V160H73Z M113 138H129V160H113Z M73 183H89V205H73Z M113 183H129V205H113Z M185 199H236V210H185Z M294 177H350V187H294Z M536 121H566V258H536Z"/></g><path d="M430 198V249M405 223H456" stroke="#FFFFFF" stroke-width="14"/><path d="M326 195L310 223H330L317 254L349 215H330L342 195Z" fill="#F0B100"/><path d="M93 93L206 121L307 70L417 106L541 45" fill="none" stroke="#F0B100" stroke-width="9"/><path d="M512 43L546 42L541 75" fill="none" stroke="#F0B100" stroke-width="9"/><g fill="#F0B100"><ellipse cx="192" cy="312" rx="43" ry="11"/><ellipse cx="192" cy="298" rx="43" ry="11"/><ellipse cx="192" cy="284" rx="43" ry="11"/></g>''',
# Urban mobility: bus, bus stop, cycle and skyline.
'''<path d="M0 252H640V360H0Z" fill="#D6E2EC"/><g fill="#B7CADA"><path d="M26 91H90V240H26Z M108 52H176V240H108Z M194 113H244V240H194Z M449 58H522V240H449Z M542 107H605V240H542Z"/></g><path d="M0 303H640" stroke="#FFFFFF" stroke-width="4" stroke-dasharray="36 22"/><rect x="95" y="162" width="326" height="112" rx="18" fill="#0F2A60"/><rect x="112" y="177" width="215" height="46" rx="4" fill="#FFFFFF"/><path d="M184 177V223M256 177V223" stroke="#0F2A60" stroke-width="5"/><rect x="344" y="177" width="54" height="82" rx="4" fill="#F0B100"/><circle cx="156" cy="275" r="22" fill="#0F172B"/><circle cx="363" cy="275" r="22" fill="#0F172B"/><circle cx="156" cy="275" r="9" fill="#FFFFFF"/><circle cx="363" cy="275" r="9" fill="#FFFFFF"/><path d="M473 140V269M467 140H593V151H467Z" stroke="#0F2A60" stroke-width="6"/><circle cx="495" cy="312" r="23" fill="none" stroke="#0F2A60" stroke-width="4"/><circle cx="568" cy="312" r="23" fill="none" stroke="#0F2A60" stroke-width="4"/><path d="M495 312L522 269L545 312H495L525 288H556L568 312M547 270H566" fill="none" stroke="#F0B100" stroke-width="5"/>''',
# Agriculture and processing: field rows, crop and processing facility.
'''<path d="M0 211Q160 150 338 219T640 189V360H0Z" fill="#D6E2EC"/><g stroke="#0F2A60" stroke-width="5" fill="none"><path d="M0 356L253 211M126 360L282 218M270 360L312 224M414 360L343 226M558 360L373 228"/></g><path d="M362 139L417 104V139L474 104V139H571V233H362Z" fill="#0F2A60"/><path d="M391 157H429V184H391Z M450 157H487V184H450Z M511 157H549V184H511Z" fill="#FFFFFF"/><path d="M527 73H552V139H527Z" fill="#F0B100"/><path d="M168 91V233" stroke="#0F2A60" stroke-width="7"/><g fill="#F0B100"><ellipse cx="149" cy="114" rx="16" ry="30" transform="rotate(-40 149 114)"/><ellipse cx="187" cy="137" rx="16" ry="30" transform="rotate(40 187 137)"/><ellipse cx="150" cy="161" rx="16" ry="30" transform="rotate(-40 150 161)"/><ellipse cx="187" cy="185" rx="16" ry="30" transform="rotate(40 187 185)"/></g><path d="M77 229H237" stroke="#0F2A60" stroke-width="5"/>'''
]
ALTS={
'fr':['Illustration générique d’un étal de poissons et de caisses de marché.','Illustration générique d’un plateau audiovisuel avec caméra, éclairage et moniteur.','Illustration générique de forêt, de grumes identifiées et de registre numérique.','Illustration générique des secteurs bancaire, énergétique et sanitaire et d’une courbe d’investissement.','Illustration générique de transports urbains avec bus, arrêt et vélo.','Illustration générique de cultures agricoles et d’une unité de transformation.'],
'en':['Generic illustration of a fish stall and market crates.','Generic illustration of an audiovisual studio with camera, lights and monitor.','Generic illustration of a forest, tagged timber and a digital record.','Generic illustration of banking, energy and healthcare sectors with an investment chart.','Generic illustration of urban transport with a bus, stop and bicycle.','Generic illustration of crops and an agricultural processing facility.']}

def make_assets():
 ASSET.mkdir(parents=True,exist_ok=True)
 result=[]
 for i,scene in enumerate(SCENES):
  svg=ASSET/f'editorial-{i+1}.svg';png=ASSET/f'editorial-{i+1}.png'
  if not png.exists():
   svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360"><rect width="640" height="360" fill="#F5F7FA"/><circle cx="560" cy="57" r="28" fill="#F0B100" opacity=".25"/>{scene}</svg>')
   subprocess.run(['/usr/bin/sips','-s','format','png',str(svg),'--out',str(png)],check=True,capture_output=True)
  result.append(png.read_bytes())
 return result

def build(data):
 art=make_assets();logo=(ROOT/'data/frontend/welispeak_original_logo.png').read_bytes();outputs={}
 for lang in ('fr','en'):
  fr=lang=='fr';c=C[lang];title='WELISPEAK — L’essentiel' if fr else 'WELISPEAK — The Brief';signature='L’actualité en français et en anglais.' if fr else 'News in French and English.'
  count=f"6 sujets · 3 médias : AIP, BENIN WEB TV, Fraternité Matin" if fr else '6 stories · 3 outlets: AIP, BENIN WEB TV, Fraternité Matin'
  caption='Illustration générique originale · Hermes Agent · CC0 1.0 — ne représente pas l’événement ni un lieu précis.' if fr else 'Original generic illustration · Hermes Agent · CC0 1.0 — not a depiction of the event or a specific location.'
  social='Chaîne WhatsApp — lien à configurer. Newsletter LinkedIn — lien à configurer.' if fr else 'WhatsApp channel — link not configured. LinkedIn newsletter — link not configured.'
  plain=[title,signature,c['date'],c['draft'],count,c['warning'],c['toc']]+[a[lang]['takeaway'] for a in data['articles']]
  def switches(email=False):
   controls=[]
   for code,label in [('fr','Français'),('en','English')]:
    active=code==lang;style=f'display:inline-block;box-sizing:border-box;min-height:44px;padding:12px 18px;line-height:20px;font-size:15px;font-weight:bold;text-decoration:none;color:{BLUE};background:{GOLD if active else "#FFFFFF"};border:1px solid {GOLD};border-radius:5px;'
    controls.append(f'<span style="{style}">{label}</span>' if email else f'<a href="welispeak_20261022_{code}_v5.html" style="{style}"'+(' aria-current="page"' if active else '')+f'>{label}</a>')
   return ' '.join(controls)
  header=f'<img class="logo" src="@@LOGO@@" width="240" height="60" alt="WELISPEAK — logo original" style="display:block;width:240px;max-width:100%;height:auto;margin:0 0 20px;">@@SWITCHES@@<h1 style="margin:24px 0 8px;font-size:30px;line-height:1.25;color:{BLUE};">{title}</h1><p style="font-size:17px;line-height:1.6;margin:0 0 18px;">{signature}</p><p style="font-size:14px;margin:0 0 14px;">{e(c["date"])}</p><span style="display:inline-block;padding:6px 10px;background:{GOLD};color:{BLUE};font-size:13px;font-weight:bold;">{e(c["draft"])}</span>'
  toc=f'<h2>{e(c["toc"])}</h2><ol>'+''.join(f'<li style="padding:5px 0;">{e(a[lang]["takeaway"])}</li>' for a in data['articles'])+f'</ol><p class="small">{e(count)}</p><p class="small">{e(c["warning"])}</p>'
  article_blocks=[]
  for i,a in enumerate(data['articles']):
   x=a[lang];meta=a['source']+' · '+c['published']+' '+date_label(a['published_at'],lang)+' · '+c['event']+' : '+event_label(a['event_date'],lang)
   image=f'<figure style="margin:20px 0;"><img class="editorial-image" src="@@ART{i}@@" width="240" height="135" alt="{e(ALTS[lang][i],quote=True)}" style="display:block;width:240px;max-width:100%;height:auto;border-radius:7px;"><figcaption style="max-width:360px;font-size:12px;line-height:1.6;color:#526574;margin-top:7px;">{e(caption)}</figcaption></figure>'
   button=f'<a class="button" href="{e(a["url"],quote=True)}" style="display:inline-block;box-sizing:border-box;min-height:44px;padding:12px 20px;background:{GOLD};color:{BLUE};font-size:16px;line-height:20px;font-weight:bold;text-decoration:none;border-radius:5px;">{e(c["read"])} &rarr;</a>'
   block=f'<p style="margin:0 0 12px;font-size:13px;font-weight:bold;color:{BLUE};">{e(x["category"])}</p><h2>{e(x["title"])}</h2><p class="small">{e(meta)}</p>{image}<p>{e(x["summary"])}</p><h3>{e(c["stakes"])}</h3><p>{e(x["relevance"])}</p><p style="padding:14px 16px;background:#FFF8E1;font-size:15px;line-height:1.6;border-radius:5px;"><strong>{e(c["caveat"])}.</strong> {e(x["caveat"])}</p>{button}'
   article_blocks.append(block)
   plain += [x['category'],x['title'],meta,caption,x['summary'],c['stakes']+': '+x['relevance'],c['caveat']+': '+x['caveat'],a['url']]
  notes=('Six illustrations originales de scènes éditoriales créées pour cette revue : Hermes Agent, CC0 1.0. Aucun visuel d’article de presse repris. Illustrations génériques, non photographies des événements. Logo officiel WELISPEAK, fichier original du site, proportions conservées ; la licence CC0 ne s’applique pas au logo.' if fr else 'Six original editorial scene illustrations created for this brief: Hermes Agent, CC0 1.0. No press article images reused. Generic illustrations, not event photographs. Official WELISPEAK logo, original website asset, proportions preserved; the logo is not covered by CC0.')
  footer=f'<h2>{e(c["method"])}</h2>'+''.join(f'<p class="small"><a href="{e(a["url"],quote=True)}" style="color:{BLUE};">{e(a["source"])} — {e(a[lang]["title"])}</a></p>' for a in data['articles'])+f'<p class="small">{e(c["methodtext"])}</p><p class="small">{e(data["limits_"+lang])}</p><p class="small">{e(notes)} <a href="https://creativecommons.org/publicdomain/zero/1.0/" style="color:{BLUE};">CC0 1.0</a></p><p class="small">{e(c["end"])}</p>'
  follow=f'<h2>'+('Suivre la revue' if fr else 'Follow the brief')+f'</h2><p>{e(social)}</p>'
  css=f'''*{{box-sizing:border-box}}body{{margin:0;background:{BG};color:{INK};font-family:Arial,Helvetica,sans-serif;font-size:17px;line-height:1.6}}.container{{width:calc(100% - 32px);max-width:720px;margin:24px auto}}.block{{padding:28px;background:#FFFFFF;margin:0 0 20px;border:1px solid #DFE6EC;border-radius:8px}}header.block{{border-top:5px solid {GOLD}}}h2{{font-size:25px;line-height:1.3;color:{BLUE};margin:0 0 16px}}h3{{font-size:18px;line-height:1.4;color:{BLUE};margin:22px 0 8px}}p{{margin:0 0 18px}}.small{{font-size:14px;line-height:1.6;color:#526574}}a{{overflow-wrap:anywhere}}ol{{padding-left:24px;margin:0 0 20px}}@media(max-width:480px){{.container{{margin:16px auto}}.block{{padding:20px}}h1{{font-size:27px!important}}h2{{font-size:23px}}.editorial-image{{width:100%!important;max-width:100%!important;height:auto!important}}}}'''
  web=f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — V5</title><style>{css}</style></head><body><main class="container"><header class="block">{header}</header><section class="block">{toc}</section>'+''.join(f'<article class="block">{b}</article>' for b in article_blocks)+f'<section class="block">{follow}</section><footer class="block">{footer}</footer></main></body></html>'
  # A distinct, balanced presentation-table template; every section lives in one 640px table.
  emailcss=f'body,table,td,a{{font-family:Arial,Helvetica,sans-serif}}table{{border-collapse:collapse}}h2{{font-size:25px;line-height:1.3;color:{BLUE};margin:0 0 16px}}h3{{font-size:18px;color:{BLUE};margin:20px 0 8px}}p{{margin:0 0 18px}}.small{{font-size:14px;line-height:1.6;color:#526574}}a{{overflow-wrap:anywhere}}@media(max-width:480px){{.pad{{padding:20px!important}}h1{{font-size:27px!important}}h2{{font-size:23px!important}}.editorial-image{{width:100%!important;height:auto!important}}}}'
  def row(b):return f'<tr><td class="pad" bgcolor="#FFFFFF" style="padding:28px;font-size:17px;line-height:1.6;color:{INK};border-bottom:16px solid {BG};">{b}</td></tr>'
  email=f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{emailcss}</style></head><body style="margin:0;padding:0;background:{BG};"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr><td align="center" style="padding:16px;"><table role="presentation" width="640" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:640px;margin:0 auto;">'+row(header)+row(toc)+''.join(row(b) for b in article_blocks)+row(follow)+row(footer)+'</table></td></tr></table></body></html>'
  web=web.replace('@@SWITCHES@@',switches());email=email.replace('@@SWITCHES@@',switches(True))
  for token,png,cid in [('@@LOGO@@',logo,'v5-logo@draft.local')]+[(f'@@ART{i}@@',png,f'v5-art{i}@draft.local') for i,png in enumerate(art)]:
   web=web.replace(token,'data:image/png;base64,'+base64.b64encode(png).decode());email=email.replace(token,'cid:'+cid)
  plain += [social,c['method'],c['methodtext'],data['limits_'+lang],notes,'https://creativecommons.org/publicdomain/zero/1.0/',c['end']]
  text='\n\n'.join(plain)+'\n';msg=EmailMessage(policy=SMTP);msg['Subject']=title+' — '+c['date'];msg['X-Unsent']='1';msg.set_content(text);msg.add_alternative(email,subtype='html');related=msg.get_payload()[-1]
  for i,png in enumerate([logo]+art):related.add_related(png,maintype='image',subtype='png',cid='<v5-logo@draft.local>' if i==0 else f'<v5-art{i-1}@draft.local>',filename='welispeak-logo.png' if i==0 else f'editorial-{i}.png',disposition='inline')
  outputs[lang]={'web':web,'email':email,'text':text,'mime':msg.as_bytes()}
 return outputs

def main():
 data=json.loads((ROOT/'data/artifacts/edition_20261022_v3.json').read_text())
 for lang,out in build(data).items():
  (ROOT/f'data/frontend/welispeak_20261022_{lang}_v5.html').write_text(out['web'])
  # Browser email preview uses the same email template with embedded assets, not broken CID URLs.
  preview=out['email'];images=[(ROOT/'data/frontend/welispeak_original_logo.png').read_bytes()]+make_assets()
  for i,png in enumerate(images):preview=preview.replace('cid:v5-logo@draft.local' if i==0 else f'cid:v5-art{i-1}@draft.local','data:image/png;base64,'+base64.b64encode(png).decode())
  (ROOT/f'data/frontend/welispeak_20261022_{lang}_v5_email_preview.html').write_text(preview)
  (ROOT/f'data/briefs/welispeak_20261022_{lang}_v5.txt').write_text(out['text'])
  (ROOT/f'data/artifacts/welispeak_20261022_{lang}_v5_unsent.eml').write_bytes(out['mime'])
 print(json.dumps({'stories':6,'image_bytes':[len(p) for p in make_assets()],'web_max':720,'email_max':640,'sent':False}))
if __name__=='__main__':main()

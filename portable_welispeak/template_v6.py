"""Separate web/email layouts, original 16:9 editorial scenes, offline only."""
import base64,json
from pathlib import Path
from html import escape as e
from email.message import EmailMessage
from email.policy import SMTP
from editorial_utils import C,date_label,event_label
ROOT=Path(__file__).resolve().parent
ASSET=ROOT/'assets'
BLUE='#0F2A60'; GOLD='#F0B100'; INK='#0F172B'; BG='#F1F5F9'

ALTS={
'fr':['Illustration générique d’un étal de poissons et de caisses de marché.','Illustration générique d’un plateau audiovisuel avec caméra, éclairage et moniteur.','Illustration générique de forêt, de grumes identifiées et de registre numérique.','Illustration générique des secteurs bancaire, énergétique et sanitaire et d’une courbe d’investissement.','Illustration générique de transports urbains avec bus, arrêt et vélo.','Illustration générique de cultures agricoles et d’une unité de transformation.'],
'en':['Generic illustration of a fish stall and market crates.','Generic illustration of an audiovisual studio with camera, lights and monitor.','Generic illustration of a forest, tagged timber and a digital record.','Generic illustration of banking, energy and healthcare sectors with an investment chart.','Generic illustration of urban transport with a bus, stop and bicycle.','Generic illustration of crops and an agricultural processing facility.']}

def make_assets():
 return [(ASSET/f'editorial-{i}.png').read_bytes() for i in range(1,7)]

def build(data):
 art=make_assets();logo=(ASSET/'logo.png').read_bytes();outputs={}
 for lang in ('fr','en'):
  fr=lang=='fr';c=dict(C[lang]);c['date']=data['cutoff'];c['methodtext']=data.get('method_'+lang, ('Fenêtre de publication : 24 heures avant '+data['cutoff']+' ; heures UTC / Abidjan. Dates déclarées par la rédaction, à vérifier dans les sources.' if fr else 'Publication window: 24 hours before '+data['cutoff']+'; UTC / Abidjan. Editorially supplied timestamps must be checked against sources.'));title='WELISPEAK — L’essentiel' if fr else 'WELISPEAK — The Brief';signature='L’actualité en français et en anglais.' if fr else 'News in French and English.'
  count=str(len(data["articles"]))+(" sujets · " if fr else " stories · ")+str(len({a["source"] for a in data["articles"]}))+(" médias : " if fr else " outlets: ")+", ".join(sorted({a["source"] for a in data["articles"]}))
  caption='Illustration générique originale · Hermes Agent · CC0 1.0 — ne représente pas l’événement ni un lieu précis.' if fr else 'Original generic illustration · Hermes Agent · CC0 1.0 — not a depiction of the event or a specific location.'
  social='Chaîne WhatsApp — lien à configurer. Newsletter LinkedIn — lien à configurer.' if fr else 'WhatsApp channel — link not configured. LinkedIn newsletter — link not configured.'
  plain=[title,signature,c['date'],c['draft'],count,c['warning'],c['toc']]+[a[lang]['takeaway'] for a in data['articles']]
  def switches(email=False):
   controls=[]
   for code,label in [('fr','Français'),('en','English')]:
    active=code==lang;style=f'display:inline-block;box-sizing:border-box;min-height:44px;padding:12px 18px;line-height:20px;font-size:15px;font-weight:bold;text-decoration:none;color:{BLUE};background:{GOLD if active else "#FFFFFF"};border:1px solid {GOLD};border-radius:5px;'
    controls.append(f'<span style="{style}">{label}</span>' if email else f'<a href="#{ "francais" if code=="fr" else "english" }" style="{style}"'+(' aria-current="page"' if active else '')+f'>{label}</a>')
   return ' '.join(controls)
  header=f'<img class="logo" src="@@LOGO@@" width="240" height="60" alt="WELISPEAK — logo original" style="display:block;width:240px;max-width:100%;height:auto;margin:0 0 20px;">@@SWITCHES@@<h1 style="margin:24px 0 8px;font-size:30px;line-height:1.25;color:{BLUE};">{title}</h1><p style="font-size:17px;line-height:1.6;margin:0 0 18px;">{signature}</p><p style="font-size:14px;margin:0 0 14px;">{e(c["date"])}</p><span style="display:inline-block;padding:6px 10px;background:{GOLD};color:{BLUE};font-size:13px;font-weight:bold;">{e(c["draft"])}</span>'
  toc=f'<h2>{e(c["toc"])}</h2><ol>'+''.join(f'<li style="padding:5px 0;">{e(a[lang]["takeaway"])}</li>' for a in data['articles'])+f'</ol><p class="small">{e(count)}</p><p class="small">{e(c["warning"])}</p>'
  article_blocks=[]
  for i,a in enumerate(data['articles']):
   scene=int(a.get('scene_index',i%6));x=a[lang];meta=a['source']+' · '+c['published']+' '+date_label(a['published_at'],lang)+' · '+c['event']+' : '+event_label(a['event_date'],lang)
   image=f'<figure style="margin:20px 0;"><img class="editorial-image" src="@@ART{scene}@@" width="240" height="135" alt="{e(ALTS[lang][scene],quote=True)}" style="display:block;width:240px;max-width:100%;height:auto;border-radius:7px;"><figcaption style="max-width:360px;font-size:12px;line-height:1.6;color:#526574;margin-top:7px;">{e(caption)}</figcaption></figure>'
   button=f'<a class="button" href="{e(a["url"],quote=True)}" style="display:inline-block;box-sizing:border-box;min-height:44px;padding:12px 20px;background:{GOLD};color:{BLUE};font-size:16px;line-height:20px;font-weight:bold;text-decoration:none;border-radius:5px;">{e(c["read"])} &rarr;</a>'
   block=f'<p style="padding:10px 14px;font-size:13px;font-weight:bold;background:#0F2A60;color:#FFFFFF;border-left:5px solid #F0B100;">{e(x["category"])}</p><h2>{e(x["title"])}</h2><p class="small">{e(meta)}</p>{image}<p>{e(x["summary"])}</p><div style="padding:14px 16px;background:#FFF8E1;"><h3>{e(c["stakes"])}</h3><p>{e(x["relevance"])}</p></div><p style="padding:14px 16px;background:#FFF8E1;font-size:15px;line-height:1.6;border-radius:5px;"><strong>{e(c["caveat"])}.</strong> {e(x["caveat"])}</p>{button}'
   extras=''.join(f'<p><a href="{e(u,quote=True)}">{e(u)}</a></p>' for u in a.get('extra_sources',[]));block+=extras;plain+=a.get('extra_sources',[]);article_blocks.append(block)
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
  for token,png,cid in [('@@LOGO@@',logo,'welispeak-logo')]+[(f'@@ART{i}@@',png,f'welispeak-art{i}') for i,png in enumerate(art)]:
   web=web.replace(token,'data:image/png;base64,'+base64.b64encode(png).decode());email=email.replace(token,'cid:'+cid)
  plain += [social,c['method'],c['methodtext'],data['limits_'+lang],notes,'https://creativecommons.org/publicdomain/zero/1.0/',c['end']]
  text='\n\n'.join(plain)+'\n';msg=EmailMessage(policy=SMTP);msg['Subject']=title+' — '+c['date'];msg['X-Unsent']='1';msg.set_content(text);msg.add_alternative(email,subtype='html');related=msg.get_payload()[-1]
  for i,png in enumerate([logo]+art):related.add_related(png,maintype='image',subtype='png',cid='<welispeak-logo>' if i==0 else f'<welispeak-art{i-1}>',filename='welispeak-logo.png' if i==0 else f'editorial-{i}.png',disposition='inline')
  outputs[lang]={'web':web,'email':email,'text':text,'mime':msg.as_bytes()}
 return outputs

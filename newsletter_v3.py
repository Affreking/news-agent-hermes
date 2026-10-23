"""Compact V3 reader draft; original V2 and SMTP remain untouched."""
import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.policy import SMTP
from html import escape
import json
from pathlib import Path
from newsletter_design import illustration

ROOT=Path(__file__).resolve().parent
C={
'fr':{'mast':'REVUE DE PRESSE — CÔTE D’IVOIRE','date':'22 octobre 2026','lang':'FRANÇAIS','draft':'Brouillon — à valider','toc':'L’essentiel en 30 secondes','read':'Lire la source','stakes':'Les enjeux','caveat':'À retenir avec réserve','method':'Sources, crédits et méthode','period':'Publications du 21 au 22 octobre 2026 · heure d’Abidjan','published':'Publié le','event':'Événement','lead':'À LA UNE','credit':'Pictogrammes génériques originaux : Hermes Agent pour CI Press Brief, licence CC0 1.0. Ils illustrent les thèmes, pas les événements. Aucune photo de presse réutilisée. Les grandes images sont réservées aux photographies pertinentes dont les droits de réutilisation sont établis.','warning':'Sélection révisée, non envoyée. Les sources et leurs réserves restent indiquées dans chaque article ; la mise en page ne vaut pas certification des faits.','methodtext':'Fenêtre conservée : du 21 octobre 2026 à 13:32:44 au 22 octobre 2026 à 13:32:44, Africa/Abidjan (UTC+0). Les dates de publication proviennent de mentions structurées de chaque article avec décalage horaire explicite, pas de la date de consultation. Les dates des événements sont distinctes. Les anciens articles KOACI sans fuseau établi et le sujet parlementaire au décompte contradictoire ne sont pas reconduits. Les annonces et projections restent attribuées, sans les présenter comme réalisées.','end':'Document de relecture · Non publié · Aucun e-mail envoyé'},
'en':{'mast':'PRESS BRIEF — CÔTE D’IVOIRE','date':'22 October 2026','lang':'ENGLISH','draft':'Draft — pending review','toc':'The essentials in 30 seconds','read':'Read the source','stakes':'Business and policy implications','caveat':'Essential caveat','method':'Sources, credits and methodology','period':'Publications from 21–22 October 2026 · Abidjan time','published':'Published','event':'Event','lead':'LEAD STORY','credit':'Original generic pictograms: Hermes Agent for CI Press Brief, CC0 1.0 licence. They illustrate subjects, not reported events. No press photographs reused. Large images are reserved for relevant photographs with established reuse rights.','warning':'Revised selection, not sent. Sources and caveats remain visible in each story; visual presentation does not certify the facts.','methodtext':'Original window retained: 21 October 2026 at 13:32:44 to 22 October 2026 at 13:32:44, Africa/Abidjan (UTC+0). Publication dates come from each article’s structured notices with explicit offsets, not consultation dates. Event dates are separate. Earlier KOACI articles with unresolved timezones and the parliamentary story with conflicting bill counts have not been carried forward. Announcements and projections remain attributed rather than described as accomplished outcomes.','end':'Review document · Unpublished · No email sent'}}

def date_label(stamp,lang):
    d=datetime.fromisoformat(stamp).astimezone(__import__('zoneinfo').ZoneInfo('Africa/Abidjan'))
    return (f'{d.day} oct. à {d:%H:%M}' if lang=='fr' else f'{d.day} Oct at {d:%H:%M}')

def event_label(value,lang):
    try:
        d=datetime.fromisoformat(value)
        return f'{d.day} oct.' if lang=='fr' else f'{d.day} Oct'
    except ValueError:return value

def build(data):
    outputs={}; articles=data['articles']; media=sorted({a['source'] for a in articles})
    end=datetime.fromisoformat(data['cutoff'])
    for a in articles:
        dt=datetime.fromisoformat(a['published_at'])
        if dt.utcoffset() is None or not end-timedelta(hours=24)<=dt<=end: raise ValueError('publication outside window')
    for lang,c in C.items():
        count=f"{len(articles)} sujets · {len(media)} médias : {', '.join(media)}" if lang=='fr' else f"{len(articles)} stories · {len(media)} outlets: {', '.join(media)}"
        limit=data.get('limits_'+lang,'')
        text=[c['mast'],c['date']+' · '+c['lang'],c['draft'],c['period'],count,c['warning'],c['toc']]
        text += [a[lang]['takeaway'] for a in articles]
        rows=[]; assets=[]
        for i,a in enumerate(articles):
            x=a[lang]; png=illustration(a.get('icon',i%6)); assets.append(png)
            metadata=a['source']+' · '+c['published']+' '+date_label(a['published_at'],lang)+' · '+c['event']+' : '+event_label(a['event_date'],lang)
            text += [x['category'],x['title'],metadata,x['summary'],c['stakes']+' : '+x['relevance'],c['caveat']+' : '+x['caveat'],c['read']+' : '+a['url']]
            extra=''
            for u in a.get('extra_sources',[]):
                extra+=f'<p style="margin:12px 0 0;font-size:13px;line-height:1.6;"><a style="color:#102A43;" href="{escape(u,quote=True)}">{escape(u)}</a></p>'
                text.append(u)
            rows.append(f'''<tr><td style="padding:0 0 20px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#FFFFFF" style="border:1px solid #DFE6EC;">
<tr><td class="pad" style="padding:24px 28px 8px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr><td width="112" valign="top" style="width:112px;padding:0 16px 10px 0;"><img src="@@IMAGE{i}@@" width="96" height="36" alt="{escape(('Pictogramme générique : ' if lang=='fr' else 'Generic pictogram: ')+x['category'],quote=True)}" style="display:block;width:96px;height:36px;border:0;"></td><td valign="top" style="padding:5px 0 10px;font-size:12px;font-weight:bold;letter-spacing:0.8px;line-height:1.5;color:#16865B;">{escape(c['lead']+' · '+x['category'] if i==0 else x['category'])}</td></tr></table>
<h2 style="margin:5px 0 12px;font-size:{'28' if i==0 else '25'}px;line-height:1.3;color:#102A43;">{escape(x['title'])}</h2>
<p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#526574;">{escape(metadata)}</p></td></tr>
<tr><td class="pad" style="padding:0 28px 26px;">
<p style="margin:0 0 20px;font-size:17px;line-height:1.8;color:#243B53;">{escape(x['summary'])}</p>
<p style="margin:0 0 8px;font-size:15px;font-weight:bold;color:#102A43;">{escape(c['stakes'])}</p>
<p style="margin:0 0 18px;font-size:16px;line-height:1.75;color:#334E68;">{escape(x['relevance'])}</p>
<p style="margin:0 0 22px;padding:13px 15px;font-size:14px;line-height:1.7;color:#102A43;background:#FFF2E5;"><strong>{escape(c['caveat'])}.</strong> {escape(x['caveat'])}</p>
<table role="presentation" cellspacing="0" cellpadding="0" border="0"><tr><td bgcolor="#102A43" style="border-radius:4px;"><a href="{escape(a['url'],quote=True)}" style="display:inline-block;padding:13px 20px;color:#FFFFFF;text-decoration:none;font-size:15px;font-weight:bold;line-height:20px;">{escape(c['read'])} &rarr;</a></td></tr></table>{extra}</td></tr></table></td></tr>''')
        toc=''.join(f'<tr><td width="30" valign="top" style="padding:8px 0;font-weight:bold;color:#16865B;font-size:13px;">{i+1:02}</td><td style="padding:8px 0;font-size:15px;line-height:1.6;color:#243B53;">{escape(a[lang]["takeaway"])}</td></tr>' for i,a in enumerate(articles))
        sources=''.join(f'<p style="margin:0 0 12px;font-size:13px;line-height:1.7;"><a style="color:#102A43;" href="{escape(a["url"],quote=True)}">{i+1:02} · {escape(a["source"])} — {escape(a[lang]["title"])}</a></p>' for i,a in enumerate(articles))
        template=f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(c['mast'])} — V3 — {escape(c['date'])}</title><style>body,table,td,a{{font-family:Arial,Helvetica,sans-serif;}}body{{margin:0!important;padding:0!important;-webkit-text-size-adjust:100%;}}table{{border-collapse:collapse;}}img{{border:0;}}a:focus{{outline:3px solid #F58220;}}@media only screen and (max-width:640px){{.outer{{padding:12px 8px!important;}}.pad{{padding-left:20px!important;padding-right:20px!important;}}h1{{font-size:27px!important;}}h2{{font-size:24px!important;}}}}</style></head>
<body bgcolor="#FFFFFF" style="background:#FFFFFF;margin:0;padding:0;color:#243B53;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr><td class="outer" align="center" style="padding:30px 16px;"><table role="presentation" width="640" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:640px;">
<tr><td class="pad" bgcolor="#102A43" style="padding:30px 28px;color:#FFFFFF;"><p style="margin:0 0 18px;font-size:12px;font-weight:bold;letter-spacing:2px;">CI PRESS BRIEF · {c['lang']}</p><h1 style="margin:0;font-size:32px;line-height:1.2;color:#FFFFFF;">{escape(c['mast'])}</h1><p style="margin:20px 0;font-size:16px;">{c['date']}</p><table role="presentation" cellspacing="0" cellpadding="0"><tr><td bgcolor="#F58220" style="padding:7px 11px;color:#102A43;font-size:12px;font-weight:bold;">{escape(c['draft'])}</td></tr></table></td></tr>
<tr><td bgcolor="#16865B" height="5" style="height:5px;font-size:0;">&nbsp;</td></tr>
<tr><td class="pad" bgcolor="#FFFFFF" style="padding:25px 28px;"><h2 style="margin:0 0 14px;color:#102A43;font-size:23px;">{c['toc']}</h2><table role="presentation" width="100%" cellspacing="0" cellpadding="0">{toc}</table><p style="margin:18px 0 0;color:#526574;font-size:13px;line-height:1.7;">{escape(count)}</p><p style="margin:8px 0 0;color:#526574;font-size:13px;line-height:1.7;">{escape(c['warning'])}</p></td></tr>
<tr><td height="20">&nbsp;</td></tr>{''.join(rows)}
<tr><td id="method" class="pad" bgcolor="#E8EEF2" style="padding:26px 28px;"><h2 style="margin:0 0 20px;color:#102A43;font-size:22px;">{escape(c['method'])}</h2>{sources}<p style="margin:20px 0 12px;font-size:13px;line-height:1.75;color:#334E68;">{escape(c['methodtext'])}</p><p style="margin:0 0 12px;font-size:13px;line-height:1.75;color:#334E68;">{escape(limit)}</p><p style="margin:0;font-size:12px;line-height:1.7;color:#526574;">{escape(c['credit'])} <a href="https://creativecommons.org/publicdomain/zero/1.0/" style="color:#102A43;">CC0 1.0</a></p></td></tr>
<tr><td style="padding:22px;text-align:center;font-size:12px;color:#526574;">{escape(c['end'])}</td></tr></table></td></tr></table></body></html>'''
        text += [c['method'],c['methodtext'],count,limit,c['credit'],'https://creativecommons.org/publicdomain/zero/1.0/',c['end']]
        preview=email_html=template
        for i,png in enumerate(assets):
            preview=preview.replace(f'@@IMAGE{i}@@','data:image/png;base64,'+base64.b64encode(png).decode())
            email_html=email_html.replace(f'@@IMAGE{i}@@',f'cid:v3-{i}@draft.local')
        plain='\n\n'.join(text)+'\n'
        msg=EmailMessage(policy=SMTP); msg['Subject']=c['mast']+' — '+c['date']+' — '+c['draft']; msg['X-Unsent']='1'
        msg.set_content(plain); msg.add_alternative(email_html,subtype='html'); related=msg.get_payload()[-1]
        for i,png in enumerate(assets):related.add_related(png,maintype='image',subtype='png',cid=f'<v3-{i}@draft.local>',disposition='inline',filename=f'vignette-{i+1}.png')
        outputs[lang]={'html':preview,'text':plain,'mime':msg.as_bytes()}
    return outputs

def main():
    data=json.loads((ROOT/'data/artifacts/edition_20261022_v3.json').read_text())
    for lang,out in build(data).items():
        (ROOT/f'data/frontend/newsletter_20261022_{lang}_v3.html').write_text(out['html'])
        (ROOT/f'data/briefs/newsletter_20261022_{lang}_v3.txt').write_text(out['text'])
        (ROOT/f'data/artifacts/newsletter_20261022_{lang}_v3_unsent.eml').write_bytes(out['mime'])
    print(json.dumps({'stories':len(data['articles']),'distinct_media':len({a['source'] for a in data['articles']}),'sent':False}))
if __name__=='__main__':main()

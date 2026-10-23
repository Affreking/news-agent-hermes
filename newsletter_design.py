"""Offline email newsletter design: original CC0 PNG pictograms, no SMTP."""
import base64
import html
import json
import math
from pathlib import Path
import struct
import zlib
from email.message import EmailMessage
from email.policy import SMTP

ROOT = Path(__file__).resolve().parent
NAVY = '#102A43'
ORANGE = '#F58220'
GREEN = '#16865B'


def illustration(kind):
    """Rasterize simple original line pictograms with stdlib only."""
    w, h = 640, 240
    bg = (232, 240, 244)
    pixels = bytearray(bg * (w*h))
    navy, green, orange = (16,42,67), (22,134,91), (245,130,32)
    def point(x,y,color):
        x,y=int(x),int(y)
        if 0<=x<w and 0<=y<h:
            i=(y*w+x)*3; pixels[i:i+3]=bytes(color)
    def circle(x,y,r,color):
        for yy in range(int(y-r),int(y+r)+1):
            half=int(math.sqrt(max(0,r*r-(yy-y)**2)))
            for xx in range(int(x-half),int(x+half)+1): point(xx,yy,color)
    def line(x1,y1,x2,y2,color=navy,width=5):
        steps=max(abs(int(x2-x1)),abs(int(y2-y1)),1)
        for i in range(steps+1): circle(x1+(x2-x1)*i/steps,y1+(y2-y1)*i/steps,width//2,color)
    def path(coords,color=navy,width=5):
        for a,b in zip(coords,coords[1:]): line(*a,*b,color,width)
    # Restrained common ground and Ivorian accent marks.
    line(115,204,525,204,navy,2)
    line(115,205,210,205,orange,5); line(430,205,525,205,green,5)
    if kind == 0:
        upper=[(205,118),(240,82),(300,72),(360,88),(390,118)]
        lower=[(390,118),(360,150),(300,166),(240,154),(205,118)]
        path(upper); path(lower)
        path([(390,118),(440,79),(440,158),(390,118)],green)
        circle(245,111,6,navy)
        path([(300,74),(320,47),(338,81)],orange)
        line(260,185,370,185,green,3)
    elif kind == 1:
        path([(200,85),(320,36),(440,85),(200,85)])
        for x in (220,270,320,370,420):
            line(x,100,x,168,navy,7)
        line(195,179,445,179,green,7); line(185,192,455,192,navy,5)
        line(320,37,320,17,navy,3); line(322,19,351,19,orange,8)
    elif kind == 2:
        path([(174,133),(275,117),(324,49),(345,49),(322,115),(425,122),(458,108),(472,111),(443,139),(319,144),(345,180),(327,183),(282,145),(174,145),(174,133)])
        line(207,173,263,173,green,4); line(183,185,254,185,orange,4)
    elif kind == 3:
        path([(204,131),(435,131),(404,174),(245,174),(204,131)])
        path([(263,130),(263,91),(370,91),(370,130)])
        path([(301,90),(301,61),(336,61),(336,90)],green)
        for x in (281,312,343): line(x,109,x+8,109,navy,6)
        for x in (200,280,360): path([(x,190),(x+20,181),(x+40,190),(x+60,181)],green,3)
        line(336,62,368,62,orange,4)
    elif kind == 4:
        path([(217,83),(252,63),(294,77),(320,57),(365,72),(413,52),(438,157),(389,179),(341,160),(309,182),(266,162),(225,180),(217,83)])
        path([(294,77),(309,182)],green,3); path([(365,72),(389,179)],green,3)
        circle(333,95,20,orange); circle(333,95,8,bg)
        path([(319,108),(333,137),(347,108)],orange,5)
    else:
        path([(211,148),(211,85),(229,63),(403,63),(425,85),(425,148),(211,148)])
        path([(226,83),(410,83),(410,117),(226,117),(226,83)],green,4)
        for x in (235,393): circle(x,155,13,navy)
        for x in (242,390): line(x,133,x+12,133,orange,5)
        line(252,184,383,184,navy,2)
    def chunk(name,data):
        return struct.pack('!I',len(data))+name+data+struct.pack('!I',zlib.crc32(name+data)&0xffffffff)
    raw=b''.join(b'\x00'+pixels[y*w*3:(y+1)*w*3] for y in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')


COPY = {
 'fr': {
  'masthead':'REVUE DE PRESSE — CÔTE D’IVOIRE', 'date':'22 octobre 2026', 'language':'FRANÇAIS',
  'draft':'Brouillon — à valider', 'toc':'L’essentiel en 30 secondes', 'lead':'À LA UNE · ÉCONOMIE',
  'warning':'MAQUETTE DE LECTURE — NON VALIDÉE SUR LE FOND',
  'hold':'Les six sujets ci-dessous sont conservés pour la relecture du brouillon, mais restent exclus de la sélection publiable : le fuseau des horaires KOACI n’est pas établi et peut modifier leur admissibilité dans la fenêtre de 24 heures.',
  'window':'Fenêtre examinée : 21 octobre 2026 à 13:32:44 → 22 octobre 2026 à 13:32:44 · Africa/Abidjan (UTC+0).',
  'scope':'Un seul média distinct : KOACI, pour les six sujets. Une source institutionnelle primaire supplémentaire : l’Assemblée nationale, uniquement pour le calendrier parlementaire. Aucune corroboration indépendante multiple établie.',
  'categories':['ÉCONOMIE · CONSOMMATION','INSTITUTIONS · LÉGISLATION','MOBILITÉ · VOYAGES','LOGISTIQUE · SÉCURITÉ','FONCIER · GOUVERNANCE','TRANSPORT · CLIMAT'],
  'alts':['Pictogramme générique de poisson, illustration de la filière du poisson congelé.','Pictogramme générique de bâtiment parlementaire, sans représentation de l’événement.','Pictogramme générique d’avion, illustration des déplacements aéroportuaires.','Pictogramme générique de navire, illustration de la sécurité maritime.','Pictogramme générique de carte foncière avec repère, illustration des litiges fonciers.','Pictogramme générique de bus, illustration de la mobilité urbaine.'],
  'caption':'Illustration générique originale — ce n’est pas une photo de l’événement.',
  'enjeux':'Enjeux pour les entreprises et décideurs', 'read':'Lire la source', 'primary':'Consulter le compte rendu primaire',
  'publication':'Publication affichée par KOACI', 'zone':'fuseau non précisé', 'event':'Date de l’événement',
  'evidence':'Sources et réserves', 'status':'Admissibilité 24 h non établie — sujet exclu en attente de clarification.',
  'conflict':'CONTRADICTION À CONSERVER : 13 projets dans le compte rendu officiel, contre 12 chez KOACI. Seule l’adoption du calendrier est confirmée ; les décomptes ne concordent pas.',
  'footer':'Sources, crédits et méthode', 'credits':'Visuels : six pictogrammes originaux créés pour cette maquette. Auteur : Hermes Agent pour CI Press Brief. Origine : création interne, sans reprise de photographie d’article. Licence : CC0 1.0, mise à disposition sans restriction de réutilisation. Tous sont des illustrations génériques, jamais des photos des événements.',
  'method':'Les résumés reprennent le brouillon existant, sans nouvelle validation factuelle. Les dates d’événement sont séparées des dates de publication ; la consultation n’est pas utilisée comme date de publication. La confirmation primaire concerne le calendrier parlementaire et ne supprime ni la contradiction sur les textes, ni l’incertitude de publication. Les limites d’extraction sont maintenues dans les articles concernés.',
  'end':'Document local de relecture · Non publié · Aucun e-mail envoyé',
  'bullets':['Poisson : baisse provisoire annoncée ; application au détail à constater.','Parlement : calendrier adopté ; divergence entre 13 et 12 projets de loi.','Aéroport : prévoir une marge pour les accès routiers.','Mer : coopération régionale, sans nouvelles décisions opérationnelles confirmées.','Foncier : concertation envisagée, pas de procédure entrée en vigueur confirmée.','Mobilité : déclaration annoncée, sans financement précis confirmé.']
 },
 'en': {
  'masthead':'PRESS BRIEF — CÔTE D’IVOIRE','date':'22 October 2026','language':'ENGLISH',
  'draft':'Draft — pending review','toc':'The essentials in 30 seconds','lead':'LEAD STORY · ECONOMY',
  'warning':'READING MOCKUP — NOT FACTUALLY APPROVED',
  'hold':'The six stories below are preserved for review of the existing draft, but remain excluded from the publishable selection: KOACI’s timestamp timezone has not been established and may affect eligibility within the 24-hour window.',
  'window':'Window examined: 21 October 2026 at 13:32:44 → 22 October 2026 at 13:32:44 · Africa/Abidjan (UTC+0).',
  'scope':'One distinct news outlet: KOACI, for all six stories. One additional institutional primary source: the National Assembly, for the parliamentary timetable only. No independent multi-source corroboration established.',
  'categories':['ECONOMY · CONSUMER MARKETS','INSTITUTIONS · LEGISLATION','MOBILITY · TRAVEL','LOGISTICS · SECURITY','LAND · GOVERNANCE','TRANSPORT · CLIMATE'],
  'alts':['Generic fish pictogram illustrating the frozen-fish sector.','Generic parliament-building pictogram, not a depiction of the event.','Generic aircraft pictogram illustrating airport travel.','Generic ship pictogram illustrating maritime security.','Generic land-map and location-marker pictogram illustrating land disputes.','Generic bus pictogram illustrating urban mobility.'],
  'caption':'Original generic illustration — not a photograph of the event.',
  'enjeux':'Business and policy implications','read':'Read the source','primary':'Read the primary institutional account',
  'publication':'Publication displayed by KOACI','zone':'time zone unspecified','event':'Event date',
  'evidence':'Sources and caveats','status':'24-hour eligibility not established — excluded pending clarification.',
  'conflict':'DISCREPANCY TO RETAIN: 13 government bills in the official account versus 12 in KOACI. Only adoption of the timetable is confirmed; the counts do not agree.',
  'footer':'Sources, image credits and methodology','credits':'Visuals: six original pictograms created for this mockup. Author: Hermes Agent for CI Press Brief. Origin: in-house creation, with no reuse of article photographs. Licence: CC0 1.0, made available without reuse restrictions. All are generic illustrations, never photographs of the reported events.',
  'method':'Summaries reproduce the existing draft without new factual certification. Event dates are separate from publication dates; consultation dates are not treated as publication dates. Primary confirmation concerns the parliamentary timetable and resolves neither the bill-count discrepancy nor publication-time uncertainty. Extraction limits remain visible in the relevant stories.',
  'end':'Local review document · Unpublished · No email sent',
  'bullets':['Fish: provisional reduction announced; retail implementation remains unconfirmed.','Parliament: timetable adopted; discrepancy between 13 and 12 government bills.','Airport: allow extra time for road access.','At sea: regional cooperation, with no new operational decisions confirmed.','Land: consultation proposed, with no confirmed procedure in force.','Mobility: declaration reported, with no specific financing confirmed.']
 }
}


def build(data):
    assets=[illustration(i) for i in range(6)]
    outputs={}
    esc=lambda text: html.escape(str(text),quote=True)
    for lang,c in COPY.items():
        text=[c['masthead'],c['date']+' · '+c['language'],c['draft'],c['warning'],c['hold'],c['window'],c['scope'],c['toc']]+c['bullets']
        rows=[]
        for i,a in enumerate(data['articles']):
            item=a[lang]
            # Never render the unverified +00:00 from the old structured field.
            date=a['published_at'][:10]+' '+a['published_at'][11:16]+' · '+c['zone']
            metadata=c['publication']+' : '+date+' | '+c['event']+' : '+a['event_date']
            block=[c['categories'][i],item['title'],metadata,c['caption'],item['summary'],c['enjeux']+' : '+item['relevance'],c['evidence']+' : '+item['verification'],c['status']]
            if i==1: block.append(c['conflict'])
            block += [c['read']+' : '+a['url']]
            if a.get('primary_url'): block += [c['primary']+' : '+a['primary_url']]
            text += block
            marker='@@IMAGE'+str(i)+'@@'
            image=f'<img src="{marker}" width="640" height="240" alt="{esc(c["alts"][i])}" style="display:block;width:100%;max-width:640px;height:auto;border:0;background:#E8F0F4;">'
            label=c['lead'] if i==0 else c['categories'][i]
            conflict=f'<p style="margin:18px 0;padding:16px;background:#FFF2E5;color:#102A43;font-weight:bold;font-size:15px;line-height:1.6;">{esc(c["conflict"])}</p>' if i==1 else ''
            primary=f'<p style="margin:16px 0 0;"><a href="{esc(a["primary_url"])}" style="color:#102A43;text-decoration:underline;font-size:15px;">{esc(c["primary"])}</a></p>' if a.get('primary_url') else ''
            rows.append(f'''<tr><td style="padding:0 0 24px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#FFFFFF;border:1px solid #DFE6EC;">
<tr><td class="pad" style="padding:28px 30px 22px;">
<p style="margin:0 0 12px;color:#16865B;font-size:12px;font-weight:bold;letter-spacing:1.2px;">{esc(label)}</p>
<h2 id="story-{i+1}" style="margin:0;color:#102A43;font-size:{'30' if i==0 else '25'}px;line-height:1.25;font-weight:bold;">{esc(item['title'])}</h2>
<p style="margin:14px 0 0;color:#526574;font-size:13px;line-height:1.6;">{esc(metadata)}</p></td></tr>
<tr><td>{image}</td></tr>
<tr><td class="pad" style="padding:10px 30px 28px;">
<p style="margin:0 0 22px;font-size:12px;color:#526574;line-height:1.6;">{esc(c['caption'])}</p>
<p style="margin:0 0 22px;color:#243B53;font-size:17px;line-height:1.8;">{esc(item['summary'])}</p>
<h3 style="margin:0 0 8px;color:#102A43;font-size:16px;line-height:1.5;">{esc(c['enjeux'])}</h3>
<p style="margin:0 0 22px;color:#334E68;font-size:16px;line-height:1.75;">{esc(item['relevance'])}</p>
{conflict}
<p style="margin:0 0 9px;color:#102A43;font-weight:bold;font-size:13px;">{esc(c['evidence'])}</p>
<p style="margin:0 0 14px;color:#526574;font-size:14px;line-height:1.7;">{esc(item['verification'])}</p>
<p style="margin:0 0 22px;color:#102A43;font-size:13px;font-weight:bold;line-height:1.6;">{esc(c['status'])}</p>
<table role="presentation" cellspacing="0" cellpadding="0" border="0"><tr><td bgcolor="#102A43" style="border-radius:4px;"><a href="{esc(a['url'])}" style="display:inline-block;padding:14px 23px;border:1px solid #102A43;border-radius:4px;color:#FFFFFF;text-decoration:none;font-size:15px;font-weight:bold;line-height:20px;">{esc(c['read'])} &rarr;</a></td></tr></table>{primary}
</td></tr></table></td></tr>''')
        text += [c['footer'],c['scope']]
        source_items=[]
        for i,a in enumerate(data['articles'],1):
            text += [str(i)+'. '+a[lang]['title'],a['url']]
            source_items.append(f'<p style="margin:0 0 12px;font-size:13px;line-height:1.6;"><a href="{esc(a["url"])}" style="color:#102A43;text-decoration:underline;">{i:02d} · KOACI — {esc(a[lang]["title"])}</a></p>')
            if a.get('primary_url'): source_items.append(f'<p style="font-size:13px;line-height:1.6;"><a href="{esc(a["primary_url"])}" style="color:#102A43;">{esc(c["primary"])}</a></p>')
        text += [c['credits'],'https://creativecommons.org/publicdomain/zero/1.0/',c['method'],c['window'],c['end']]
        toc=''.join(f'<tr><td width="32" valign="top" style="padding:9px 0;color:#16865B;font-size:13px;font-weight:bold;">{i+1:02d}</td><td style="padding:9px 0;font-size:15px;line-height:1.6;color:#243B53;">{esc(b)}</td></tr>' for i,b in enumerate(c['bullets']))
        template=f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>{esc(c['masthead'])} — {esc(c['date'])} — {esc(c['draft'])}</title>
<style>body,table,td,a{{font-family:Arial,Helvetica,sans-serif;}}table{{border-collapse:collapse;}}body{{margin:0!important;padding:0!important;width:100%!important;-webkit-text-size-adjust:100%;}}img{{border:0;outline:none;text-decoration:none;}}a:focus{{outline:3px solid #F58220;outline-offset:3px;}}@media only screen and (max-width:640px){{.wrap{{width:100%!important;}}.outer{{padding:12px 8px!important;}}.pad{{padding-left:20px!important;padding-right:20px!important;}}.mast{{font-size:26px!important;}}h2{{font-size:24px!important;}}}}</style></head>
<body bgcolor="#FFFFFF" style="background:#FFFFFF;margin:0;padding:0;color:#243B53;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#FFFFFF"><tr><td class="outer" align="center" style="padding:32px 16px;">
<table role="presentation" class="wrap" width="640" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:640px;">
<tr><td bgcolor="#102A43" class="pad" style="padding:32px 30px;color:#FFFFFF;">
<p style="margin:0 0 16px;color:#FFFFFF;font-size:12px;letter-spacing:2px;font-weight:bold;">CI PRESS BRIEF · {esc(c['language'])}</p>
<h1 class="mast" style="margin:0;color:#FFFFFF;font-size:32px;line-height:1.2;letter-spacing:-0.5px;">{esc(c['masthead'])}</h1>
<p style="margin:20px 0 0;color:#FFFFFF;font-size:16px;">{esc(c['date'])}</p>
<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin-top:20px;"><tr><td bgcolor="#F58220" style="padding:7px 11px;color:#102A43;font-size:12px;font-weight:bold;">{esc(c['draft'])}</td></tr></table></td></tr>
<tr><td height="5" bgcolor="#16865B" style="height:5px;font-size:0;line-height:0;">&nbsp;</td></tr>
<tr><td class="pad" bgcolor="#FFF2E5" style="padding:22px 30px;">
<p style="margin:0 0 10px;font-size:12px;font-weight:bold;color:#102A43;letter-spacing:0.6px;">{esc(c['warning'])}</p>
<p style="margin:0;color:#243B53;font-size:14px;line-height:1.7;">{esc(c['hold'])}</p></td></tr>
<tr><td class="pad" bgcolor="#FFFFFF" style="padding:28px 30px;">
<h2 style="margin:0 0 16px;font-size:23px;line-height:1.3;color:#102A43;">{esc(c['toc'])}</h2>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">{toc}</table>
<p style="margin:18px 0 0;font-size:13px;line-height:1.7;color:#526574;">{esc(c['scope'])}</p></td></tr>
<tr><td height="24" style="height:24px;">&nbsp;</td></tr>
{''.join(rows)}
<tr><td class="pad" bgcolor="#E8EEF2" style="padding:28px 30px;">
<h2 style="margin:0 0 20px;font-size:22px;line-height:1.3;color:#102A43;">{esc(c['footer'])}</h2>
{''.join(source_items)}
<p style="margin:24px 0 12px;font-size:13px;line-height:1.75;color:#334E68;">{esc(c['credits'])} <a href="https://creativecommons.org/publicdomain/zero/1.0/" style="color:#102A43;">CC0 1.0</a></p>
<p style="margin:0 0 12px;font-size:13px;line-height:1.75;color:#334E68;">{esc(c['method'])}</p>
<p style="margin:0;font-size:12px;line-height:1.7;color:#526574;">{esc(c['window'])}</p></td></tr>
<tr><td style="padding:24px 20px;text-align:center;color:#526574;font-size:12px;line-height:1.7;">{esc(c['end'])}</td></tr>
</table></td></tr></table></body></html>'''
        preview=email_html=template
        for i,png in enumerate(assets):
            preview=preview.replace('@@IMAGE'+str(i)+'@@','data:image/png;base64,'+base64.b64encode(png).decode())
            email_html=email_html.replace('@@IMAGE'+str(i)+'@@',f'cid:ci-brief-{i+1}@draft.local')
        plain='\n\n'.join(text)+'\n'
        message=EmailMessage(policy=SMTP)
        message['Subject']=c['masthead']+' — '+c['date']+' — '+c['draft']
        message['X-Unsent']='1'
        message.set_content(plain)
        message.add_alternative(email_html,subtype='html')
        related=message.get_payload()[-1]
        for i,png in enumerate(assets): related.add_related(png,maintype='image',subtype='png',cid=f'<ci-brief-{i+1}@draft.local>',disposition='inline',filename=f'illustration-{i+1}.png')
        outputs[lang]={'html':preview,'email_html':email_html,'text':plain,'mime':message.as_bytes()}
    return outputs


def main():
    data=json.loads((ROOT/'data/artifacts/edition_20261022_editorial.json').read_text())
    outputs=build(data)
    for lang,out in outputs.items():
        (ROOT/f'data/frontend/newsletter_20261022_{lang}_v2.html').write_text(out['html'])
        (ROOT/f'data/briefs/newsletter_20261022_{lang}_v2.txt').write_text(out['text'])
        (ROOT/f'data/artifacts/newsletter_20261022_{lang}_v2_unsent.eml').write_bytes(out['mime'])
    print(json.dumps({'languages':list(outputs),'stories_per_draft':len(data['articles']),'original_pngs_per_email':6,'email_sent':False,'smtp_accessed':False}))

if __name__=='__main__': main()

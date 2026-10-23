"""Build and send exactly one approved presentation test. Never logs secrets."""
import json,os,re,smtplib,ssl,sqlite3
from pathlib import Path
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default,SMTP
from email.utils import formatdate,make_msgid,getaddresses
ROOT=Path(__file__).resolve().parent
RECIPIENT='ndriaffre@gmail.com'
SUBJECT='[TEST] WELISPEAK — L’essentiel | Édition du 22 octobre 2026'

def build():
 parts={l:BytesParser(policy=default).parsebytes((ROOT/f'data/artifacts/welispeak_20261022_{l}_v5_unsent.eml').read_bytes()) for l in ('fr','en')}
 htmls=[];plain=[];images={}
 notice='TEST DE RÉCEPTION ET DE PRÉSENTATION — ne vaut pas approbation factuelle. / RECEIPT AND LAYOUT TEST — not factual approval.'
 for lang,msg in parts.items():
  text=msg.get_body(preferencelist=('plain',)).get_content();plain.append(text)
  h=msg.get_body(preferencelist=('html',)).get_content()
  style=re.search(r'<style>(.*?)</style>',h,re.S).group(1)
  body=re.search(r'<body[^>]*>(.*?)</body>',h,re.S).group(1)
  # Genuine in-message section anchors, no local or invented hosted links.
  body=re.sub(r'<span style="([^"]*)">(Français|English)</span>',lambda m:'<a href="#'+('francais' if m[2]=='Français' else 'english')+'" style="'+m[1]+'">'+m[2]+'</a>',body)
  htmls.append(f'<section id="'+('francais' if lang=='fr' else 'english')+f'" lang="{lang}">{body}</section>')
  for p in msg.walk():
   if p.get_content_maintype()=='image':images[p['Content-ID']]=(p.get_payload(decode=True),p.get_filename())
 combined='<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+style+'</style></head><body style="margin:0;background:#F1F5F9;"><p style="max-width:600px;margin:16px auto;padding:0 16px;font:14px/1.6 Arial;color:#0F2A60;">'+notice+'</p>'+''.join(htmls)+'</body></html>'
 assert len(combined.encode())<100000
 assert not re.search(r'(?:href|src)=[\"\x27](?:file:|/Users/|data:|welispeak_2026)',combined)
 message=EmailMessage(policy=SMTP);message['Subject']=SUBJECT
 message['From']=os.environ['MAIL_FROM'];message['To']=RECIPIENT
 message['Date']=formatdate(localtime=False);message['Message-ID']=make_msgid(domain='welispeak.local')
 message.set_content(notice+'\n\nFRANÇAIS — puis ENGLISH ci-dessous\n\n'+'\n\n'.join(plain))
 message.add_alternative(combined,subtype='html');related=message.get_payload()[-1]
 for cid,(png,name) in images.items():related.add_related(png,maintype='image',subtype='png',cid=cid,filename=name,disposition='inline')
 assert len(images)==7
 for lang in ('fr','en'):
  data=json.loads((ROOT/'data/artifacts/edition_20261022_v3.json').read_text())
  for a in data['articles']:assert a[lang]['summary'] in message.get_body(preferencelist=('plain',)).get_content()
 return message

def main():
 db=sqlite3.connect(ROOT/'data/artifacts/delivery.sqlite');db.execute('CREATE TABLE IF NOT EXISTS delivery (id TEXT PRIMARY KEY,status TEXT,message_id TEXT)')
 key='test-20261022-ndriaffre-v5'
 if db.execute('SELECT status FROM delivery WHERE id=?',(key,)).fetchone():
  print(json.dumps({'status':'already_attempted_no_resend','recipient':RECIPIENT}));return
 required=['MAIL_HOST','MAIL_PORT','MAIL_FROM','MAIL_USER','MAIL_PASSWORD']
 if not all(os.environ.get(k) for k in required):print(json.dumps({'status':'missing_configuration'}));return
 if os.environ['MAIL_HOST'].lower().strip()!='smtp.gmail.com' or os.environ['MAIL_PORT'].strip()!='587':print(json.dumps({'status':'configuration_refused'}));return
 msg=build();sender=getaddresses([os.environ['MAIL_FROM']])[0][1]
 smtp=None;stage='connection';accepted=False
 try:
  smtp=smtplib.SMTP('smtp.gmail.com',587,timeout=30);smtp.set_debuglevel(0);smtp.ehlo();stage='starttls';smtp.starttls(context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'));smtp.ehlo();stage='authentication';smtp.login(os.environ['MAIL_USER'],os.environ['MAIL_PASSWORD'])
  db.execute('INSERT INTO delivery VALUES (?,?,?)',(key,'attempting',msg['Message-ID']));db.commit()
  stage='sending';refused=smtp.send_message(msg,from_addr=sender,to_addrs=[RECIPIENT]);accepted=True
  db.execute('UPDATE delivery SET status=? WHERE id=?',('accepted',key));db.commit()
  # Server acceptance is final; never resend if later verification fails.
  code,_=smtp.noop()
  result={'recipient':RECIPIENT,'subject':SUBJECT,'gmail_accepted':True,'refused_count':len(refused),'post_send_noop':code,'inbox_reception_verified':False}
  (ROOT/'data/artifacts/welispeak_test_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
  print(json.dumps(result,ensure_ascii=False))
 except Exception as exc:
  result={'status':'failed','stage':stage,'exception':type(exc).__name__,'smtp_code':getattr(exc,'smtp_code',None),'gmail_accepted':accepted}
  print(json.dumps(result))
 finally:
  if smtp:
   try:smtp.quit()
   except Exception:smtp.close()
  db.close()
if __name__=='__main__':main()

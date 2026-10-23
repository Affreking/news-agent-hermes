"""WELISPEAK V6 portable renderer. Python 3.10+; no network calls."""
import argparse
import base64
import json
import re
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.policy import SMTP
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import template_v6

ROOT = Path(__file__).resolve().parent
RECIPIENT = 'ndriaffre@gmail.com'
PREHEADER = 'Votre essentiel de l’actualité, en français et en anglais.'


def load_config(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    if config.get('recipient') != RECIPIENT:
        raise ValueError('Unique recipient must be ndriaffre@gmail.com')
    if config.get('linkedin_kind') not in (None, 'newsletter', 'page', 'profile'):
        raise ValueError('linkedin_kind must be newsletter, page or profile')
    for key in ('whatsapp_channel_url', 'linkedin_url', 'preference_url', 'unsubscribe_url'):
        value = config.get(key)
        if value is not None:
            parsed = urlsplit(value)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Audience URLs must be HTTPS or null')
    return config


def validate(data):
    end = datetime.fromisoformat(data['cutoff'])
    if end.utcoffset() is None:
        raise ValueError('Edition timezone required')
    if not 6 <= len(data['articles']) <= 8:
        raise ValueError('Edition requires 6–8 stories')
    identities, urls = set(), set()
    for article in data['articles']:
        if 'scene_index' in article and (type(article['scene_index']) is not int or not 0 <= article['scene_index'] <= 5):
            raise ValueError('scene_index must be integer 0–5')
        stamp = datetime.fromisoformat(article['published_at'])
        if stamp.utcoffset() is None or not end-timedelta(hours=24) <= stamp <= end:
            raise ValueError('Publication outside explicit 24h window')
        if article['story_id'] in identities or article['url'] in urls:
            raise ValueError('Duplicate story or URL')
        identities.add(article['story_id']); urls.add(article['url'])
        for url in [article['url']] + article.get('extra_sources', []):
            if urlsplit(url).scheme not in ('http', 'https') or not urlsplit(url).hostname:
                raise ValueError('Invalid source URL')
        for lang in ('fr', 'en'):
            for key in ('category', 'title', 'summary', 'relevance', 'caveat', 'takeaway'):
                if not isinstance(article[lang][key], str) or not article[lang][key].strip():
                    raise ValueError('Incomplete editorial content')
        if article['fr']['summary'] == article['en']['summary']:
            raise ValueError('English translation required')
    return end


def audience(config, lang, invite=False):
    fr = lang == 'fr'
    labels = {'newsletter': 'Newsletter LinkedIn', 'page': 'Page LinkedIn', 'profile': 'Profil LinkedIn' if fr else 'LinkedIn profile'}
    title = ('Recevez aussi notre essentiel sur WhatsApp' if fr else 'Get the essentials on WhatsApp') if invite else ('Restons connectés' if fr else 'Stay connected')
    buttons, text = [], [title]
    pairs = [('whatsapp_channel_url', 'WhatsApp')]
    if not invite:
        pairs += [('linkedin_url', labels.get(config.get('linkedin_kind'), 'LinkedIn')), ('preference_url', 'Préférences' if fr else 'Preferences'), ('unsubscribe_url', 'Se désabonner' if fr else 'Unsubscribe')]
    for key, label in pairs:
        url = config.get(key)
        style = 'display:inline-block;min-height:44px;padding:12px 18px;margin:4px;background:#F0B100;color:#0F2A60;font-weight:bold;text-decoration:none;box-sizing:border-box;'
        if url:
            buttons.append(f'<a style="{style}" href="{escape(url,quote=True)}">{escape(label)}</a>')
            text.append(label+': '+url)
        else:
            label += ' — lien à configurer' if fr else ' — link not configured'
            buttons.append(f'<span aria-disabled="true" style="{style}opacity:.65;">{escape(label)}</span>')
            text.append(label)
    return '<h2>'+title+'</h2>'+''.join(buttons), '\n'.join(text)


def build(data, config):
    validate(data)
    outputs = template_v6.build(data)
    fragments, texts = [], []
    for lang in ('fr', 'en'):
        original = outputs[lang]['email']
        # Retain original balanced V5 presentation-table rows; one bilingual table.
        start = original.index('<tr><td class="pad"')
        end = original.rindex('</table></td></tr></table>')
        fragment = original[start:end]
        if lang == 'en':
            fragment = re.sub(r'<img class="logo"[^>]+>', '', fragment, count=1)
        anchor = 'francais' if lang == 'fr' else 'english'
        fragment = fragment.replace('<td class="pad"', f'<td id="{anchor}" lang="{lang}" class="pad"', 1)
        fragment = fragment.replace('<span style="display:inline-block;box-sizing:border-box;', '<span style="display:inline-block;box-sizing:border-box;')
        # Replace static email switches with real internal anchors.
        fragment = re.sub(r'<span style="([^"]+)">(Français|English)</span>', lambda m: '<a style="'+m[1]+'" href="#'+('francais' if m[2]=='Français' else 'english')+'">'+m[2]+'</a>', fragment)
        invite, itext = audience(config, lang, True)
        follow, ftext = audience(config, lang)
        fragment = fragment.replace('</ol>', '</ol>'+invite, 1)
        fragment = re.sub(r'<h2>(Suivre la revue|Follow the brief)</h2><p>.*?</p>', follow, fragment, count=1)
        fragments.append(fragment)
        text = outputs[lang]['text'].replace('Chaîne WhatsApp — lien à configurer. Newsletter LinkedIn — lien à configurer.', '').replace('WhatsApp channel — link not configured. LinkedIn newsletter — link not configured.', '')
        texts.append(text+'\n'+itext+'\n'+ftext)
    archive = data.get('archive_example') is True
    badge = '<p style="padding:16px;background:#FFF8E1;">ARCHIVE EXEMPLE — NON ENVOYABLE / ARCHIVE EXAMPLE — NOT FOR SENDING</p>' if archive else ''
    html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>WELISPEAK V6</title></head><body style="margin:0;background:#F1F5F9;font-family:Arial,Helvetica,sans-serif;"><div style="display:none;max-height:0;overflow:hidden;">'+PREHEADER+'</div>'+badge+'<table role="presentation" width="100%"><tr><td align="center" style="padding:16px;"><table role="presentation" width="640" style="width:100%;max-width:640px;border-collapse:collapse;">'+''.join(fragments)+'</table></td></tr></table></body></html>'
    text = ('ARCHIVE EXEMPLE — NON ENVOYABLE\n' if archive else '')+PREHEADER+'\n\n'+'\n\n'.join(texts)
    msg = EmailMessage(policy=SMTP)
    sender = config.get('sender_email')
    if sender:
        from email.headerregistry import Address
        msg['From'] = Address('WELISPEAK — L’essentiel', addr_spec=sender)
    msg['To'] = RECIPIENT
    msg['Subject'] = 'WELISPEAK — L’essentiel / The Brief — '+data['cutoff'][:10]+(' — ARCHIVE EXEMPLE' if archive else '')
    msg['X-Unsent'] = '1'
    msg.set_content(text); msg.add_alternative(html, subtype='html')
    related = msg.get_payload()[-1]
    preview = html
    for i, png in enumerate([(ROOT/'assets/logo.png').read_bytes()]+template_v6.make_assets()):
        cid = 'welispeak-logo' if i == 0 else f'welispeak-art{i-1}'
        related.add_related(png, maintype='image', subtype='png', cid='<'+cid+'>', filename='logo.png' if i == 0 else f'editorial-{i}.png', disposition='inline')
        preview = preview.replace('cid:'+cid, 'data:image/png;base64,'+base64.b64encode(png).decode())
    return {'html': html, 'preview': preview, 'text': text, 'mime': msg.as_bytes()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input'); parser.add_argument('--output', required=True)
    parser.add_argument('--config', default=str(ROOT/'config.example.json'))
    args = parser.parse_args()
    out = build(json.loads(Path(args.input).read_text()), load_config(args.config))
    target = Path(args.output); target.mkdir(parents=True, exist_ok=True)
    for name, key in [('newsletter.html', 'preview'), ('newsletter.txt', 'text'), ('newsletter_unsent.eml', 'mime')]:
        path = target/name
        path.write_bytes(out[key]) if key == 'mime' else path.write_text(out[key], encoding='utf-8')
    print(json.dumps({'rendered': True, 'sent': False, 'html_bytes': len(out['html'].encode())}))

if __name__ == '__main__':
    main()

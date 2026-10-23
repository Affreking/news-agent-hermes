"""Read-only wrapper for portable WELISPEAK; renders artifacts, never sends.

Empty launch previews intentionally bypass the 6–8 article publication validator:
no articles are manufactured to satisfy a validator. They are never sendable.
"""
import argparse
import hashlib
import json
import re
import sys
import types
from html import escape
from pathlib import Path

DEFAULT_PORTABLE = Path(__file__).resolve().parent.parent / 'portable_welispeak'


def _portable(root):
    """Load only the three read-only renderer modules, without .pyc writes."""
    root = Path(root).resolve()
    saved = {name: sys.modules.get(name) for name in ('editorial_utils', 'template_v6')}
    try:
        for name in ('editorial_utils', 'template_v6', 'welispeak'):
            module = types.ModuleType(name)
            module.__file__ = str(root / (name + '.py'))
            if name != 'welispeak':
                sys.modules[name] = module
            exec(compile(Path(module.__file__).read_text(), module.__file__, 'exec'), module.__dict__)
        return module
    finally:
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def _banner(metadata, lang):
    fr = lang == 'fr'
    date = '1er novembre 2026' if fr else '1 November 2026'
    if metadata['date'] != '2026-11-01':
        date = metadata['date']
    label = 'APERÇU DU LANCEMENT — NON ENVOYABLE' if fr else 'LAUNCH PREVIEW — NOT FOR SENDING'
    return f'<aside style="padding:16px;background:#F0B100;color:#0F2A60;font-weight:bold;">{escape(label)}<br>{escape(metadata["label"])} · {escape(date)} · Africa/Abidjan</aside>'


def build_numbered(data, config, metadata, *, portable_root=DEFAULT_PORTABLE, context_preview=False):
    """Render an existing identity, without reserving, sending or confirming it.

    Identity must come from Registry/Coordinator. Rendering is not an approval
    authority. Archive samples always remain non-sendable, even if approved=true.
    """
    from copy import deepcopy
    from email import policy
    from email.parser import BytesParser
    portable = _portable(portable_root)
    source_date = data['cutoff'][:10]
    if source_date != metadata['date'] and not context_preview:
        raise ValueError('Editorial cutoff and official edition date differ')
    archive = data.get('archive_example') is True
    if archive and not context_preview:
        raise ValueError('Archive sample requires explicit historical context preview')
    number = metadata['number']
    if type(number) is not int or number < 1 or metadata.get('label') != f'Nº{number:03d}':
        raise ValueError('Invalid numbering identity')
    data = deepcopy(data)
    out = portable.build(data, config)
    languages = portable.template_v6.build(data)
    corrected = metadata.get('corrected') is True
    manifest = {key: metadata[key] for key in ('bulletin', 'date', 'number', 'label')}
    manifest.update(timezone='Africa/Abidjan', status='rendered_preview', published=False,
                    approved_for_send=False, sent=False, corrected=corrected,
                    article_count=len(data['articles']), source_content_date=source_date,
                    archive_example=archive, context_preview=context_preview)
    banners = {}
    for lang in ('fr', 'en'):
        fr = lang == 'fr'
        notice = 'APERÇU — NON ENVOYABLE' if fr else 'PREVIEW — NOT FOR SENDING'
        if corrected:
            notice += ' · ÉDITION CORRIGÉE' if fr else ' · CORRECTED EDITION'
        if context_preview:
            notice += (' · CONTEXTE HISTORIQUE DU ' if fr else ' · HISTORICAL CONTEXT FROM ') + source_date
        text = f'{metadata["label"]} · {metadata["date"]} · Africa/Abidjan · {notice}'
        banners[lang] = f'<aside style="padding:16px;background:#F0B100;color:#0F2A60;font-weight:bold;">{escape(text)}</aside>'
        languages[lang]['web'] = languages[lang]['web'].replace('<header class="block">', '<header class="block">'+banners[lang], 1)
        languages[lang]['email'] = languages[lang]['email'].replace('<body', '<body', 1).replace('<h1 ', banners[lang]+'<h1 ', 1)
        languages[lang]['text'] = text+'\n\n'+languages[lang]['text']
        # Drop stale per-language MIME; reconstruct with corrected bodies below.
        msg = BytesParser(policy=policy.default).parsebytes(languages[lang]['mime'])
        msg.replace_header('Subject', metadata['label']+' — '+str(msg['Subject'])+(' — ÉDITION CORRIGÉE / CORRECTED EDITION' if corrected else ''))
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                part.set_content(languages[lang]['text'])
            elif part.get_content_type() == 'text/html':
                part.set_content(languages[lang]['email'], subtype='html')
        languages[lang]['mime'] = msg.as_bytes()
    # Combined portable HTML has explicit language cells; keep bilingual numbering.
    for key in ('html', 'preview'):
        for lang, anchor in (('fr', 'francais'), ('en', 'english')):
            pattern = f'(<td id="{anchor}"[^>]*>)'
            out[key] = re.sub(pattern, lambda m: m[1]+banners[lang], out[key], count=1)
    out['text'] = languages['fr']['text']+'\n\n'+languages['en']['text']
    msg = BytesParser(policy=policy.default).parsebytes(out['mime'])
    msg.replace_header('Subject', metadata['label']+' — '+str(msg['Subject'])+(' — ÉDITION CORRIGÉE / CORRECTED EDITION' if corrected else ''))
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            part.set_content(out['text'])
        elif part.get_content_type() == 'text/html':
            part.set_content(out['html'], subtype='html')
    for lang in ('fr', 'en'):
        msg.add_attachment(languages[lang]['web'].encode(), maintype='text', subtype='html', filename=f'{metadata["label"]}_{lang}.html')
    out.update(mime=msg.as_bytes(), languages=languages, manifest=manifest, sent=False)
    return out


def write_archive(artifact, target):
    """Persist an unsent archive into a NEW directory; never alter the registry."""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    files = {'newsletter.html': artifact['preview'].encode(),
             'newsletter.txt': artifact['text'].encode(),
             'newsletter_unsent.eml': artifact['mime']}
    for lang in ('fr', 'en'):
        files[f'newsletter_{lang}.html'] = artifact['languages'][lang]['web'].encode()
    manifest = dict(artifact['manifest'], files={})
    for name, content in files.items():
        (target/name).write_bytes(content)
        manifest['files'][name] = hashlib.sha256(content).hexdigest()
    (target/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return manifest


def launch_preview(output, *, portable_root=DEFAULT_PORTABLE):
    portable = _portable(portable_root)
    data = {'cutoff': '2026-11-01T00:00:00+00:00', 'articles': [],
            'method_fr': 'Maquette vide du lancement. Aucune actualité du 1er novembre 2026 n’est affirmée. Aucun envoi, aucune publication, aucun numéro officiel réservé.',
            'method_en': 'Empty launch mock-up. No news for 1 November 2026 is asserted. No sending, no publication and no official number reserved.',
            'limits_fr': 'Contenu rédactionnel à préparer et à approuver humainement à la date de l’édition.',
            'limits_en': 'Editorial content must be prepared and approved by a human at the edition date.'}
    metadata = {'bulletin': 'WELISPEAK', 'date': '2026-11-01', 'number': 1, 'label': 'Nº001',
                'timezone': 'Africa/Abidjan', 'status': 'preview', 'published': False,
                'approved_for_send': False, 'official_number_reserved': False,
                'article_count': 0, 'sent': False, 'corrected': False, 'files': {}}
    outputs = portable.template_v6.build(data)
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    for lang in ('fr', 'en'):
        html = outputs[lang]['web'].replace('<header class="block">', '<header class="block">'+_banner(metadata, lang), 1)
        html = html.replace('href="#francais"', 'href="launch_fr.html"').replace('href="#english"', 'href="launch_en.html"')
        # Empty preview has no scene illustrations; retain only the original logo credit.
        html = re.sub(r'Six illustrations originales.*?Logo officiel', 'Aucune illustration d’article. Logo officiel', html)
        html = re.sub(r'Six original editorial.*?Official WELISPEAK', 'No article illustrations. Official WELISPEAK', html)
        name = f'launch_{lang}.html'
        (target/name).write_text(html, encoding='utf-8')
        metadata['files'][name] = hashlib.sha256(html.encode()).hexdigest()
    (target/'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent/'preview')
    parser.add_argument('--portable-root', type=Path, default=DEFAULT_PORTABLE)
    args = parser.parse_args()
    print(json.dumps(launch_preview(args.output, portable_root=args.portable_root), ensure_ascii=False))

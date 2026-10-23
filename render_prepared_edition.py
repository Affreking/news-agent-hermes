"""Render the prepared, source-grounded edition locally. No SMTP operations."""
import html
import json
from pathlib import Path
from datetime import datetime, timedelta
from email.message import EmailMessage

ROOT = Path(__file__).resolve().parent

def main():
    data = json.loads((ROOT / 'data/artifacts/edition_20261022_editorial.json').read_text())
    cutoff = datetime.fromisoformat(data['cutoff'])
    articles = data['articles']
    assert len({a['story_id'] for a in articles}) == len(articles)
    assert len({a['url'] for a in articles}) == len(articles)
    result = {}
    for lang in ('fr', 'en'):
        parts = ["CÔTE D’IVOIRE — REVUE DE PRESSE" if lang == 'fr' else 'CÔTE D’IVOIRE — PRESS BRIEF',
                 '22/10/2026 — BROUILLON NON ENVOYÉ' if lang == 'fr' else '22 October 2026 — UNSENT DRAFT',
                 data['publication_timezone_note_' + lang],
                 data['limits_' + lang]]
        for i, a in enumerate(articles, 1):
            assert cutoff - timedelta(hours=24) <= datetime.fromisoformat(a['published_at']) <= cutoff
            item = a[lang]
            assert 60 <= len(item['summary'].split()) <= 90
            refs = ''.join(f'[{n}]' for n in [a['citation']] + a.get('additional_citations', []))
            parts += [f"{i}. {item['title']}", item['summary'] + refs,
                      ('Intérêt pour les entreprises et décideurs : ' if lang == 'fr' else 'Business and policy relevance: ') + item['relevance'],
                      ('Publication : ' if lang == 'fr' else 'Published: ') + a['published_at'].replace('T', ' ') + ' — ' + a['source'],
                      ('Événement : ' if lang == 'fr' else 'Event: ') + a['event_date'],
                      item['verification'], a['url']]
            if a.get('primary_url'):
                parts.append(a['primary_url'])
        text = '\n\n'.join(parts) + '\n'
        assert 'artifacts/' not in text and '/Users/' not in text
        out = ROOT / f'data/briefs/edition_20261022_{lang}.txt'
        out.write_text(text)
        body = '\n'.join('<p>' + html.escape(part).replace('\n', '<br>') + '</p>' for part in parts)
        html_text = f'<!doctype html><html lang="{lang}"><meta charset="utf-8"><title>CI Press Brief</title><body style="color:#000;background:#fff;font:16px/1.6 Arial;max-width:900px;margin:32px auto">{body}</body></html>'
        html_path = ROOT / f'data/frontend/edition_20261022_{lang}.html'
        html_path.write_text(html_text)
        result[lang] = (text, html_text, html_path)
    msg = EmailMessage()
    msg['Subject'] = 'Côte d’Ivoire — Revue de presse FR/EN — 22/10/2026 — BROUILLON'
    # Deliberately no recipients or SMTP imports in this unsent artifact.
    msg.set_content(result['fr'][0] + '\n\n' + result['en'][0])
    msg.add_alternative(result['fr'][1] + result['en'][1], subtype='html')
    for lang in ('fr', 'en'):
        msg.add_attachment(result[lang][1].encode(), maintype='text', subtype='html', filename=result[lang][2].name)
    eml = ROOT / 'data/artifacts/edition_20261022_unsent.eml'
    eml.write_bytes(msg.as_bytes())
    (ROOT / 'data/briefs/edition_20261022_bilingual.txt').write_text(result['fr'][0] + '\n\n' + result['en'][0])
    report = {'sent': False, 'retained_count': len(articles), 'cutoff': data['cutoff'],
              'source_diversity_limit': 'Six news articles from KOACI, one primary parliamentary cross-check with conflicting bill count.',
              'truncated_extractions': ['zone-f-maritime-cooperation', 'cimdc-abidjan-declaration'],
              'excluded': ['Old budget and digital stories', 'General/category pages', 'Duplicate fish-price stories', 'School-desks story: insufficient extracted text'],
              'publication_timezone_assumption': 'KOACI displayed times interpreted as Africa/Abidjan; publisher timezone unconfirmed',
              'smtp_config_modified': False}
    (ROOT / 'data/artifacts/edition_20261022_technical.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'retained_count': len(articles), 'summary_word_counts': {a['story_id']: {l: len(a[l]['summary'].split()) for l in ('fr','en')} for a in articles}, 'html_attachments': len(list(msg.iter_attachments())), 'smtp_called': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()

"""Adapt the already-written edition to the offline validation schema; never send."""
import json
from pathlib import Path
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from news_brief import run

ROOT = Path(__file__).resolve().parent

def main():
    original = json.loads((ROOT / 'data/artifacts/edition_20261022_editorial.json').read_text())
    sources = {}
    for batch in (1, 2):
        for row in json.loads((ROOT / f'data/sources/editorial_retrieval_{batch}.json').read_text())['results']:
            if row.get('content'):
                sources[row['url']] = row['content']
    data = {'articles': [], 'limitations': [original['limits_fr'], original['limits_en']]}
    for lang in ('fr', 'en'):
        data['limitations_' + lang] = [original['publication_timezone_note_' + lang], original['limits_' + lang]]
    for old in original['articles']:
        item = {k: old[k] for k in ('story_id', 'url', 'source', 'published_at', 'event_date')}
        item['published_evidence'] = {'url': old['url'], 'excerpt': old['published_evidence'], 'published_at': old['published_at'], 'timezone_basis': 'KOACI: timezone unspecified; interpreted as Africa/Abidjan, not confirmed by publisher.'}
        for lang in ('fr', 'en'):
            item[lang] = {'title': old[lang]['title'], 'summary': old[lang]['summary'], 'interest': old[lang]['relevance'], 'verification_note': old[lang]['verification']}
        # Use the recorded evidence file's mtime as a conservative latest-known
        # consultation bound; do not pretend it is article publication time.
        citation = old['citation']
        evidence = ROOT / f'data/sources/evidence_{citation}.txt'
        consulted = datetime.fromtimestamp(evidence.stat().st_mtime, timezone.utc).isoformat()
        text = sources[old['url']]
        assert old['published_evidence'] in text
        item['verification'] = {'status': 'source_consulted', 'sources': [{'url': old['url'], 'origin': 'KOACI', 'consulted_at': consulted, 'excerpt': text}]}
        if old.get('primary_url'):
            primary = ROOT / 'data/sources/assembly_primary.txt'
            item['additional_source_urls'] = [old['primary_url']]
            item['verification']['sources'].append({'url': old['primary_url'], 'origin': 'Assemblée nationale de Côte d’Ivoire', 'consulted_at': datetime.fromtimestamp(primary.stat().st_mtime, timezone.utc).isoformat(), 'excerpt': primary.read_text(), 'is_primary': True, 'primary_evidence': 'Official National Assembly account of its own sitting; confirms timetable, disagrees with KOACI bill count.'})
            item['verification']['status'] = 'primary'
        data['articles'].append(item)
    path = ROOT / 'data/artifacts/edition_20261022_validated_input.json'
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    result = run(editorial_file=path, now=datetime.fromisoformat(original['cutoff']))
    assert result['report']['accepted_count'] == 6, result['report']
    assert result['report']['excluded_count'] == 0, result['report']
    for lang in ('fr', 'en'):
        (ROOT / f'data/frontend/edition_20261022_validated_{lang}.html').write_text(result['html_' + lang])
    (ROOT / 'data/artifacts/edition_20261022_validated_unsent.eml').write_bytes(result['mime_bytes'])
    (ROOT / 'data/artifacts/edition_20261022_validation_report.json').write_text(json.dumps(result['report'], ensure_ascii=False, indent=2))
    msg = BytesParser(policy=default).parsebytes(result['mime_bytes'])
    assert len(list(msg.iter_attachments())) == 2
    plain = msg.get_body(preferencelist=('plain',)).get_content()
    assert all(a[l]['summary'] in plain for a in data['articles'] for l in ('fr', 'en'))
    assert '/Users/' not in plain and 'artifacts/' not in plain
    assert not msg.get('To') and not msg.get('From') and msg['X-Unsent'] == '1'
    print(json.dumps({'accepted': result['report']['accepted_count'], 'excluded': result['report']['excluded_count'], 'html_attachments': 2, 'complete_plaintext_body': True, 'sent': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()

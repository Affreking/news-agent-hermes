"""Import the confirmed table, never reconstruct destination codes by hand."""
import json
from pathlib import Path
import re


def parse_spec(text):
    section = re.search(r'^## 18\..*?(?=^## |\Z)', text, re.M | re.S)
    if not section:
        raise ValueError('Section 18 missing')
    rows = []
    for line in section.group().splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 5 and cells[0].isdigit():
            number, fr, en, code, offer = cells
            if not re.fullmatch('[A-Z]{2}', code):
                raise ValueError('Invalid configuration code')
            rows.append(dict(number=int(number), fr=fr, en=en, code=code, offer=offer))
    if len(rows) != 31 or [r['number'] for r in rows] != list(range(31)):
        raise ValueError('Expected exact ordered table: CI + 30 destinations')
    if rows[0]['code'] != 'CI' or len({r['code'] for r in rows}) != 31:
        raise ValueError('Duplicate or missing destination')
    return {'source': 'AGENT_SPEC_CI_PRESS_BRIEF_v2.md §18', 'base': rows[0], 'destinations': rows[1:]}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('spec', type=Path)
    args = parser.parse_args()
    Path(__file__).with_name('destinations.json').write_text(
        json.dumps(parse_spec(args.spec.read_text()), ensure_ascii=False, indent=2) + '\n')

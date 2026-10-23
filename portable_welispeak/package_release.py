"""Release by explicit whitelist only; never inspect private source settings."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WHITELIST = (
    'welispeak.py', 'template_v6.py', 'editorial_utils.py', 'sender.py',
    'package_release.py', 'config.example.json', 'sources.json', 'requirements.txt',
    'README_V6.md', 'PROMPT_EDITION_V6.md', 'VERIFICATION_V6.json',
    'tests/test_portable.py', 'examples/archive_20261022.json',
    'example_output/newsletter.html', 'example_output/newsletter.txt',
    'example_output/newsletter_unsent.eml', 'assets/logo.png',
) + tuple(f'assets/editorial-{i}.png' for i in range(1, 7))


def scan(name, data):
    forbidden = (b'/Users/'+b'romaric', b'MAIL_'+b'PASSWORD', b'-----BEGIN '+b'PRIVATE KEY-----', b'-----BEGIN '+b'RSA PRIVATE KEY-----')
    if any(marker in data for marker in forbidden):
        raise ValueError('Forbidden marker in '+name)


def main():
    blobs = {}
    for name in WHITELIST:
        path = ROOT/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Nonregular release input: '+name)
        data = path.read_bytes(); scan(name, data); blobs[name] = data
    archive = ROOT.parent/'welispeak_portable.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in blobs.items():
            out.writestr('portable_welispeak/'+name, data)
    with zipfile.ZipFile(archive) as check:
        expected = {'portable_welispeak/'+name for name in WHITELIST}
        if set(check.namelist()) != expected or len(check.namelist()) != len(expected) or check.testzip() is not None:
            raise ValueError('Archive verification failed')
        for name in check.namelist(): scan(name, check.read(name))
    print(json.dumps({'archive': archive.name, 'files': len(blobs), 'bytes': archive.stat().st_size, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'scan': 'passed', 'sent': False}))

if __name__ == '__main__':
    main()

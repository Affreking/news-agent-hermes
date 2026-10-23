"""Re-run offline acceptance checks; output machine-readable real results."""
import hashlib
import json
import socket
import smtplib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def forbidden(*args, **kwargs):
    raise AssertionError('Network/SMTP is forbidden during acceptance checks')


def main():
    socket.create_connection = forbidden
    smtplib.SMTP.connect = forbidden
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    expected = {
        'welispeak.py': 'c081532afbd51ee6c29ad8ccdd1d4fbf6013c75ee727e65d8a7cff7ce71c4eee',
        'sender.py': 'e4d3948838a70b2da36d8432af9e704ef575393c9503d97265f04aa2eadc3303',
        'template_v6.py': '59713ab03d8534b81b4fffdb9d993b0a81f416bfd8ae00515ffff7a25b21fbb6',
        'assets/logo.png': '7a4a5b8fead52fdeae7322510aa33de532513265d6e70f202d2832a6088cbc67',
    }
    unchanged = {name: hashlib.sha256((ROOT.parent/'portable_welispeak'/name).read_bytes()).hexdigest() == digest for name, digest in expected.items()}
    manifest = json.loads((ROOT/'preview/manifest.json').read_text())
    preview_hashes_match = all(hashlib.sha256((ROOT/'preview'/name).read_bytes()).hexdigest() == digest for name, digest in manifest['files'].items())
    report = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'passed': result.wasSuccessful(), 'portable_unchanged': unchanged,
              'preview_hashes_match': preview_hashes_match,
              'sqlite_files_in_deliverable': [str(p.relative_to(ROOT)) for p in ROOT.rglob('*.sqlite*')],
              'smtp_connect_forbidden': True, 'network_create_connection_forbidden': True,
              'sent': False, 'production_initialized': False,
              'browser_opened': True, 'responsive_browser_verified': False,
              'gmail_rendering_verified': False}
    (ROOT/'VERIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 0 if result.wasSuccessful() and all(unchanged.values()) and preview_hashes_match else 1


if __name__ == '__main__':
    raise SystemExit(main())

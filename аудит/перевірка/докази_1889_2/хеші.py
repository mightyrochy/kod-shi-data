"""Звірити LF-блоби з обома записами SHA-256 без перетворення байтів PowerShell."""
import hashlib
import re
import subprocess
import sys

rev = sys.argv[1]
prefix = 'аудит/адаптери/gemini/'

def blob(path):
    return subprocess.check_output(['git', 'show', f'{rev}:{prefix}{path}'])

manifest = blob('m9v/хеші.psd1').decode('utf-8-sig')
doc = blob('НАЛАШТУВАННЯ.md').decode('utf-8-sig')
bad = 0
for name in ('gemini_run.ps1', 'gemini_publish.ps1', 'gemini_watch.ps1', 'queue_lanes.ps1', 'claude_run.ps1'):
    data = blob(name)
    actual = hashlib.sha256(data).hexdigest().upper()
    recorded = re.search(r"['\"]" + re.escape(name) + r"['\"]\s*=\s*['\"]([A-Fa-f0-9]{64})", manifest).group(1).upper()
    table = re.search(r'\| `' + re.escape(name) + r'` \| `([A-Fa-f0-9]{64})`', doc).group(1).upper()
    ok = actual == recorded == table
    bad += not ok
    print(f'{name}: blob={actual}; psd1={recorded}; table={table}; CRLF={data.count(bytes([13, 10]))}; equal={ok}')
print(f'HASHES equal={5-bad}/5 revision={rev}')
sys.exit(bool(bad))

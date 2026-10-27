"""Звіряє маніфест і документацію з SHA-256 блобів git (LF)."""
import hashlib
from pathlib import Path
import re
import subprocess
import sys


def main():
    """Завершується помилкою при розбіжності хешів або наборів файлів."""
    root = Path(__file__).resolve().parents[1]
    manifest = dict(re.findall(r"'([\w.]+\.ps1)'\s*=\s*'([0-9A-F]{64})'",
                              (root / 'm9v/хеші.psd1').read_text(encoding='utf-8-sig')))
    table = dict(re.findall(r"\| `([\w.]+\.ps1)` \| `([0-9A-F]{64})` \|",
                           (root / 'НАЛАШТУВАННЯ.md').read_text(encoding='utf-8')))
    if set(manifest) != set(table) or len(manifest) < 3:
        print('✗ набори файлів маніфесту й таблиці не збігаються')
        return 1
    bad = 0
    for name, expected in manifest.items():
        blob = subprocess.check_output(['git', 'show', f':аудит/адаптери/gemini/{name}'], cwd=root)
        actual = hashlib.sha256(blob).hexdigest().upper()
        ok = expected == table[name] == actual and b'\r\n' not in blob
        print(f"{'✓' if ok else '✗'} {name}: {actual}")
        bad += not ok
    return int(bool(bad))


if __name__ == '__main__':
    sys.exit(main())

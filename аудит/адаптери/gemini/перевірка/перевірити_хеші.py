"""Звіряє маніфест і документацію з SHA-256 блобів git (LF) і формат `смуги.json` v2."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ДАТА = r'(?<![0-9])(?:0[1-9]|[12][0-9]|3[01])\.(?:0[1-9]|1[0-2])(?![0-9])'


def є_джерело(текст):
    """Той самий розбір, що Test-LimitSource у queue_lanes.ps1: «власник ДД.ММ …» чи «вимір: …» з датою й числом."""
    if len(текст) > 300 or re.search(r'[\x00-\x1f]', текст):
        return False
    if re.fullmatch(r'власник ' + ДАТА + r'(?:[^0-9].*)?', текст, re.S):
        return True
    if not текст.startswith('вимір: '):
        return False
    дата = re.search(ДАТА, текст)
    return bool(дата) and bool(re.search(r'[0-9]', (текст[:дата.start()] + текст[дата.end():])[6:]))


def перевірити_смуги(root):
    """Кожна межа — {"n": число в стелі коду, "джерело": "" чи за форматом}; порожнє джерело — друк, не помилка."""
    код = (root / 'queue_lanes.ps1').read_text(encoding='utf-8-sig')
    стелі = {k: (int(a), int(b)) for k, a, b in re.findall(r'(\w+) = @\((\d+), (\d+)\)', код.split('$script:Ceil = @{', 1)[1].split('\n}', 1)[0])}
    смуги = re.search(r"LaneDefaults = \[ordered\]@\{ ([^}]*) \}", код).group(1)
    поля = {'slots.' + k: стелі['slots'] for k in re.findall(r'(\w+) = \d+', смуги)}
    поля.update({k: v for k, v in стелі.items() if k != 'slots'})
    try:
        дані = json.loads((root / 'смуги.json').read_text(encoding='utf-8'))
    except ValueError as e:
        print(f'✗ смуги.json не JSON: {e}')
        return 1
    вади = []
    if дані.get('v') != 2:
        вади.append('v не 2')
    знайдено = {'slots.' + k: v for k, v in (дані.get('slots') or {}).items()}
    знайдено.update({k: v for k, v in дані.items() if k not in ('v', 'slots')})
    вади += [f'зайве поле {k}' for k in sorted(set(знайдено) - set(поля))]
    вади += [f'нема поля {k}' for k in sorted(set(поля) - set(знайдено))]
    без = []
    for k in sorted(set(поля) & set(знайдено)):
        межа = знайдено[k]
        if not isinstance(межа, dict) or set(межа) != {'n', 'джерело'}:
            вади.append(f'{k}: не {{"n", "джерело"}}')
            continue
        n, джерело = межа['n'], межа['джерело']
        if isinstance(n, bool) or not isinstance(n, (int, float)) or not поля[k][0] <= n <= поля[k][1]:
            вади.append(f'{k}: n поза стелею {поля[k]}')
        if not isinstance(джерело, str) or (джерело and not є_джерело(джерело)):
            вади.append(f'{k}: джерело не за форматом')
        elif not джерело:
            без.append(k)
    for вада in вади:
        print(f'✗ смуги.json: {вада}')
    if not вади:
        print(f"✓ смуги.json: v2, полів {len(поля)}, без джерела (обгортка бере попереднє): {', '.join(без) or 'нема'}")
    return int(bool(вади))


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
    bad += перевірити_смуги(root)
    return int(bool(bad))


if __name__ == '__main__':
    sys.exit(main())

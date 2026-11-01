"""Звіряє маніфест і документацію з SHA-256 блобів git (LF) і формат `смуги.json` v2."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ДАТА = r'(?<![0-9])(?:0[1-9]|[12][0-9]|3[01])\.(?:0[1-9]|1[0-2])(?![0-9])'


def є_джерело(текст, механізм=False):
    """Той самий розбір, що Test-LimitSource у queue_lanes.ps1: «власник ДД.ММ …» чи «вимір: …» з датою й числом."""
    if len(текст) > 300 or re.search(r'[\x00-\x1f]', текст):
        return False
    if механізм and re.match(r'механізм: \S', текст):
        return True
    if re.fullmatch(r'власник ' + ДАТА + r'(?:[^0-9].*)?', текст, re.S):
        return True
    if not текст.startswith('вимір: '):
        return False
    дата = re.search(ДАТА, текст)
    return bool(дата) and bool(re.search(r'[0-9]', (текст[:дата.start()] + текст[дата.end():])[6:]))


def перевірити_смуги(root):
    """Кожна межа — {"n": число, "джерело": "" чи за форматом}; порожнє джерело — друк, не помилка. Стель у коді нема:
    криве n (не число, від'ємне, нуль для хвилин, дробові слоти) — помилка даних, як і відмова обгортки."""
    код = (root / 'queue_lanes.ps1').read_text(encoding='utf-8-sig')
    хвилини = re.search(r"LimitMinuteFields = @\(([^)]*)\)", код).group(1)
    смуги = re.search(r"LaneNames = @\(([^)]*)\)", код).group(1)
    поля = {'slots.' + k: True for k in re.findall(r"'(\w+)'", смуги)}
    поля.update({k: False for k in re.findall(r"'(\w+)'", хвилини)})
    механізми = set(re.findall(r"'(\w+)'", re.search(r"MechanismFields = @\(([^)]*)\)", код).group(1)))
    try:
        дані = json.loads((root / 'смуги.json').read_text(encoding='utf-8'))
    except ValueError as e:
        print(f'✗ смуги.json не JSON: {e}')
        return 1
    вади = []
    if дані.get('v') != 2:
        вади.append('v не 2')
    знайдено = {'slots.' + k: v for k, v in (дані.get('slots') or {}).items()}
    # claude_laptop — перелік нарядів Claude, яким потрібен ноутбук (#2211), не межа: лише назви-рядки.
    перелік = дані.get('claude_laptop', [])
    if not isinstance(перелік, list) or not all(isinstance(x, str) and x for x in перелік):
        вади.append('claude_laptop не перелік назв')
    знайдено.update({k: v for k, v in дані.items() if k not in ('v', 'slots', 'claude_laptop')})
    вади += [f'зайве поле {k}' for k in sorted(set(знайдено) - set(поля))]
    вади += [f'нема поля {k}' for k in sorted(set(поля) - set(знайдено))]
    без = []
    for k in sorted(set(поля) & set(знайдено)):
        межа = знайдено[k]
        if not isinstance(межа, dict) or set(межа) != {'n', 'джерело'}:
            вади.append(f'{k}: не {{"n", "джерело"}}')
            continue
        n, джерело = межа['n'], межа['джерело']
        слоти = поля[k]
        if isinstance(n, bool) or not isinstance(n, (int, float)) or n < 0 or (not слоти and n == 0) or (слоти and n != int(n)):
            вади.append(f'{k}: n не число, від\'ємне, нуль для хвилин чи дробові слоти')
        if not isinstance(джерело, str) or (джерело and not є_джерело(джерело, k in механізми)):
            вади.append(f'{k}: джерело не за форматом')
        elif not джерело:
            без.append(k)
    for вада in вади:
        print(f'✗ смуги.json: {вада}')
    if not вади:
        print(f"✓ смуги.json: v2, полів {len(поля)}, без джерела (межі нема): {', '.join(без) or 'нема'}")
    return int(bool(вади))


def main():
    """Завершується помилкою при розбіжності хешів або наборів файлів."""
    root = Path(__file__).resolve().parents[1]
    # Значення беруться як є, довжина й регістр — перевірка нижче: шаблон з {64} мовчки викидав зіпсований рядок
    # з обох словників, і маніфест із 63 знаками проходив (дошка 12231).
    manifest = dict(re.findall(r"'([\w.]+\.ps1)'\s*=\s*'([^']*)'",
                              (root / 'm9v/хеші.psd1').read_text(encoding='utf-8-sig')))
    table = dict(re.findall(r"\| `([\w.]+\.ps1)` \| `([^`]*)` \|",
                           (root / 'НАЛАШТУВАННЯ.md').read_text(encoding='utf-8')))
    зіпсовані = [f'{н}: {len(х)} знаків' for джерело in (manifest, table) for н, х in джерело.items()
                 if not re.fullmatch(r'[0-9A-F]{64}', х)]
    if зіпсовані:
        print('✗ хеш не з 64 шістнадцяткових знаків (верхній регістр): ' + '; '.join(зіпсовані))
        return 1
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

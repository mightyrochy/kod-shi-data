#!/usr/bin/env python3
"""Звірка ноутбука в ході пульсу диспетчера (менеджер 01.11: виводом скрипта, не пам'яттю).

Читає лише публічне: issue #1856 (стан ноутбука, пише обгортка) і `git ls-remote` (main, позначки).
Друкує: вік стану, версію копії обгортки проти main, останні рядки самооновлення, GPU, позначки без старту
з причиною, зайнятість смуг, рядки зупинки. Рядок «УВАГА» — що диспетчер розбирає в тому самому ході.
Запуск: python3 аудит/адаптери/пульс_ноутбука.py
"""
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.request

REPO = 'mightyrochy/kod-shi-data'


def стан():
    with urllib.request.urlopen(f'https://api.github.com/repos/{REPO}/issues/1856', timeout=30) as r:
        return json.load(r)


def розділ(тіло, назва):
    m = re.search(r'^### ' + re.escape(назва) + r'\n(.*?)(?=^### |\Z)', тіло, re.S | re.M)
    return m.group(1).strip() if m else ''


def main():
    увага = []
    main_sha = subprocess.run(['git', 'ls-remote', f'https://github.com/{REPO}', 'refs/heads/main'],
                              capture_output=True, text=True, check=True).stdout.split()[0]
    d = стан()
    тіло = d.get('body') or ''
    зараз = dt.datetime.now(dt.timezone.utc)
    m = re.search(r'оновлено (\S+Z)', тіло)
    вік = (зараз - dt.datetime.fromisoformat(m.group(1).replace('Z', '+00:00'))).total_seconds() / 60 if m else None
    print(f'main {main_sha}')
    print(f'стан #1856: оновлено {m.group(1) if m else "?"} · вік {вік:.0f} хв' if вік is not None else 'стан #1856: нема часу')
    if вік is None or вік > 5:
        увага.append(f'стан ноутбука старший за 5 хв ({вік and round(вік)} хв): вимкнено чи claude-run стоїть')
    for рядок in re.findall(r'^- версія: .*$', тіло, re.M):
        print(рядок)
    локальні = розділ(тіло, 'Локальні рядки обгортки').splitlines()
    онов = [l for l in локальні if 'ОНОВЛЕН' in l]
    for l in онов[-3:]:
        print(l.strip())
    if онов and 'ОНОВЛЕНО' not in онов[-1]:
        увага.append('останнє самооновлення не вдалось: ' + онов[-1].split(': ', 1)[-1])
    if онов and 'ОНОВЛЕНО' in онов[-1] and main_sha[:8] not in онов[-1]:
        print(f'  (останнє ОНОВЛЕНО — не на голові main {main_sha[:8]}; наступне — після звірки дерева обгортки)')
    gpu = re.search(r'^GPU: .*$', тіло, re.M)
    print(gpu.group(0) if gpu else 'GPU: ?')
    смуги = розділ(тіло, 'Смуги')
    for l in смуги.splitlines()[2:]:
        if not l.startswith('|'):
            break
        print('смуга ' + ' · '.join(c.strip() for c in l.strip('|').split('|')[:4]))
    без = [l for l in розділ(тіло, 'Позначки без старту').splitlines()[2:] if l.startswith('|')]
    print(f'позначок без старту: {len(без)}')
    for l in без:
        c = [x.strip() for x in l.strip('|').split('|')]
        print(f'  {c[0]} · з {c[1]} · {c[2]}')
    if без:
        увага.append(f'{len(без)} позначок без старту — причина в переліку вище')
    for l in локальні:
        if 'ЗАБЛОКОВАНО' in l or 'ТРИВОГА' in l or 'ЛАНЦЮГ' in l:
            print('зупинка: ' + l.strip())
    for у in увага:
        print('УВАГА: ' + у)
    return 0


if __name__ == '__main__':
    sys.exit(main())

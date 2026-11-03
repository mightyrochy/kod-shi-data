# -*- coding: utf-8 -*-
"""Порівнює коди всіх проб на двох комітах в ізольованих тимчасових деревах."""
import argparse
import concurrent.futures
import contextlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import time
import types


ІЗОЛЯТОР = 'a913f53b6e8acf6a63293eaa230e4037eb0bf23f'


def main():
    """Готує незалежні дерева кожній нитці й записує повний перелік кодів ДО/ПІСЛЯ."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--база', required=True)
    парсер.add_argument('--голова', default='HEAD')
    парсер.add_argument('--вихід', type=Path, required=True)
    парсер.add_argument('--ниток', type=int, default=4)
    парсер.add_argument('--стеля', type=int, default=120)
    парсер.add_argument('--лише', nargs='+')
    парсер.add_argument('--коди-бази', type=Path)
    парсер.add_argument('--без-стелі', nargs='*', default=[])
    а = парсер.parse_args()
    корінь = Path(__file__).resolve().parents[3]
    os.chdir(корінь)
    os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONHASHSEED='0',
                      STELYA=str(а.стеля))
    # Живий прогін не входить у цей наряд; оточення не повинно вмикати його неявно.
    for ключ in ('ZHYVA', 'MODEL_URL', 'MODEL', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY'):
        os.environ.pop(ключ, None)
    код = subprocess.check_output(['git', 'show', ІЗОЛЯТОР + ':джерела/прилади/лічба_проб.py'])
    ізолятор = types.ModuleType('ізолятор_проб')
    ізолятор.__file__ = str(корінь / 'джерела/прилади/лічба_проб.py')
    exec(compile(код, ізолятор.__file__, 'exec'), ізолятор.__dict__)
    стан_до = ізолятор.знімок_користувача()
    база, голова = [ізолятор.git(корінь, 'rev-parse', р).decode().strip()
                    for р in (а.база, а.голова)]
    попередні = {}
    if а.коди_бази:
        запис = json.loads(а.коди_бази.read_text(encoding='utf-8-sig'))
        if запис['ревізія'] != база:
            raise RuntimeError('Коди ДО належать іншій базі')
        попередні = запис['коди']
    переліки = [set(ізолятор.git(корінь, 'ls-tree', '-rz', '--name-only', р,
                                '--', 'джерела/проби').decode().split('\0'))
                for р in (база, голова)]
    проби = sorted(п for п in переліки[0] | переліки[1] if п.endswith('.py'))
    if а.лише:
        проби = [п for п in проби if п in а.лише]
    проби.sort(key=lambda п: п not in а.без_стелі)
    а.вихід.mkdir(parents=True, exist_ok=True)
    початок = time.monotonic()
    результати = []
    дерева = queue.Queue()
    # Клас ізолятора видаляє тільки власні TemporaryDirectory під TEMP.
    # Перевіряємо їхню межу до будь-якого reset/clean/cleanup.
    межа = Path(os.environ['TEMP']).resolve()
    if not межа.is_relative_to(корінь.parent):
        raise RuntimeError('TEMP має бути всередині теки задачі')
    with contextlib.ExitStack() as стек:
        захист = Path(стек.enter_context(tempfile.TemporaryDirectory(prefix='проби_без_мережі_')))
        (захист / 'sitecustomize.py').write_text(
            'import os, sys\n'
            'def контроль(подія, аргументи):\n'
            '    if подія == "socket.connect":\n'
            '        raise PermissionError("Порівняння проб без мережі та живої моделі")\n'
            '    if подія == "subprocess.Popen":\n'
            '        назва = os.path.basename(str(аргументи[0])).lower()\n'
            '        if назва in ("claude", "claude.exe", "lms", "lms.exe"):\n'
            '            raise PermissionError("Живий прогін поза цим нарядом")\n'
            'sys.addaudithook(контроль)\n', encoding='utf-8')
        середовище = ізолятор.Дерево_проби.середовище

        def без_мережі(дерево):
            """Застосовує однакове оточення без мережі до бази й голови."""
            env = середовище(дерево)
            env['PYTHONPATH'] = str(захист) + os.pathsep + env['PYTHONPATH']
            return env

        ізолятор.Дерево_проби.середовище = без_мережі
        каталог = корінь / 'джерела/каталог_повний.xml'
        if not каталог.exists():
            каталог = None
        for _ in range(а.ниток):
            пара = []
            for sha in (база, голова):
                дерево = ізолятор.Дерево_проби(sha, каталог)
                дерево = стек.enter_context(дерево)
                if not Path(дерево.корінь).resolve().is_relative_to(межа):
                    raise RuntimeError('Тимчасове дерево поза TEMP задачі')
                пара.append(дерево)
                каталог = Path(дерево.джерела, 'каталог_повний.xml')
            дерева.put(пара)

        def пара_кодів(проба):
            """Запускає ту саму пробу на базі й голові та повертає обидва результати."""
            пара = дерева.get()
            try:
                готове = попередні.get(проба)
                стеля = None if проба in а.без_стелі else (готове['стеля'] if готове else а.стеля)
                if готове and готове['стеля'] != стеля:
                    готове = None
                if готове and готове['результат']['проба'] != проба:
                    raise RuntimeError('Код ДО належить іншій пробі')
                до = готове['результат'] if готове else ізолятор.гнати(проба, стеля, пара[0])
                return {'проба': проба, 'до': до, 'після': ізолятор.гнати(проба, стеля, пара[1]),
                        'стеля': стеля, 'код_бази_з_попереднього_прогону': bool(готове)}
            finally:
                дерева.put(пара)

        with (а.вихід / 'пари.jsonl').open('w', encoding='utf-8') as файл, \
                concurrent.futures.ThreadPoolExecutor(max_workers=а.ниток) as пул:
            завдання = [пул.submit(пара_кодів, п) for п in проби]
            for готове in concurrent.futures.as_completed(завдання):
                пара = готове.result()
                результати.append(пара)
                файл.write(json.dumps(пара, ensure_ascii=False) + '\n')
                файл.flush()
                print(f"{len(результати)}/{len(проби)} {пара['проба']}: "
                      f"{пара['до']['rc']} → {пара['після']['rc']}", flush=True)
    різні = [п for п in результати if п['до']['rc'] != п['після']['rc']]
    стан_після = ізолятор.знімок_користувача()
    зміни = sorted(п for п in стан_до.keys() | стан_після.keys()
                   if стан_до.get(п) != стан_після.get(п))
    підсумок = {'база': база, 'голова': голова, 'ізолятор': ІЗОЛЯТОР,
                'python': sys.version, 'ниток': а.ниток, 'стеля': а.стеля,
                'мережа_та_жива_модель': False,
                'попередніх_кодів_бази': sum(п['код_бази_з_попереднього_прогону'] for п in результати),
                'проби_без_стелі': а.без_стелі,
                'проб': len(проби), 'пар': len(результати), 'різних_кодів': len(різні),
                'зміни_дерева_користувача': зміни,
                'секунд': round(time.monotonic() - початок, 1)}
    (а.вихід / 'підсумок.json').write_text(
        json.dumps(підсумок, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (а.вихід / 'коди.tsv').open('w', encoding='utf-8') as файл:
        файл.write('проба\tкод ДО\tкод ПІСЛЯ\n')
        for пара in sorted(результати, key=lambda п: п['проба']):
            файл.write(f"{пара['проба']}\t{пара['до']['rc']}\t{пара['після']['rc']}\n")
    print(json.dumps(підсумок, ensure_ascii=False))
    return int(bool(різні or зміни))


if __name__ == '__main__':
    sys.exit(main())

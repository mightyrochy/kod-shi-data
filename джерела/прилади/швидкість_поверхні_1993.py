# -*- coding: utf-8 -*-
"""Парний вимір 40 записів: ядро перевірки → поточне, CPython і Pyodide.

Сирі RGB й відповіді пишуться лише у --вихід поза git. Бази беруться з git;
спільні залежності — з поточної голови, щоб ізолювати зміну виміру.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ДЖЕРЕЛА = Path(__file__).resolve().parents[1]
КОРІНЬ = ДЖЕРЕЛА.parent
sys.path.insert(0, str(ДЖЕРЕЛА))
from поверхня_показ_212 import кадри


def читати(шлях):
    """Читає JSON UTF-8."""
    return json.loads(шлях.read_text(encoding='utf-8'))


def записати(шлях, дані):
    """Зберігає повні факти без округлення чисел."""
    шлях.write_text(json.dumps(дані, ensure_ascii=False, indent=2), encoding='utf-8')


def база(ша, імʼя, вихід):
    """Витягає оригінальний модуль із git без зміни робочого дерева."""
    шлях = вихід / (ша + '-' + імʼя)
    шлях.write_bytes(subprocess.check_output(
        ['git', 'show', ша + ':джерела/' + імʼя], cwd=КОРІНЬ))
    return шлях


def модуль(імʼя, шлях):
    """Піднімає окремий простір імен оригінального модуля."""
    опис = importlib.util.spec_from_file_location(імʼя, шлях)
    м = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(м)
    return м


def часи(значення):
    """Медіана й лінійний p90 в мілісекундах."""
    from surface import перцентиль
    return dict(медіана=перцентиль(значення, 50), p90=перцентиль(значення, 90), максимум=max(значення))


def без_меж(значення):
    """Прибирає лише новий провенанс; усі числа, латки й рішення лишаються у порівнянні."""
    if isinstance(значення, dict):
        return {к: без_меж(в) for к, в in значення.items() if к != 'колір_не_вимір'}
    if isinstance(значення, list):
        return [без_меж(в) for в in значення]
    return значення


def main():
    """Міряє обидві версії поруч, звіряє повні виходи та бюджет часу."""
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument('--тека', type=Path, required=True)
    ап.add_argument('--pyodide', type=Path, required=True)
    ап.add_argument('--вихід', type=Path, required=True)
    ап.add_argument('--база', default='665dfb48')
    ап.add_argument('--стара', default='9dd9f675')
    ап.add_argument('--невизначеність', action='store_true', help='дозволити тільки додавання меж кольору')
    а = ап.parse_args()
    а.тека, а.pyodide, а.вихід = (p.resolve() for p in (а.тека, а.pyodide, а.вихід))
    if а.вихід.is_relative_to(КОРІНЬ):
        ап.error('--вихід має бути поза робочим деревом')
    а.вихід.mkdir(parents=True, exist_ok=True)
    import surface as П
    import жнива_колір as Ж
    import річ_з_фото as Р
    from проби.поверхня_212 import споживачеві
    стара = база(а.стара, 'річ_з_фото.py', а.вихід)
    п_до = база(а.база, 'surface.py', а.вихід)
    р_до = база(а.база, 'річ_з_фото.py', а.вихід)
    Пдо = модуль('поверхня_до', п_до)
    Ждо = модуль('жнива_до', база(а.база, 'жнива_колір.py', а.вихід))
    Рдо = модуль('річ_до', р_до)
    Рдо._ПОВ = Пдо
    вих = []
    for з, кадр, маска, арр, пікселі, _ in кадри(а.тека):
        ряд = dict(ключ=з['ключ'], пікселі=пікселі)
        # Чергуємо порядок, щоб прогрів кадру не давав переваги одній версії.
        версії = [('до', Ждо, Рдо, Пдо), ('після', Ж, Р, П)]
        for імʼя, ж, р, п in версії[::1 if len(вих) % 2 == 0 else -1]:
            sys.modules['surface'] = п
            try:
                t = time.perf_counter()
                вимір = ж.виміряти_поверхню(кадр, маска, арр, джерело=з.get('маска'))
                ряд['жнива_' + імʼя + '_мс'] = (time.perf_counter()-t)*1000
                осн = ж.звести_колір(вимір['сегменти'], None, з.get('слова_крамниці'))[0] if вимір['придатна'] else None
                ряд['споживачеві_' + імʼя] = споживачеві(осн, з.get('слова_крамниці'), вимір['візерунок'] == 'однотонний')
                ряд['жнива_' + імʼя] = вимір
                t = time.perf_counter()
                ряд['показ_' + імʼя] = р.виміряти(пікселі, рамка=True)
                ряд['показ_' + імʼя + '_мс'] = (time.perf_counter()-t)*1000
            finally:
                sys.modules['surface'] = П
        вих.append(ряд)
        print(з['ключ'], *(round(ряд['жнива_' + v + '_мс']) for v in ('до', 'після')), flush=True)
    записати(а.вихід / 'cpython.json', вих)
    subprocess.run(['node', str(Path(__file__).with_suffix('.js')), str(а.pyodide),
                    str(а.вихід / 'cpython.json'), str(а.вихід / 'pyodide.json'),
                    str(стара), str(п_до), str(р_до)], check=True)
    пдо = читати(а.вихід / 'pyodide.json')
    підсумок = dict(голова=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=КОРІНЬ).decode().strip(),
                    база=а.база, стара=а.стара, кадрів=len(вих), python=sys.version)
    підсумок['cpython'] = {k: часи([р[k] for р in вих]) for k in
                           ('жнива_до_мс', 'жнива_після_мс', 'показ_до_мс', 'показ_після_мс')}
    підсумок['pyodide'] = {v: часи([р[v]['мс'] for р in пдо]) for v in ('стара', 'до', 'після')}
    підсумок['тотожні_cpython'] = {k: sum(р[k + '_до'] == р[k + '_після'] for р in вих)
                                  for k in ('жнива', 'споживачеві', 'показ')}
    підсумок['тотожні_pyodide'] = sum(р['до']['вимір'] == р['після']['вимір'] for р in пдо)
    if а.невизначеність:
        підсумок['числа_й_латки_cpython'] = {k: sum(без_меж(р[k + '_до']) == без_меж(р[k + '_після']) for р in вих)
                                            for k in ('жнива', 'споживачеві', 'показ')}
        підсумок['числа_й_латки_pyodide'] = sum(без_меж(р['до']['вимір']) == без_меж(р['після']['вимір']) for р in пдо)
    підсумок['телефон'] = 'не виміряно'
    підсумок['повний_нічний_прохід'] = 'не виміряно'
    підсумок['бюджет_показу'] = all(підсумок['pyodide']['після'][k] <= підсумок['pyodide']['стара'][k]
                                    for k in ('медіана', 'p90'))
    записати(а.вихід / 'підсумок.json', підсумок)
    print(json.dumps(підсумок, ensure_ascii=False, indent=2))
    assert len(вих) == 39
    assert all(n == 39 for n in підсумок['числа_й_латки_cpython' if а.невизначеність else 'тотожні_cpython'].values())
    assert підсумок['числа_й_латки_pyodide' if а.невизначеність else 'тотожні_pyodide'] == 39
    assert підсумок['бюджет_показу']


if __name__ == '__main__':
    main()

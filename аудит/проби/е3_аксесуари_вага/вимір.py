"""Відтворювана звірка всіх емісій частини: вихідна тека, [коміт ДО], [--батарея]."""
import collections
import gzip
import importlib
import json
import os
from pathlib import Path
import runpy
import sys
import traceback

КОРІНЬ = Path(__file__).resolve().parents[3]
ДЖЕРЕЛА = КОРІНЬ / 'джерела'
sys.path[:0] = [str(ДЖЕРЕЛА), str(ДЖЕРЕЛА / 'проби')]
МОДУЛІ = ('аксесуари_розмір', 'аксесуари_носіння', 'аксесуари_взуття')


def входи(каталог):
    """Повний каталог та сітки, що досягають кожної з дев'яти емісій."""
    import fit
    Р, Н, В = (importlib.import_module(ім) for ім in МОДУЛІ)
    вх = json.loads((ДЖЕРЕЛА / 'стенд_вх.json').read_text(encoding='utf-8'))
    т = fit.тіло(float(вх['зріст']), {к: float(з) for к, з in dict(вх['обхвати'], литка=42).items()})
    т['аксесуарні'] = dict(довжина_стопи_мм=250, міжзіницева_мм=80, голова_см=57)
    низ = dict(id='низ', назва='низ', слот='сукня', тип='сукня', довжина_рівень='міні', текстура='denim')
    пара = dict(id='пара', назва='пара', слот='взуття', тип='балетки')
    for р in каталог:
        ід = str(р.get('id'))
        yield ід, Р.ворота_розміру, (т, [р]), {}
        yield ід, В.халява_і_поділ, (т, [р]), {}
        yield ід, В.лінія_ноги, ([низ, р],), dict(особа=dict(L_шкіри=75.8))
        yield ід, Н.маса_взуття, ([низ, р] if р.get('слот') == 'взуття' else [р, пара],), {}
        for год in (2, 9):
            yield ід + '@' + str(год), Н.вартість_носіння, ([р],), dict(тривалість_год=год, поверхня='бруківка')
    for сл, поле, значення in (('взуття', 'устілка_см', [23, 24.9, 25.49, 25.5, 27, 27.01, 28, 30]),
                              ('окуляри', 'оправа', ['52-18-140', '60-18-140', 'невідомо']),
                              ('головний_убір', 'обхват_голови_см', [52, 55.49, 55.5, 57, 58.5, 58.51, 62])):
        for знач in значення:
            р = dict(id='межа', назва='межа', слот=сл, **{поле: знач})
            yield '%s/%s' % (сл, знач), Р.ворота_розміру, (т, [р]), {}
    for h in (4, 4.5, 5, 6, 7, 9, 12):
        for год in (1, 4, 6, 6.1, 9, 12):
            р = dict(пара, каблук_см=h)
            yield '%s/%s' % (h, год), Н.вартість_носіння, ([р, низ, dict(id='сумка', назва='сумка', слот='сумка')],), dict(тривалість_год=год)
    for см in range(20, 111, 2):
        for сл in ('взуття', 'сукня'):
            р = dict(id='край', назва='край', слот=сл, халява_см=см, поділ_см=см)
            yield '%s/%s' % (сл, см), В.халява_і_поділ, (т, [р]), {}
    for hex in ('#000000', '#444444', '#999999', '#deb295', '#ffffff'):
        р = dict(пара, виріз_стопи='високий', hex=hex)
        yield hex, В.лінія_ноги, ([низ, р],), dict(особа=dict(L_шкіри=75.8))


def main():
    """Зберегти повні знахідки, покриття й результат кожної перевірки без моделей."""
    вихід = Path(sys.argv[1]).resolve()
    вихід.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        from виконання.е3_база import встановити
        встановити(sys.argv[2], МОДУЛІ + ('реєстр_сила',))
    покриття, мітка, кількість = collections.Counter(), [''], [0]
    with gzip.open(вихід / 'знахідки.jsonl.gz', 'wt', encoding='utf-8') as записи:
        for ім in МОДУЛІ:
            м = importlib.import_module(ім)
            def обгортка(*а, _ф=м._зн, _ім=ім, **к):
                з = _ф(*а, **к)
                функція = sys._getframe(1).f_code.co_name
                ключ = (_ім, функція, з['правило'])
                покриття[' · '.join(ключ)] += 1
                записи.write(json.dumps([мітка[0], *ключ, з], ensure_ascii=False) + '\n')
                кількість[0] += 1
                return з
            м._зн = обгортка
        провали = []
        if '--край' in sys.argv:
            мітка[0] = 'acc_вага_краю.py'
            runpy.run_path(str(ДЖЕРЕЛА / 'проби/acc_вага_краю.py'), run_name='__main__')
        elif '--батарея' in sys.argv:
            шляхи = [ДЖЕРЕЛА / ім for ім in ('стенд_знімок.py', 'тест_живого_шляху.py', 'тест_протоколу.py',
                                              'прилади/розділи_гейтів.py', 'audit_contracts.py')]
            шляхи += sorted(ш for п in ('acc_', 'sho_', 'tsina_') for ш in (ДЖЕРЕЛА / 'проби').glob(п + '*.py'))
            for шлях in шляхи:
                if шлях.name == 'acc_вага_краю.py':
                    continue  # записується окремо режимом --край
                if шлях.name == 'acc_вага_категорії.py' and len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
                    continue  # новий режим відсутній у базі
                мітка[0] = шлях.name
                вих, пом, арг = sys.stdout, sys.stderr, sys.argv
                os.chdir(ДЖЕРЕЛА)
                код = 0
                with (вихід / (шлях.stem + '.log')).open('w', encoding='utf-8') as лог:
                    sys.stdout = sys.stderr = лог
                    sys.argv = [str(шлях)] + (['--дим'] if шлях.name == 'стенд_знімок.py' else [])
                    try:
                        runpy.run_path(str(шлях), run_name='__main__')
                    except SystemExit as п:
                        код = п.code or 0
                    except Exception:
                        код = 1
                        traceback.print_exc()
                    finally:
                        sys.stdout, sys.stderr, sys.argv = вих, пом, арг
                if код:
                    провали.append([шлях.name, код])
                print(шлях.name, 'код', код, flush=True)
        else:
            import feed
            каталог = feed.база_прогону(feed.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог']
            print('повний каталог:', len(каталог), flush=True)
            for назва, ф, а, к in входи(каталог):
                мітка[0] = назва
                ф(*а, **к)
    (вихід / 'підсумок.json').write_text(json.dumps(dict(знахідок=кількість[0], покриття=покриття,
                                                       провали=провали), ensure_ascii=False, indent=2), encoding='utf-8')
    print('знахідок:', кількість[0], 'провали:', провали, flush=True)
    return bool(провали)


if __name__ == '__main__':
    sys.exit(main())

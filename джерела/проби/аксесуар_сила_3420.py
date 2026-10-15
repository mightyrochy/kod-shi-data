# -*- coding: utf-8 -*-
"""K-ACC-01, крок (2) #795: 40 каталожних пар ДО/ПІСЛЯ, сила/невідомо/опора/витрата; поля джерела незмінні.
Запуск з джерела/: python3 проби/аксесуар_сила_3420.py <JSON каталогу з bridge.каталог_останнього_пакета()> [база]."""
import collections, hashlib, json, pathlib, subprocess, sys, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import аксесуари_структура as А, колір_річ as К, колір_відношення as В

def головна():
    """Друкує той самий K-ACC-01 над незміненими реальними речами, без моделі й мережі."""
    кат = json.loads(pathlib.Path(sys.argv[1]).read_text()); база = sys.argv[2] if len(sys.argv) > 2 else '531ce082f573d225d444952207930095d2e260fc'
    до = types.ModuleType('аксесуари_до'); exec(subprocess.check_output(['git', 'show', база + ':джерела/аксесуари_структура.py']), до.__dict__)
    відбиток = lambda: hashlib.sha256(json.dumps(кат, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    поч = відбиток(); сл = lambda р: р.get('слот') in А.СЛОТИ_АКСЕСУАРІВ
    акс = [р for р in кат if сл(р) and К.гучність_меж(р) == 'так']; гучні = [р for р in кат if not сл(р) and К.гучність_меж(р) == 'так']
    пари = [(а, б, В.сила(К.запис_кольору(а), К.запис_кольору(б), 'same_hue', певність=False)) for а in акс for б in гучні]
    взяті, рядки = set(), []
    for ціль in [i / 27 for i in range(28)]:
        а, б, с = min((п for п in пари if (п[0]['id'], п[1]['id']) not in взяті), key=lambda п: abs(п[2][0] - ціль))
        взяті.add((а['id'], б['id'])); рядки.append((а, б, с))
    for стан in ('можливо', 'ні'):
        решта = [р for р in кат if not сл(р) and К.гучність_меж(р) == стан]
        for а, б in zip(акс[:6], решта[:6]): рядки.append((а, б, В.сила(К.запис_кольору(а), К.запис_кольору(б), 'same_hue', певність=False)))
    л = collections.Counter()
    for а, б, с in рядки:
        звіти = []
        for мод in (до, А):
            зн = мод.аксесуар_як_структура([а, б])
            звіти.append([dict(стан='опора' if з.get('полярність') == 'опора' else 'невідомо' if з.get('сила') == 'питання' else 'витрата', вага=з.get('сила_нп'), заяви=з.get('заяви')) for з in зн])
        л['зміни_ваги'] += [з.get('вага') for з in звіти[0]] != [з.get('вага') for з in звіти[1]]
        л['зміни_стану'] += [з.get('стан') for з in звіти[0]] != [з.get('стан') for з in звіти[1]]
        print(json.dumps(dict(id=[а['id'], б['id']], гучність=[К.гучність_меж(а), К.гучність_меж(б)], сила=с, вирок=В.вердикт(с), ДО=звіти[0], ПІСЛЯ=звіти[1]), ensure_ascii=False))
    print(json.dumps(dict(пар=len(рядки), **л, source_sha256=поч, source_незмінне=поч == відбиток()), ensure_ascii=False))

if __name__ == '__main__': головна()

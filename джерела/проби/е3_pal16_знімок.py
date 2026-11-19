"""Знімок K-PAL-16 з `композитор_оцінка.оцінити` на повному каталозі; аргументи: корінь дерева, вихід .json.gz.

Межова річ — кожна річ каталогу з кольором (частка вікна 0.02/0.10/0.18), компаньйони — дві речі
каталогу за сталим зсувом, бік людини ±1; суд образу й K-COMP-04 заглушено, щоб лишився K-PAL-16.
Каталог — `$E3_PAL16_CATALOG` (pickle речей `feed.база_прогону`), той самий для ДО і ПІСЛЯ."""
import collections, gzip, json, os, pathlib, pickle, sys
from unittest.mock import patch


def main():
    """Записати вагу після `обмежити_вагу`, опору, учасників і суть кожної знахідки K-PAL-16."""
    дерево = pathlib.Path(sys.argv[1]).resolve() / 'джерела'
    sys.path.insert(0, str(дерево)); os.chdir(дерево)
    import композитор_оцінка as О, колір_річ as К
    from реєстр_сила import опора
    assert pathlib.Path(О.__file__).resolve().parent == дерево, О.__file__
    with open(os.environ['E3_PAL16_CATALOG'], 'rb') as ф:
        речі = [р for р in pickle.load(ф) if К.межі_кольору(р) is not None]
    речі.sort(key=lambda р: р['id']); н, вих, лік = len(речі), [], collections.Counter()
    with patch.object(О._ПЕР, 'перевірити_образ', return_value={}), \
         patch.object(О.КО, 'інтенсивність', return_value=[]):
        for і, р in enumerate(речі):
            комп = [речі[(і + 7) % н], речі[(і + 131) % н]]
            for ч in (0.02, 0.10, 0.18):
                for бік in (1.0, -1.0):
                    with patch.object(О._PL, 'осі', return_value=dict(позиція=dict(hue=бік))):
                        _, сума, зн, _ = О.оцінити({}, [dict(р, _частка_вікна=ч)] + комп, {}, [], [])
                    for з in [з for з in зн if з.get('правило') == 'K-PAL-16']:
                        вих.append(['%s|%s|%s' % (р['id'], ч, бік), з.get('суть'), з.get('речі'), з.get('сила'),
                                    з.get('блокує'), з.get('сила_нп'), bool(з.get('під_підлогою')), опора(з),
                                    sorted(json.dumps(у, ensure_ascii=False, sort_keys=True)
                                           for у in (з.get('учасники') or []) if isinstance(у, dict)),
                                    [з_.get('code') for з_ in з.get('заяви') or []], з.get('де_ламається'), сума])
                        лік['опора' if опора(з) else 'під підлогою' if з.get('під_підлогою') else 'зауваження'] += 1
    with gzip.open(sys.argv[2], 'wt', encoding='utf-8') as ф: json.dump(вих, ф, ensure_ascii=False)
    print('входів', н * 6, 'знахідок', len(вих), dict(лік))


if __name__ == '__main__':
    main()

"""Звірка «файл · пункт · функція» двох виводів приладу кореня для чотирьох аксесуарних файлів.
Аргументи: вивід ДО, вивід ПІСЛЯ, коміт ДО. Чотири файли — 0, решта — без змін, нових — 0."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from е3_місця import місця

ФАЙЛИ = {'джерела/аксесуари_%s.py' % ф for ф in ('носіння', 'суд', 'ціна', 'край')}


def main():
    """Порівняти мультимножини й надрукувати знятий склад."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    нові, знято = після - до, до - після
    свої_до = sum(v for k, v in до.items() if k[0] in ФАЙЛИ)
    свої_після = sum(v for k, v in після.items() if k[0] in ФАЙЛИ)
    print('місць', sum(до.values()), '→', sum(після.values()), '; чотири файли', свої_до, '→', свої_після,
          '; нових', sum(нові.values()))
    for (файл, пункт, функція), к in sorted(знято.items()):
        print('  знято', файл, пункт, функція, к)
    assert not нові and свої_після == 0 and all(k[0] in ФАЙЛИ for k in знято), (нові, знято)


if __name__ == '__main__':
    main()

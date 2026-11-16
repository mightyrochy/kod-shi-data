"""Звірка мультимножин «файл · пункт · функція» приладу кореня для частини `верхнє_суд` / `верхнє_догляд`.

Аргументи: вивід приладу ДО, вивід ПІСЛЯ, коміт ДО (функції ДО — з його дерева)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from е3_місця import місця

ФАЙЛИ = ('джерела/верхнє_суд.py', 'джерела/верхнє_догляд.py')


def main():
    """Ці два файли — 0, нових місць 0, решта без змін."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    нові, зняті = після - до, до - після
    свої = lambda м: sum(v for k, v in м.items() if k[0] in ФАЙЛИ)
    print('місць', sum(до.values()), '→', sum(після.values()), '· ці файли', свої(до), '→', свої(після),
          '· нових', sum(нові.values()), '· знято поза файлами', sum(v for k, v in зняті.items() if k[0] not in ФАЙЛИ))
    assert свої(після) == 0 and not нові and all(k[0] in ФАЙЛИ for k in зняті)


if __name__ == '__main__':
    main()

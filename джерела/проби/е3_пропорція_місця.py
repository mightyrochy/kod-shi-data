"""Звірка «файл · пункт · функція» з двох виводів приладу кореня для кроку `верхнє_пропорція`."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from е3_місця import місця
ФАЙЛ = 'джерела/верхнє_пропорція.py'


def main():
    """Аргументи: вивід ДО, вивід ПІСЛЯ, коміт ДО. Файл кроку 7 → 0, решта без змін, нових 0."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    файл = lambda м: sum(в for к, в in м.items() if к[0] == ФАЙЛ)
    решта = lambda м: {к: в for к, в in м.items() if к[0] != ФАЙЛ}
    нові = після - до
    print('місць', sum(до.values()), '→', sum(після.values()), '·', ФАЙЛ, файл(до), '→', файл(після),
          '· нових', sum(нові.values()), '· решта тотожна', решта(до) == решта(після))
    assert файл(після) == 0 and not нові and решта(до) == решта(після)


if __name__ == '__main__':
    main()

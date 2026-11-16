"""Звірка місць приладу кореня ДО → ПІСЛЯ для частини принтів; аргументи: вивід ДО, вивід ПІСЛЯ, коміт ДО."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from е3_місця import місця

ФАЙЛИ = ('джерела/колір_принти.py', 'джерела/палітра_принт.py')


def main():
    """Ці два файли — 0, нових місць 0, решта мультимножини «файл · пункт · функція» без змін."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    частина = sum(v for k, v in до.items() if k[0] in ФАЙЛИ)
    решта_до = {k: v for k, v in до.items() if k[0] not in ФАЙЛИ}
    print('місць', sum(до.values()), '→', sum(після.values()), '; принти', частина, '→',
          sum(v for k, v in після.items() if k[0] in ФАЙЛИ), '; нових', sum((після - до).values()))
    assert not any(k[0] in ФАЙЛИ for k in після) and not (після - до) and dict(після) == решта_до


if __name__ == '__main__':
    main()

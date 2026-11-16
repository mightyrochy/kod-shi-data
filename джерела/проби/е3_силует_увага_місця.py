"""Звірка «файл · пункт · функція» приладу кореня ДО → ПІСЛЯ для частини силуету й уваги.
Аргументи: вивід приладу ДО, вивід ПІСЛЯ, коміт ДО (з кореня репозиторію)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from е3_місця import місця

ФАЙЛИ = ('джерела/суд_силует.py', 'джерела/регістр_уваги.py')


def main():
    """Нових місць нема, у двох файлах частини — 0, решта мультимножини без змін."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    частина = lambda м: sum(v for k, v in м.items() if k[0] in ФАЙЛИ)
    решта = lambda м: {k: v for k, v in м.items() if k[0] not in ФАЙЛИ}
    print('місць', sum(до.values()), '→', sum(після.values()), '; частина', частина(до), '→', частина(після),
          '; нових', sum((після - до).values()))
    for k in sorted(до - після):
        print('знято', ' · '.join(k), до[k] - після[k])
    assert not (після - до) and частина(після) == 0 and решта(до) == решта(після)


if __name__ == '__main__':
    main()

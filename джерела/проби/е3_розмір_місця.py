"""Звірка мультимножин «файл · пункт · функція» приладу кореня для кроку `аксесуари_розмір.py`."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from е3_місця import місця


def main():
    """Аргументи: вивід приладу ДО, вивід ПІСЛЯ, коміт ДО; нових місць 0, файлу 0, решта без змін."""
    до = місця(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'), sys.argv[3])
    після = місця(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    файл = 'джерела/аксесуари_розмір.py'
    зняті = до - після
    print('місць', sum(до.values()), '→', sum(після.values()), '; нових', sum((після - до).values()),
          '; аксесуари_розмір', sum(v for k, v in до.items() if k[0] == файл), '→',
          sum(v for k, v in після.items() if k[0] == файл), '; знято поза файлом',
          sum(v for k, v in зняті.items() if k[0] != файл))
    assert not після - до and all(k[0] == файл for k in зняті) and not any(k[0] == файл for k in після)


if __name__ == '__main__':
    main()

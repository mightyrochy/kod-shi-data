"""Діагностика читання таблиці незміненим приладом; його файли й результат не підміняються."""


def main():
    """Виконати перевірку або запис стану лише при прямому запуску."""
    from pathlib import Path
    import sys
    РЕПО = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(РЕПО / 'джерела/прилади'))
    import корінь_річ_колір_межі as П
    print('subprocess.run:', П.subprocess.run.__module__, П.subprocess.run.__code__.co_filename, flush=True)
    таблиця = П.таблиця_г2(str(РЕПО))
    print('Полів таблиці:', len(таблиця), flush=True)


if __name__ == '__main__':
    main()

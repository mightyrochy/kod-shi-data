"""Показати нові місця приладу промптів без зсувів номерів рядків."""


def main():
    """Виконати перевірку або запис стану лише при прямому запуску."""
    from pathlib import Path
    import re
    ТЕКА = Path(__file__).resolve().parent
    def рядки(назва):
        вих = {}
        байти = (ТЕКА / назва).read_bytes()
        for рядок in байти.decode('utf-16' if байти.startswith(b'\xff\xfe') else 'utf-8-sig').splitlines():
            if ' · пункт ' in рядок:
                ключ = re.sub(r':\d+', ':N', рядок)
                вих[ключ] = рядок
        return вих
    до, після = рядки('промпти-до.txt'), рядки('промпти-після.txt')
    print('НОВІ:')
    for к in sorted(після.keys() - до.keys()):
        print(після[к])
    print('ЗНЯТІ:')
    for к in sorted(до.keys() - після.keys()):
        print(до[к])


if __name__ == '__main__':
    main()

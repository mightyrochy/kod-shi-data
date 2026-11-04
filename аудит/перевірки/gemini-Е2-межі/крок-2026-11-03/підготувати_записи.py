"""Викласти відсутні записи перших ходів для е2_нагода_зустріч_повтор без нових записів."""


def main():
    """Виконати перевірку або запис стану лише при прямому запуску."""
    from pathlib import Path
    import re
    import subprocess

    РЕПО = Path(__file__).resolve().parents[4]
    файли = subprocess.check_output(['git', 'ls-files', '-z'], cwd=РЕПО).decode('utf-8').split('\0')
    потрібні = [ф for ф in файли if re.search(r'/VIDPOVIDI/seed[^/]*_01_мовний_шар_хід_розмови\.txt$', ф)]
    відсутні = [ф for ф in потрібні if not (РЕПО / ф).is_file()]
    if відсутні:
        subprocess.run(['git', 'sparse-checkout', 'add', *('/' + ф for ф in відсутні)], cwd=РЕПО, check=True)
    assert all((РЕПО / ф).is_file() for ф in потрібні)
    print('Записів перших ходів:', len(потрібні), '· додано з наявного git:', len(відсутні))


if __name__ == '__main__':
    main()

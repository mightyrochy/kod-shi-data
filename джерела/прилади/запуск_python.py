"""Спільний транспорт дочірнього Python: UTF-8 на обох кінцях труби."""
import os
import subprocess


def запустити_python(команда, *, потрібен_вивід=False, **параметри):
    """Запускає Python з явним UTF-8; повертає CompletedProcess або діагноз із кодом і stderr.

    Читаємо байти до завершення процесу й лише тоді декодуємо: помилка декодера
    не губиться в потоці subprocess і не перетворює stdout на None.
    Порожній stdout дозволений для проб, які звітують лише кодом виходу.
    """
    команда = list(команда)
    команда[1:1] = ['-X', 'utf8']
    передане = параметри.pop('env', None)
    середовище = dict(os.environ if передане is None else передане)
    середовище['PYTHONIOENCODING'] = 'utf-8'
    середовище['PYTHONUTF8'] = '1'
    текст = any([параметри.pop('text', False), параметри.pop('universal_newlines', False),
                 параметри.pop('encoding', None) is not None, параметри.pop('errors', None) is not None])
    перевірити = параметри.pop('check', False)
    if isinstance(параметри.get('input'), str):
        параметри['input'] = параметри['input'].encode('utf-8')
    вихід = subprocess.run(команда, env=середовище, check=False, **параметри)
    причина = (вихід.stderr or b'').decode('utf-8', 'replace').strip()
    if (перевірити or потрібен_вивід) and (вихід.returncode or потрібен_вивід and not (вихід.stdout or b'').strip()):
        raise subprocess.SubprocessError(
            f'Python: код виходу {вихід.returncode}; '
            f'stdout: {"порожній" if not вихід.stdout else "є"}; stderr: {причина or "—"}')
    if текст:
        try:
            for поле in ('stdout', 'stderr'):
                дані = getattr(вихід, поле)
                if дані is not None:
                    setattr(вихід, поле, дані.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n'))
        except UnicodeDecodeError as помилка:
            raise subprocess.SubprocessError(
                f'Python: код виходу {вихід.returncode}; не UTF-8: {помилка}; stderr: {причина or "—"}') from помилка
    return вихід

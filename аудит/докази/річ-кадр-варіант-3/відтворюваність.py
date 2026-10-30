"""Порівнює побайтовий вивід приладу й проб на доступних Python 3.11–3.13."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

КОРІНЬ = Path(__file__).resolve().parents[3]
ДОКАЗИ = Path(__file__).parent
ТМП = КОРІНЬ.parent / 'tmp'


def main():
    """Виконує кожну версію на передньому плані й зберігає хеші та підсумки."""
    версії = [ТМП / 'python311/python.exe', Path(sys.executable), ТМП / 'python313/python.exe']
    режими = [('кандидати', 'джерела/прилади/корінь_річ_кадр_варіант.py', ['--json']),
              ('маршрути', 'джерела/прилади/корінь_річ_кадр_варіант.py', ['--маршрути']),
              ('проби', 'аудит/докази/річ-кадр-варіант-3/проби_маршруту.py', [])]
    звіт = []
    for режим, скрипт, арг in режими:
        for рушій in версії:
            if not рушій.is_file():
                звіт.append(dict(режим=режим, рушій=str(рушій), стан='нема рушія'))
                continue
            версія = subprocess.check_output([str(рушій), '--version'], text=True).strip()
            код = ('import runpy,sys;sys.path.insert(0,"джерела/прилади");'
                   'sys.argv=' + repr([скрипт] + арг) + ';runpy.run_path(' + repr(скрипт) + ',run_name="__main__")')
            початок = time.monotonic()
            вихід = subprocess.run([str(рушій), '-X', 'utf8', '-c', код], cwd=КОРІНЬ, capture_output=True)
            assert вихід.returncode == 0, вихід.stderr.decode('utf-8', errors='replace')
            дані = json.loads(вихід.stdout)
            хеш = hashlib.sha256(вихід.stdout).hexdigest()
            (ТМП / (режим + '-' + версія.replace(' ', '-') + '.json')).write_bytes(вихід.stdout)
            запис = dict(режим=режим, python=версія, команда=[str(рушій), '-X', 'utf8', '-c', код],
                          код=вихід.returncode, секунд=round(time.monotonic() - початок, 1), sha256=хеш)
            if режим == 'кандидати':
                запис['підсумок'] = {к: дані[к] for к in ('файлів', 'кандидатів', 'підсумки')}
                запис['підсумок'].update(нових=len(дані['нові']), розбіжностей=len(дані['розбіжності']),
                                         операторів=len(дані['місця']))
            elif режим == 'маршрути':
                запис['підсумок'] = {к: дані[к] for к in ('файлів', 'вузлів', 'звязаних_викликів', 'підсумки')}
                запис['підсумок']['нерозвязаних_викликів'] = len(дані['нерозвязаних_викликів'])
                if рушій == версії[0]:
                    (ДОКАЗИ / 'маршрути.json').write_bytes(вихід.stdout)
            elif рушій == версії[0]:
                (ДОКАЗИ / 'проби_маршруту.json').write_bytes(вихід.stdout)
            звіт.append(запис)
            print(режим, версія, хеш, запис['секунд'], flush=True)
            (ДОКАЗИ / 'відтворюваність.json').write_text(
                json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        хеші = {з['sha256'] for з in звіт if з['режим'] == режим and 'sha256' in з}
        assert len(хеші) == 1, (режим, хеші)


if __name__ == '__main__':
    main()

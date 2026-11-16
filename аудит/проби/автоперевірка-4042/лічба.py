"""Відтворює ДО/ПІСЛЯ приладами бази й голови #4042 на тотожному коді продукту; аргумент — дерево голови."""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile

def main():
    """Друкує факти незалежної перевірки на переданому дереві голови."""
    дерево = pathlib.Path(sys.argv[1]).resolve()
    очікувана = '29810c7fa728848c3ad10ca45aef568f951cef8e'
    голова = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=дерево).decode().strip()
    assert голова == очікувана, (голова, очікувана)
    шлях = 'джерела/прилади/корінь_е2_смуга_погоди.py'
    зміни = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD^', 'HEAD', '--', 'джерела'], cwd=дерево).decode().splitlines()
    assert len(зміни) == 1
    sys.path.insert(0, str(дерево / 'джерела' / 'прилади'))
    множини = {}
    with tempfile.TemporaryDirectory(prefix='перевірка_4042_') as тека:
        for назва, версія in [('ДО', 'HEAD^'), ('ПІСЛЯ', 'HEAD')]:
            файл = pathlib.Path(тека) / ('прилад_' + версія.replace('^', '_база') + '.py')
            файл.write_bytes(subprocess.check_output(['git', 'show', версія + ':' + шлях], cwd=дерево))
            опис = importlib.util.spec_from_file_location('прилад_' + назва, файл)
            прилад = importlib.util.module_from_spec(опис)
            опис.loader.exec_module(прилад)
            місця = прилад.лічити(str(дерево))[0]
            множини[назва] = set(місця)
            print(назва + ' місць: ' + str(len(місця)), flush=True)
            for ім, рядок in sorted(місця):
                print(f'  {ім}:{рядок}', flush=True)
    print('прибрано:', sorted(множини['ДО'] - множини['ПІСЛЯ']))
    print('додано:', sorted(множини['ПІСЛЯ'] - множини['ДО']))


if __name__ == "__main__":
    main()

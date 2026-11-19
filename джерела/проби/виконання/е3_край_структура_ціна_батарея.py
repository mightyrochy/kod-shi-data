"""Батарея та ваги трьох аксесуарних модулів: префікс [коміт ДО] [--сімя]."""
import functools
import gzip
import json
import os
import pathlib
import runpy
import subprocess
import sys
import traceback

МОДУЛІ = ('аксесуари_край', 'аксесуари_структура', 'аксесуари_ціна')


def main():
    """Записати кожну емісію й завершити всі перевірки навіть після провалу однієї."""
    корінь = pathlib.Path(__file__).resolve().parents[3]
    джерела = корінь / 'джерела'
    sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    лише_сімя = '--сімя' in sys.argv
    if лише_сімя:
        sys.argv.remove('--сімя')
    префікс = sys.argv[1]
    if len(sys.argv) > 2:
        from виконання.е3_база import встановити
        встановити(sys.argv[2], МОДУЛІ)
    import importlib
    записи, результати, мітка = [], [], ['']

    def обгорнути(ф, модуль):
        @functools.wraps(ф)
        def виклик(*args, **kwargs):
            з = ф(*args, **kwargs)
            записи.append([мітка[0], модуль, з])
            return з
        return виклик

    for ім in МОДУЛІ:
        модуль = importlib.import_module(ім)
        модуль._зн = обгорнути(модуль._зн, ім)
    перевірки = [(джерела / ім, арг) for ім, арг in (
        ('стенд_знімок.py', ['--дим']), ('тест_живого_шляху.py', []),
        ('тест_протоколу.py', []), ('прилади/розділи_гейтів.py', []), ('audit_contracts.py', []))]
    if лише_сімя:
        перевірки = []
    перевірки += [(ш, []) for ш in sorted({ш for п in ('acc_', 'cra_', 'sho_', 'tsina_')
                     for ш in (джерела / 'проби').glob(п + '*.py')})]
    with open(префікс + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for шлях, арг in перевірки:
            мітка[0] = шлях.name
            sys.argv = [str(шлях), *арг]
            вих, пом, шляхи = sys.stdout, sys.stderr, list(sys.path)
            os.chdir(джерела)
            sys.path.insert(0, str(шлях.parent))
            sys.stdout = sys.stderr = журнал
            код = 0
            try:
                runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as з:
                код = з.code or 0
            except BaseException:
                код = 1
                traceback.print_exc()
            finally:
                sys.stdout, sys.stderr, sys.path[:] = вих, пом, шляхи
            результати.append([шлях.name, код])
            print('КІНЕЦЬ', шлях.name, 'код', код, flush=True)
        код = subprocess.run(['node', 'тест_показу.js'], cwd=джерела,
                            env=dict(os.environ, NODE_PATH='node_modules'), stdout=журнал, stderr=журнал).returncode
        результати.append(['тест_показу.js', код])
    with gzip.open(префікс + '.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, результати=результати), ф, ensure_ascii=False)
    print('ГОТОВО', len(записи), 'знахідок; провали', [р for р in результати if р[1]], flush=True)
    return int(any(р[1] for р in результати))


if __name__ == '__main__':
    raise SystemExit(main())

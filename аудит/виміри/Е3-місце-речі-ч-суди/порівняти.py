"""Повторює одну пробу читачів на функціях бази та робочого дерева."""
import ast, contextlib, os, pathlib, runpy, subprocess, sys


def main():
    """Порівнює старі функції з поточними на однакових залежностях і входах."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    os.chdir(корінь)
    sys.path.insert(0, str(корінь / 'джерела'))
    import суд_образу, суд_огляд, суд_від_моделі, pipeline
    база = '6de6f0b8b8a6166e77c4b99db5f9d327a3acb3ac'
    for модуль, ім in ((суд_огляд, 'перевірка_сегментації'), (суд_від_моделі, 'кольори_образу')):
        текст = subprocess.check_output(['git', 'show', база + ':джерела/' + модуль.__name__ + '.py']).decode('utf-8')
        вузол = next(n for n in ast.parse(текст).body if isinstance(n, ast.FunctionDef) and n.name == ім)
        exec(compile(ast.Module(body=[вузол], type_ignores=[]), '<ДО>', 'exec'), модуль.__dict__)
    суд_образу.перевірка_сегментації = суд_огляд.перевірка_сегментації
    pipeline._кольори_образу = суд_від_моделі.кольори_образу
    проба = 'джерела/проби/е3_місце_суди.py'
    with (тека / 'проба-ДО.txt').open('w', encoding='utf-8') as ф, contextlib.redirect_stdout(ф):
        до = runpy.run_path(проба)['main']()
    with (тека / 'проба-ПІСЛЯ.txt').open('wb') as ф:
        після = subprocess.run([sys.executable, '-X', 'utf8', проба], stdout=ф, stderr=subprocess.STDOUT).returncode
    for назва in ('ДО', 'ПІСЛЯ'):
        print(назва, (тека / ('проба-' + назва + '.txt')).read_text(encoding='utf-8').splitlines()[-1])
    return 0 if до and після == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

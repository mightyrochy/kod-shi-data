"""Виконує сім'ю палітри й сили до кінця одним процесом.

Запуск із `джерела`: python ../аудит/проби/е3_сила_правила/схеми_сімя.py.
Той самий спосіб запуску, що використовувався для кроку; кожна невдала проба зберігається у звіті.
"""
import contextlib, io, json, os, pathlib, runpy, sys, traceback


def головна():
    """Записує результати всіх проб, повертає помилку за наявності провалу."""
    src = pathlib.Path.cwd()
    sys.path[:0] = [str(src), str(src / 'проби')]
    files = sorted({*src.glob('проби/pal_*.py'), *src.glob('проби/сила_*.py'),
        *[src / 'проби' / p for p in ['схема_960_гейт.py', 'схема_назви_сімей.py', 'колір_тип_213_великі.py',
            'kcol03_вставка_прикраси.py', 'палітра5_невідомий_акцент.py', 'прикр2_золото_слово.py', 'фокус3_зняття_кольору.py']]}
        - {src / 'проби/pal_вердикт.py', src / 'проби/pal_вимір.py'})
    results = []
    for p in files:
        os.chdir(src); sys.argv = [str(p)]
        if p.name == 'фокус3_зняття_кольору.py':
            sys.argv.append(str(src.parent / 'аудит/перевірки/fokus_2/ПІСЛЯ'))
        s = io.StringIO(); code = 0
        with contextlib.redirect_stdout(s), contextlib.redirect_stderr(s):
            try:
                runpy.run_path(str(p), run_name='__main__')
            except SystemExit as e:
                code = e.code or 0
            except BaseException:
                code = 1; traceback.print_exc()
        results.append(dict(файл=p.name, код=code, хвіст=s.getvalue().splitlines()[-12:]))
        print(p.name, code, flush=True)
    out = src.parent / 'аудит/проби/е3_сила_правила/крок1_схеми_сімя.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ФАКТ · проб', len(results), 'пройшло', sum(r['код'] == 0 for r in results))
    return any(r['код'] != 0 for r in results)


if __name__ == '__main__':
    sys.exit(головна())

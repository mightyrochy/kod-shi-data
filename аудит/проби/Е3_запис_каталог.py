"""Повторює формати речі на всьому каталозі; модель і платні API не викликаються."""
import ast, contextlib, copy, gzip, os, pickle, runpy, subprocess, sys
from pathlib import Path


def головна():
    """Повторює читачів початкового чи поточного коду на одному каталозі."""
    # Запуск: python аудит/проби/Е3_запис_каталог.py [--до <SHA>]
    os.chdir(Path(__file__).resolve().parents[2] / 'джерела')
    sys.path.insert(0, str(Path.cwd()))
    import feed as Ф, pipeline as П, пакет_моделі as М, дріт_моделі as Д, каталог_коди as К
    тека = Path(os.environ['TEMP'])
    кеш = тека / 'е3-каталог.pickle.gz'
    if not кеш.exists():
        with (тека / 'е3-каталог-побудова.log').open('w', encoding='utf-8') as файл, contextlib.redirect_stdout(файл):
            каталог = Ф._прочитати_каталог(Ф.каталог_на_диску(), ліміт_фото=0, кеш=str(тека / 'е3-кольори.json'))['каталог']
        with gzip.open(кеш, 'wb') as файл: pickle.dump(каталог, файл)
    with gzip.open(кеш, 'rb') as файл: каталог = pickle.load(файл)
    проба = runpy.run_path('проби/запис_одна_величина.py')
    код = ast.parse(Path('проби/запис_одна_величина.py').read_text(encoding='utf-8'))
    фікстури = [п for п in код.body[-1].body if isinstance(п, ast.Assign)]
    простір = {}
    exec(compile(ast.Module(body=фікстури[:2], type_ignores=[]), '<випадки>', 'exec'), простір)
    if '--до' in sys.argv:
        for модуль, ім in ((К, 'запис_для_моделі'), (М, 'річ_пулу'), (Д, 'річ')):
            до = subprocess.check_output(['git', 'show', sys.argv[sys.argv.index('--до') + 1] + ':джерела/' + модуль.__name__ + '.py'], encoding='utf-8')
            вузол = next(п for п in ast.parse(до).body if isinstance(п, ast.FunctionDef) and п.name == ім)
            exec(compile(ast.Module(body=[вузол], type_ignores=[]), '<ДО>', 'exec'), модуль.__dict__)
        П.річ_пулу = М.річ_пулу
    print('Джерело: каталог feed.каталог_на_диску(), ліміт_фото=0; однакові записи для ДО/ПІСЛЯ', flush=True)
    print('Контрольні випадки:', flush=True)
    проба['перевірити'](простір['речі'])
    суперечність = простір['розбір']
    записи = [dict(r, розбір=dict(r.get('розбір') or {}, **суперечність)) for r in каталог]
    print('Увесь каталог із суперечливим розбором:', flush=True)
    розбіжності = проба['перевірити'](записи)
    print('Покриття: тип', sum(bool(r.get('тип')) for r in каталог), 'матеріалів', sum(bool(r.get('погодні_матеріали')) for r in каталог), 'крою', sum(bool(r.get('крій')) for r in каталог), flush=True)
    return bool(розбіжності) if '--до' not in sys.argv else 0


if __name__ == "__main__":
    sys.exit(головна())

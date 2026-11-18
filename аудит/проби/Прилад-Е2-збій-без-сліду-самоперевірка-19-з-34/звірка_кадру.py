"""Звірити повним обходом вплив правки Е2 на прилад кадру варіанта.

Запуск із кореня репозиторію. В обох проходах те саме дерево; другий підставляє
AST приладу Е2 із заданого main, не змінюючи файлів робочої копії.
"""
import ast
import importlib
import json
import pathlib
import subprocess
import sys


def головна():
    """Зберегти обидва повні переліки місць поруч зі скриптом доказу."""
    sys.path.insert(0, 'джерела/прилади')
    прилад = importlib.import_module('корінь_річ_кадр_варіант')
    змінений = pathlib.Path('джерела/прилади/корінь_е2_збій_без_сліду.py').resolve()
    відносний = змінений.relative_to(pathlib.Path.cwd()).as_posix()
    давній_текст = subprocess.check_output(
        ['git', 'show', '3a1edf232e1:' + відносний], encoding='utf8')
    розібрати = прилад.розібрати
    результат = {}
    try:
        for стан in ('голова', 'до'):
            if стан == 'до':
                прилад.розібрати = lambda шлях: (
                    ast.parse(давній_текст) if pathlib.Path(шлях).resolve() == змінений
                    else розібрати(шлях))
            місця = прилад.головна('.')[0]
            результат[стан] = {
                'python': [dict(файл=м.файл, рядок=м.рядок, пункт=м.пункт, чому=м.чому)
                           for м in місця],
                'js': прилад.скан_js('.')[2],
            }
            print(стан, json.dumps(результат[стан], ensure_ascii=False), flush=True)
            pathlib.Path(__file__).with_name('кадр-повний.json').write_text(
                json.dumps(результат, ensure_ascii=False, indent=2), encoding='utf8')
    finally:
        прилад.розібрати = розібрати


if __name__ == '__main__':
    головна()

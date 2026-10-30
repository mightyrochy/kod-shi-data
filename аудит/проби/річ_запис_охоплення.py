"""Звіряє незалежний грубий обхід AST зі списками приладу; аргумент — його JSON."""
import ast
import json
from pathlib import Path
import re
import sys
import warnings


def головна():
    """Шукає читання чотирьох текстових полів з регексом за будь-яким іменем отримувача."""
    warnings.simplefilter('ignore', SyntaxWarning)
    дані = json.loads(Path(sys.argv[1]).read_text(encoding='utf8'))
    результати = []
    for тека in ('джерела', 'zhnyvarka'):
        for файл in sorted(Path(тека).rglob('*.py')):
            if any(п in ('проби', 'прилади', 'аудит', 'показ', 'node_modules', 'розвідка', 'фікстури') for п in файл.parts) or re.match(r'тест|gate_|audit_|стенд|батарея_|measure_|pair_test|мутанти|replay|проба', файл.name):
                continue
            дерево = ast.parse(файл.read_text(encoding='utf-8-sig'))
            регекс = {'re', 'regex'} | {а.asname or а.name for в in ast.walk(дерево) if isinstance(в, ast.Import) for а in в.names if а.name in ('re', 'regex')}
            регекс |= {ц.id for в in ast.walk(дерево) if isinstance(в, ast.Assign) and isinstance(в.value, ast.Call) and isinstance(в.value.func, ast.Attribute) and в.value.func.attr == 'compile' for ц in в.targets if isinstance(ц, ast.Name)}
            for ф in ast.walk(дерево):
                if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                вузли = list(ast.walk(ф))
                ключі = [в.args[0] for в in вузли if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == 'get' and в.args]
                ключі += [в.slice for в in вузли if isinstance(в, ast.Subscript)]
                if not any(isinstance(в, ast.Constant) and в.value in ('назва', 'опис', 'склад', 'категорія') for в in ключі):
                    continue
                if not any(isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and (в.func.attr in ('search', 'match', 'fullmatch', 'findall', 'finditer', 'sub', 'subn') or (в.func.attr == 'split' and isinstance(в.func.value, ast.Name) and в.func.value.id in регекс)) for в in вузли):
                    continue
                збіги = {к: [м for м in дані[к] if м['файл'] == файл.as_posix() and ф.lineno <= м['рядок'] <= ф.end_lineno] for к in ('місця', 'відкинуті')}
                результати.append(dict(функція=f'{файл.as_posix()}:{ф.lineno}:{ф.name}', **збіги))
    print(json.dumps(результати, ensure_ascii=False, indent=1))
    return int(any(not (р['місця'] or р['відкинуті']) for р in результати))


if __name__ == '__main__':
    sys.exit(головна())

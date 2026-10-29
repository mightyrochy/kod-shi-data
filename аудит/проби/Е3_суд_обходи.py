"""Друкує підміни відсутнього числового входу й власників погодних рішень."""
import ast
import json
import subprocess
import sys
from pathlib import Path


ПОЛЯ = {"площа", "near", "C", "a", "b", "блиск", "тепло_особи", "впевненість", "полірування", "chroma"}


def вимір(база=None):
    """Лічить підміни предметних входів; лічильники й суми виходу входами не є."""
    обходи, погода = [], []
    for файл in sorted(Path("джерела").glob("*.py")):
        if not (файл.stem.startswith("суд_") or файл.stem == "правила"):
            continue
        текст = (subprocess.check_output(["git", "show", f"{база}:{файл.as_posix()}"]).decode("utf-8")
                 if база else файл.read_text(encoding="utf-8-sig"))
        дерево = ast.parse(текст)
        for вузол in ast.walk(дерево):
            вираз = None
            if isinstance(вузол, ast.BoolOp) and isinstance(вузол.op, ast.Or):
                if any(isinstance(в, ast.Constant) and type(в.value) in (int, float) for в in вузол.values):
                    вираз = вузол
            elif isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute):
                if вузол.func.attr == "get" and len(вузол.args) > 1:
                    типовий = вузол.args[1]
                    if isinstance(типовий, ast.Constant) and type(типовий.value) in (int, float):
                        вираз = вузол
            if вираз and any(isinstance(в, ast.Constant) and в.value in ПОЛЯ
                             for в in ast.walk(вираз) if isinstance(в, ast.Constant) and isinstance(в.value, str)):
                обходи.append(f"{файл.as_posix()}:{вузол.lineno}: {ast.unparse(вираз)}")
    for ім in ("суд_погода", "аксесуари_погода", "верхнє_погода"):
        файл = Path("джерела", ім + ".py")
        текст = (subprocess.check_output(["git", "show", f"{база}:{файл.as_posix()}"]).decode("utf-8")
                 if база else файл.read_text(encoding="utf-8-sig"))
        дерево = ast.parse(текст)
        if any(isinstance(в, ast.FunctionDef) for в in дерево.body):
            погода.append(ім)
    return dict(типові=len(обходи), місця=обходи, погодні_модулі=погода)


if __name__ == "__main__":
    print(json.dumps(вимір(sys.argv[1] if len(sys.argv) > 1 else None), ensure_ascii=False, indent=2))

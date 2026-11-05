"""Показує числові операції над прямими псевдонімами коду смуги для ручного огляду.

Це допоміжний пошук, не заміна приладу кореня: перетворення через довільний
виклик функції він не простежує. Кожен знайдений виклик перевіряється читанням.
"""
import ast
from pathlib import Path
import re
import subprocess
import sys

КЛЮЧІ = {"смуга_погоди", "weather_band"}
ВИКЛИКИ = {"float", "int", "round", "abs"}
КОРІНЬ = Path(__file__).resolve().parents[4]


def шукати(текст, файл):
    """Збирає прямі псевдоніми та друкує підозрілі числові читання."""
    дерево = ast.parse(текст)
    рядки = текст.splitlines()
    for функція in ast.walk(дерево):
        if not isinstance(функція, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        імена = {а.arg for а in (*функція.args.args, *функція.args.kwonlyargs)} & КЛЮЧІ

        def код(вузол):
            if isinstance(вузол, ast.Name):
                return вузол.id in імена
            if isinstance(вузол, ast.Subscript):
                return isinstance(вузол.slice, ast.Constant) and вузол.slice.value in КЛЮЧІ
            if isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute):
                return вузол.func.attr == "get" and bool(вузол.args) and isinstance(вузол.args[0], ast.Constant) and вузол.args[0].value in КЛЮЧІ
            if isinstance(вузол, ast.IfExp):
                return код(вузол.body) or код(вузол.orelse)
            if isinstance(вузол, ast.BoolOp):
                return any(код(в) for в in вузол.values)
            return False

        вузли = list(ast.walk(функція))
        старі = None
        while старі != імена:
            старі = set(імена)
            for в in вузли:
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and код(в.value):
                    цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                    імена.update(ц.id for ц in цілі if isinstance(ц, ast.Name))
        for в in вузли:
            причина = None
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in ВИКЛИКИ and any(код(а) for а in в.args):
                причина = "числовий виклик"
            if isinstance(в, ast.Compare) and any(isinstance(оп, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for оп in в.ops) and any(код(а) for а in (в.left, *в.comparators)):
                причина = "числове порівняння"
            if isinstance(в, ast.BinOp) and not isinstance(в.op, ast.Mod) and (код(в.left) or код(в.right)):
                причина = "арифметика"
            if isinstance(в, ast.BinOp) and isinstance(в.op, ast.Mod) and isinstance(в.left, ast.Constant) and isinstance(в.left.value, str):
                формати = re.findall(r"%(?!%)[-+ #0]*\d*(?:\.\d+)?[sdifgeEGF]", в.left.value)
                значення = в.right.elts if isinstance(в.right, ast.Tuple) else [в.right]
                if any(ф[-1] != "s" and код(а) for ф, а in zip(формати, значення)):
                    причина = "числовий формат"
            if isinstance(в, ast.FormattedValue) and код(в.value) and в.format_spec:
                причина = "форматування"
            if причина:
                print(f"{файл}:{в.lineno}: {причина}: {рядки[в.lineno-1].strip()}")


if __name__ == "__main__":
    ревізія = sys.argv[1] if len(sys.argv) > 1 else None
    файли = subprocess.check_output(["git", "ls-files", "джерела", "zhnyvarka"], cwd=КОРІНЬ, encoding="utf-8").splitlines()
    кількість = 0
    for файл in файли:
        п = Path(файл)
        if п.suffix != ".py" or set(п.parts) & {"проби", "прилади", "node_modules", "__pycache__"} or re.search(r"^(тест|test|стенд|батарея|gate_|pair_test|проба)|(_test|_тест)\.|\.test\.", п.name, re.I):
            continue
        текст = subprocess.check_output(["git", "show", f"{ревізія}:{файл}"], cwd=КОРІНЬ, encoding="utf-8") if ревізія else (КОРІНЬ / п).read_text(encoding="utf-8-sig")
        шукати(текст, файл)
        кількість += 1
    print("Переглянуто модулів Python:", кількість)

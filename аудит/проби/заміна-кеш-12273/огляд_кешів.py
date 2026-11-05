"""Інвентар повних очищень за розміром у коді продукту; це не гейт кореня."""
import ast
from pathlib import Path


def оглянути():
    """Шукає clear і заміну порожнім словником під умовою len у всіх модулях продукту."""
    джерела = Path(__file__).resolve().parents[3] / 'джерела'
    for p in sorted(джерела.rglob('*.py')):
        if any(x in p.parts for x in ('проби', 'прилади', 'лабораторія', 'node_modules')):
            continue
        if p.name.startswith(('тест_', 'стенд_', 'гейти', 'батарея')):
            continue
        tree = ast.parse(p.read_text(encoding='utf-8-sig'))
        for n in ast.walk(tree):
            if not isinstance(n, (ast.If, ast.While)):
                continue
            if not any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == 'len' for c in ast.walk(n.test)):
                continue
            for b in n.body:
                for c in ast.walk(b):
                    clear = isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == 'clear'
                    порожній = isinstance(c, ast.Assign) and isinstance(c.value, ast.Dict) and not c.value.keys
                    if clear or порожній:
                        print(f'{p.relative_to(джерела)}:{c.lineno}: {ast.unparse(n.test)} → {ast.unparse(c)}')


if __name__ == '__main__':
    оглянути()

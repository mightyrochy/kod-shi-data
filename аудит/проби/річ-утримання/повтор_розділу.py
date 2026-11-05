"""Повторює незмінені перевірки розділу про свідка підтону з основного приладу."""
import ast
import inspect
import json
from pathlib import Path
import sys

К = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела"))
import colorspace
import palette
import bridge

дерево = ast.parse((К / "джерела/прилади/розділи_гейтів.py").read_text("utf8"))
main = next(n for n in дерево.body if isinstance(n, ast.FunctionDef) and n.name == "main")
початок = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Expr)
               and "ПРИДАТНІСТЬ ЗНАКА МАЄ ОДНОГО СВІДКА" in ast.unparse(n))
кінець = next(i for i in range(початок + 1, len(main.body)) if isinstance(main.body[i], ast.Expr)
              and ast.unparse(main.body[i]).startswith("print("))
результати = []
def тест(назва, ок, дані=None):
    """Зберігає результат існуючої звірки та друкує її фактичні дані."""
    результати.append(dict(назва=назва, пройдено=bool(ок), дані=дані))
    print("✓" if ок else "✗", назва, дані, flush=True)
env = dict(sys=sys, _json=json, _insp134=inspect, _cs135=colorspace, _P135=palette, _B134=bridge, тест=тест)
exec(compile(ast.Module(body=main.body[початок:кінець], type_ignores=[]), "розділ_свідка", "exec"), env)
Path(__file__).with_name("розділ-повтор.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf8")
assert результати and all(р["пройдено"] for р in результати)

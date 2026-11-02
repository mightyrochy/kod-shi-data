"""Один запит б1 (як Е2-вікно-3110/запуск.py), але з вікном стилістки W: його бачить і проксі (CTX), і сторінка (MODEL_CTX)."""
import sys, os, importlib.util
from pathlib import Path
КОРІНЬ = Path(os.getcwd())
id_, вікно, вихід = sys.argv[1], sys.argv[2], sys.argv[3]
код = (КОРІНЬ / "аудит/проби/записати_сцену.py").read_text(encoding="utf-8").replace("57344", вікно)
assert код.count(вікно) == 1
м = type(sys)("записати_сцену"); м.__file__ = str(КОРІНЬ / "аудит/проби/записати_сцену.py")
exec(compile(код, м.__file__, "exec"), м.__dict__)
рядок = next(р.split("|") for р in (КОРІНЬ / "аудит/проби/б1_доречність.md").read_text(encoding="utf-8").splitlines() if р.startswith(id_ + "|"))
м.сцена_реєстру = lambda _: {"назва": id_, "сід": 3, "змінні": {"OTSINKA": "0", "MODEL_CTX": вікно,
    "CHAT_TEXT": рядок[2], "ZHINKA": str(КОРІНЬ / "аудит/проби/жінки" / (рядок[1] + ".json")),
    "MODEL": "qwen/qwen3.5-9b", "MODEL_MOVA": "mamaylm-gemma-3-12b-it-v2.0"}}
sys.argv = [sys.argv[0], str(КОРІНЬ), r"C:\Users\Admin\stend-nout\pyodide", вихід, "--сцена", id_]
raise SystemExit(м.виконати())

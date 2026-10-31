"""Один запит б1 через прилад записати_сцену.py: змінні — з рядка run.sh (б1_доречність.md), MODEL_CTX=57344, OTSINKA=0, без FOTO."""
import importlib.util
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[4]
спека = importlib.util.spec_from_file_location("записати_сцену", КОРІНЬ / "аудит/проби/записати_сцену.py")
м = importlib.util.module_from_spec(спека)
спека.loader.exec_module(м)

id_ = sys.argv[1]
рядок = next(р.split("|") for р in (КОРІНЬ / "аудит/проби/б1_доречність.md").read_text(encoding="utf-8").splitlines()
             if р.startswith(id_ + "|"))
м.сцена_реєстру = lambda _: {"назва": id_, "сід": 3, "змінні": {"OTSINKA": "0", "MODEL_CTX": "57344",
    "CHAT_TEXT": рядок[2], "ZHINKA": str(КОРІНЬ / "аудит/проби/жінки" / (рядок[1] + ".json")),
    "MODEL": "qwen/qwen3.5-9b", "MODEL_MOVA": "mamaylm-gemma-3-12b-it-v2.0"}}
sys.argv = [sys.argv[0], str(КОРІНЬ), r"C:\Users\Admin\stend-nout\pyodide", sys.argv[2], "--сцена", id_]
raise SystemExit(м.виконати())

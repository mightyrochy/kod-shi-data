"""ПС-1: новий розбір змінює версію каталогу, зібраний запис зберігає свій знімок."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed
import каталог_коди as коди


def головна():
    """Змінити файл кодів між двома входами й перевірити відбиток та незмінність запису."""
    with tempfile.TemporaryDirectory() as тека, patch.dict(os.environ, ROZBIR_KODY=str(Path(тека) / "розбір.json")):
        шлях = Path(os.environ["ROZBIR_KODY"])
        шлях.write_text(json.dumps({"1": {"item_type": "shirt", "fabric_kind": "woven"}}), encoding="utf-8")
        офер = dict(id="1", назва="Сорочка", категорія="верх", параметри={})
        до = коди.відбиток()
        запис = feed.побудувати_запис_речі(офер)
        шлях.write_text(json.dumps({"1": {"item_type": "dress_generic"}}), encoding="utf-8")
        після = коди.відбиток()
        assert до != після and коди.відбиток() == після
        assert запис["тип"] == "сорочка" and запис["розбір"]["item_type"] == "shirt"
        assert запис["ознаки_зі_слів"]["рід_тканини_слово"] == "полотно"
        assert feed.побудувати_запис_речі(офер)["тип"] == "сукня_без_уточнення"
        print("ПС-1: версія кодів змінює ключі кешів; попередній запис лишається своїм знімком")


if __name__ == "__main__":
    головна()

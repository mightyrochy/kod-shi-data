"""Прицільні відтворення перевірки #2283; реалізацію PR не змінює.

python -X utf8 <цей файл> <дерево PR із приладом>
"""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile

корінь = Path(sys.argv[1]).resolve()
шлях = корінь / "джерела/прилади/корінь_річ_запис_речі.py"
спец = importlib.util.spec_from_file_location("прилад_2283", шлях)
прилад = importlib.util.module_from_spec(спец)
спец.loader.exec_module(прилад)

випадки = {
    "координати": '''def рамка(v):
    return [v.get(k) for k in ("ліво", "верх", "право", "низ")]
''',
    "одне_слово": '''СЛОВНИК = {"платт": "dress_generic"}
def тип_речі(назва):
    return СЛОВНИК.get(назва)
''',
    "латинське_слово": '''import re
def тип_речі(назва):
    if re.search(r"hoodie", назва):
        return "hoodie"
''',
    "JS_група_кодів": '''const група = ["hoodie", "shirt"];
function читач(item) { return група.includes(item.item_type); }
''',
    "поза_блоком": '''def запис(soup):
    return {"опис": soup.get_text(" ")}
''',
    "поза_блоком_псевдонім": '''def запис(doc):
    return {"опис": doc.get_text(" ")}
''',
}

for назва, текст in випадки.items():
    with tempfile.TemporaryDirectory(prefix="перевірка-2283-") as тека:
        дерево = Path(тека)
        джерела = дерево / "джерела"
        джерела.mkdir()
        for ім in ("slots.py", "внутрішня_мова.py"):
            shutil.copy2(корінь / "джерела" / ім, джерела / ім)
        суфікс = ".js" if назва.startswith("JS_") else ".py"
        (джерела / ("читач" + суфікс)).write_text(текст, encoding="utf-8")
        аналіз = прилад.Аналіз(дерево)
        місця, *_ = прилад.скласти(аналіз, дерево)
        print(f"{назва}: місць {len(місця.дані)}, пункти {dict(sorted(місця.пункти().items()))}")
        for (файл, рядок), пункти in sorted(місця.дані.items()):
            for пункт, (чому, _) in sorted(пункти.items()):
                print(f"  {файл}:{рядок} · п.{пункт} · {чому}")

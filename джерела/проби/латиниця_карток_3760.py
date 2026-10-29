#!/usr/bin/env python3
"""Друкує залишки латинки картки на базі та після правки 3760."""
import json
import pathlib
import re
import subprocess
import sys

ДЖ = pathlib.Path(__file__).resolve().parents[1]
БАЗА = "66e29b6534290e438ae814f7f3db1e230cc2c920"
КАРТКА = {"речі": [{"назва": "Кросівки", "назва_крамниці": "Кросівки Nike", "крамниця": "VOVK"}]}
ПРИКЛАДИ = [("піна EVA", КАРТКА, ["EVA"]), ("крем SPF 30", КАРТКА, ["SPF"]),
             ("річ Nike з VOVK", КАРТКА, []), ("колготи 40 den, V-подібний виріз, сумка A4", КАРТКА, []),
             ("колір AABBCC", КАРТКА, []), ("піна EVA", {"речі": [{"назва": "Кросівки EVA"}]}, []),
             ("піна EVA", {"речі": [{"вигадана": True, "назва": "Кросівки EVA"}]}, ["EVA"])]

def прогін(текст):
    код = re.search(r"function словаП\(т\)\{.*?\}\n", текст).group(0)
    код += текст[текст.index("const ЗАКОННА_ЛАТИНКА_П"):текст.index("/* ТЕКСТ ЧАТУ ПРОХОДИТЬ ТОЙ САМИЙ СТОРОЖ")]
    for ім in ("законніКарткиП", "словаКарткиП"):
        код += re.search(r"function " + ім + r"\(.*?\n\}\n", текст, re.S).group(0)
    код += "for (const [т,к] of " + json.dumps(ПРИКЛАДИ, ensure_ascii=False) + ") {"
    код += "const с=словаКарткиП(к); const з=законніКарткиП.length===2?законніКарткиП(к,с):законніКарткиП(с);"
    код += "console.log(JSON.stringify({залишки:латинськіЗалишкиП(т,з),текст:безЗайвоїЛатинкиП(т,з)}));}"
    # Функція зняття не викликає модель; беремо її незміненою з тієї самої сторінки.
    код = re.search(r"function безЗайвоїЛатинкиП\(.*?\n\}\n", текст, re.S).group(0) + код
    вих = subprocess.run(["node", "-e", код], capture_output=True, text=True, check=True)
    return [json.loads(р) for р in вих.stdout.splitlines()]

if __name__ == "__main__":
    до = прогін(subprocess.check_output(["git", "show", БАЗА + ":джерела/показ.html"], cwd=ДЖ, text=True))
    після = прогін((ДЖ / "показ.html").read_text())
    for (т, _, оч), д, п in zip(ПРИКЛАДИ, до, після):
        print(f"{т}: ДО {д} → ПІСЛЯ {п}")
    sys.exit(any(п["залишки"] != оч for (_, _, оч), п in zip(ПРИКЛАДИ, після)))

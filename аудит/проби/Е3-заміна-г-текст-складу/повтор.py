# -*- coding: utf-8 -*-
"""Е3-заміна-з-перевіркою, умова «г», мірило ДО → ПІСЛЯ повтором записаних прогонів: сцени нічних наборів 07.11
(відмови `reason_not_in_list`), 15.11 і 16.11 з пропозицією заміни з фото та с5 «весілля сестри» (живий-як-людина-4).
З кожної — записане рішення коду (рядок `photo_swap_proposed`/`photo_swap_decided` журналу) і записана відповідь опису,
що несла `swap` (VIDPOVIDI; с5 — текст картки з вердиктів). Обидва — у справжній етап фото-заміни показу: ДО —
`показ/збирання_руки.js` з `origin/main`, ПІСЛЯ — з робочого дерева (`повтор.js`). Рядок картки ПІСЛЯ —
`заміна_з_фото.текст_складу` над записаним рішенням. Друкує по сцені й підсумок.
Запуск з кореня: python3 аудит/проби/Е3-заміна-г-текст-складу/повтор.py"""
import os, re, sys, json, subprocess
КОР = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(КОР, "джерела"))
import заміна_з_фото as ЗФ
П = os.path.join(КОР, "аудит", "проби")
ТЕКИ = [os.path.join(н, с) for н in ("Е1-нічний-живий-20261107", "Е1-нічний-живий-20261115", "Е1-нічний-живий-20261116")
        for с in sorted(os.listdir(os.path.join(П, н))) if os.path.isdir(os.path.join(П, н, с))] + ["живий-як-людина-4/с5_весілля_сестри"]
РЯД = re.compile(r"hand_(\d+) · photo_swap_proposed · item=(\S+) · why=(.*?) · code=(\w+)(?: · refused=(\w+))?")


def проза(тека):
    """Записана відповідь опису з `swap` → (текст, як_носити); с5 — текст картки з вердиктів."""
    в = os.path.join(П, тека, "VIDPOVIDI")
    for ф in sorted(os.listdir(в)) if os.path.isdir(в) else []:
        т = open(os.path.join(в, ф), encoding="utf8", errors="replace").read() if ф.endswith(".txt") else ""
        відп = т.split("── ВІДПОВІДЬ", 1)[-1]
        if '"swap"' not in відп:
            continue
        м = re.search(r"\{.*\}", відп, re.S)
        try:
            о = json.loads(м.group(0))
        except Exception:
            continue
        if о.get("swap"):
            return str(о.get("text") or ""), [str(х) for х in (о.get("how_to_wear") or [])]
    for ф in os.listdir(os.path.join(П, тека)):
        if ф.startswith("verdykty") and ф.endswith(".json"):
            т = open(os.path.join(П, тека, ф), encoding="utf8").read()
            for м in re.finditer(r'"([^"]*Я замінюю[^"]*)"', т):
                return json.loads('"%s"' % м.group(1)), []
    return None, []


випадки = []
for тека in ТЕКИ:
    журнал = "".join(open(os.path.join(П, тека, ф), encoding="utf8", errors="replace").read()
                     for ф in os.listdir(os.path.join(П, тека)) if ф in ("лог.txt", "вердикти.txt") or ф.startswith("verdykty"))
    м = РЯД.search(журнал)
    if not м:
        continue
    рука, річ, чому, стан, відмова = м.groups()
    рішення = re.search(r"hand_%s · photo_swap_decided · state=(\w+)(?: · to=(\S+))?" % рука, журнал[м.end():])
    текст, як = проза(тека)
    словник = {річ: {"слот": "x"}, "нова": {"слот": "x"}}
    перше = dict(стан=стан, річ=річ, чому=чому, **({"відмова": відмова} if відмова else {}))
    друге = None
    if рішення:
        друге = dict(стан=рішення.group(1), річ=річ, чому=чому, **({"на": "нова", "ід": ["інша", "нова"]} if рішення.group(1) == "accepted" else {}))
        друге["текст"] = ЗФ.текст_складу(друге, ["інша", річ], словник)
        перше = dict(перше, запасні=[{"id": "нова"}])
    перше["текст"] = ЗФ.текст_складу(перше, ["інша", річ], словник)
    випадки.append(dict(тека=тека, перше=перше, друге=друге, проза=текст, як=як))
json.dump(випадки, open("/tmp/е3г_випадки.json", "w"), ensure_ascii=False)
старий = subprocess.run(["git", "-C", КОР, "show", "origin/main:джерела/показ/збирання_руки.js"], capture_output=True, text=True, check=True).stdout
open("/tmp/е3г_старий.js", "w").write(старий)
вих = subprocess.run(["node", os.path.join(os.path.dirname(__file__), "повтор.js"), "/tmp/е3г_випадки.json", "/tmp/е3г_старий.js",
                      os.path.join(КОР, "джерела", "показ", "збирання_руки.js")], capture_output=True, text=True)
print(вих.stdout + вих.stderr)

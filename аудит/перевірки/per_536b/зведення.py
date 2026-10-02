# -*- coding: utf-8 -*-
"""ПЕРЕВИМІР-536: зведення живих прогонів стенда (ZHYVA=sonnet) по теках <набір>_<клітинка> (типово — поточна тека); друкує факти, нічого не викликає."""
import json, re, sys, glob, os, gzip
К = sys.argv[1] if len(sys.argv) > 1 else "."
for т in sorted(glob.glob(К + "/*_[A-D]")):
    лог, d = open(т + "/stend.log", encoding="utf-8").read(), json.load(gzip.open(т + "/вердикти.txt.gz", "rt", encoding="utf-8"))["прогони"][0]["вердикти"]
    кінець = max([float(m.group(2)) for m in re.finditer(r"^\s+([\d.]+) →\s+([\d.]+)\s+\(", лог.split("ЧАСИ ЗБОРУ")[1].split("\n\n")[0], re.M)] or [0])
    картки = open(т + "/картки.txt", encoding="utf-8").read().split("═══ картка")[1:]
    стеля = re.search(r"понад стелю виводу продукту — (\d+) \(([^)]*)\)", лог)
    print(f"## {os.path.basename(т)} · «Зібрати образи» → усі картки {кінець:.0f} с · відповідей понад стелю виводу {стеля.group(1) if стеля else 0}: {стеля.group(2)[:200] if стеля else ''}")
    for x in d:
        if str(x["рука"]) not in "12": continue
        с, ід = x["етапи"]["суд"], set(x["склад"].split("+"))
        прийнято = any(set(о["ід"]) == ід and о.get("перевірено") and not о.get("блокує") for о in с["образи"])
        к = next(k for k in картки if f"рука {x['рука']} " in k.split("\n")[0])
        прози = any(p.startswith("Чому це працює") or (len(p) > 200 and not re.match(r"^[^:.]{2,45}: ", p)) for p in к[к.index("Чому цей образ"):к.index("Як це носити")].split("\n"))
        вага = [(f["правило"], f["сила"]) for f in с["знахідки"] if f["сила"] in ("hard", "strong", "soft")]
        print(f"  рука {x['рука']}: речей {len(ід)} · ітерацій {x['ітерацій']} · викликів {x['викликів']} · прийнято кодом {прийнято} · блокує {с['блокує']} · проза на картці {прози} ({x['текст'] and len(x['текст'])} симв.) · знахідок {len(с['знахідки'])} (soft+ {len(вага)}): {вага}")
        print("    речі:", " | ".join(i["назва"] + f" [{i.get('категорія')}]" for i in x["речі_образу"]))

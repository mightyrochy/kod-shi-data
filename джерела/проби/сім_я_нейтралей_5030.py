# -*- coding: utf-8 -*-
"""5030: ДО/ПІСЛЯ на повному каталозі; пороги суду та кольорові контролі сталі."""
import ast, os, sys, subprocess
from collections import Counter
from types import FunctionType
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as КС, колір_річ as КР, дріт_моделі as Д
import фід_каталог as Ф, пакет_моделі as П, композитор_річ as КМ
БАЗА = "8f22756364e060d4fc968671be11740d6aed8ceb"
def було(м, ім):
    """Функція ДО з перевіреної бази, без дублювання її логіки у пробі."""
    текст = subprocess.check_output(["git", "show", f"{БАЗА}:джерела/{м.__name__}.py"], text=True)
    вузол = next(n for n in ast.parse(текст).body if isinstance(n, ast.FunctionDef) and n.name == ім)
    простір = dict(vars(м))
    exec(compile(ast.Module(body=[вузол], type_ignores=[]), "<ДО>", "exec"), простір)
    return простір[ім]
if __name__ == "__main__":
    тон_до = було(П, "_сім_я_тону")
    річ_до = FunctionType(Д.річ.__code__, dict(vars(Д), _сім_я_речі=було(Д, "_сім_я_речі")), argdefs=Д.річ.__defaults__)
    кат = Ф.база_прогону(Ф.каталог_на_диску("каталог_повний.xml"), ліміт_фото=0)["каталог"]
    групи = {}; вади = 0
    for р in кат:
        hex_ = р.get("hex") or (КМ.hex_від_lab(р["lab"]) if р.get("lab") else None)
        if not hex_: continue
        lab = КС.hx(hex_); суд = Д.код("colour_family", КР.сім_я(lab))
        вхід = dict(р, hex=hex_, колір=р.get("колір") or р.get("колір_назва"))
        до = річ_до(П.річ_пулу(dict(вхід, сім_я=тон_до(hex_)), {}))
        після = Д.річ(П.річ_пулу(dict(вхід, сім_я=П.сім_я_тону(hex_)), {}))
        нейтр = КР.нейтраль(lab) is not None; буре = КР._темне_буре(*КС.lch(lab))
        бордо = Д.колір_код(вхід["колір"])[0] == "burgundy"
        наз = "темне буре" if буре else ("нейтраль" if нейтр else "кольоровий контроль")
        for група in [наз] + (["бордо нейтраль" if нейтр else "бордо кольоровий"] if бордо and not буре else []):
            групи.setdefault(група, Counter())[(до.get("family"), після.get("family"), суд)] += 1
        вади += (після.get("family") != суд if нейтр else до != після)
        вади += {к: v for к, v in до.items() if к != "family"} != {к: v for к, v in після.items() if к != "family"}
        вади += буре and до != після
    for наз, пари in групи.items():
        print(наз, "речей", sum(пари.values()), "зміни family", sum(n for (a, b, _), n in пари.items() if a != b), dict(пари))
    print("Каталог", len(кат), "вад", вади)
    sys.exit(bool(вади))

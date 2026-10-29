"""Кожне перше поєднання прийому (те, що на чипі) — суд за кінцевим hex і за внутрішнім Lab палітри.
argv: дерево, вихід.txt. Ті самі функції, що й у PR: набір_законний, та_сама_сім_я, сила ≥ 0.5."""
import sys, json, pathlib, itertools
from collections import Counter
sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / "джерела"))
import bridge as М, palettes as П, colorspace as cs, колір_річ as КР, колір_відношення as КВ
ориг = П.палітра_практична
зап = []
def запис(*а, **к):
    р = ориг(*а, **к); зап.append((р, к.get("контраст_рівень"))); return р
П.палітра_практична = запис
КЛАС = {"аналогова": "analogous", "приглушена_комплементарна": "complementary", "тріада": "triadic"}
def точка(lab):
    L, C, h = cs.lch(tuple(lab)); return dict(L=L, C=C, h=h, lab=tuple(lab))
def суд(кольори, прийом, кр):
    законно, чому = П.набір_законний(кольори, кр)
    пари = []
    кл = КЛАС.get(прийом)
    if кл:
        кол = [к for к in кольори if к["роль"] == "колір"]
        for а, б in itertools.combinations(кол, 2):
            сс = КР.та_сама_сім_я(dict(lab=а["lab"]), dict(lab=б["lab"]))
            с = КВ.сила(КР.запис_кольору(dict(lab=а["lab"])), КР.запис_кольору(dict(lab=б["lab"])), кл)[0]
            if сс != "ні" or с < 0.5: пари.append((а["hex"], б["hex"], сс, round(с, 2)))
    return законно, чому, пари
out = open(sys.argv[2], "w", encoding="utf-8")
лік = Counter()
сітка = itertools.product(
    ("#f1d0b5", "#e8b99b", "#bb8561", "#8d573c", "#5a3a2a"),
    ("#3b2417", "#765336", "#9a803e", "#56816b", "#5c8499", "#687982", "#9c9e87"),
    ("#16110e", "#70503b", "#d4b887"), ("золото", "срібло", "обидва"))
for і, (ш, о, в, м) in enumerate(сітка):
    зап.clear()
    М.палітри(dict(шкіра=[ш], очі=о, волосся=[в], обхвати={}, зріст=168, самозвіт=dict(метал=м)))
    бачено = set()
    for Пр, кр in зап:
        за_hex = {к["hex"]: к for к in Пр["кольори"]}
        перші = {}
        for q in Пр["поєднання"]:
            перші.setdefault(q["прийом"], q)
        for прийом, q in перші.items():
            ключ = (прийом, tuple(к["hex"] for к in q["кольори"]), кр)
            if ключ in бачено: continue
            бачено.add(ключ)
            hexк = [dict(точка(cs.hx(к["hex"])), hex=к["hex"], роль=к["роль"]) for к in q["кольори"]]
            внутр = [dict(точка(за_hex[к["hex"]]["lab"]), hex=к["hex"], роль=к["роль"]) if к["hex"] in за_hex else None for к in q["кольори"]]
            зh = суд(hexк, прийом, кр)
            зв = суд(внутр, прийом, кр) if all(внутр) else None
            вада = (not зh[0]) or зh[2]
            лік[(прийом, "додаткове" if q.get("додаткове") else "основне", "вада_hex" if вада else "ок")] += 1
            if вада:
                print(і, ш, о, в, м, кр, прийом, "додаткове" if q.get("додаткове") else "основне",
                      [к["hex"] for к in q["кольори"]], "| hex:", зh, "| внутр:", зв, file=out, flush=True)
    if і % 50 == 0: print(і, flush=True)
print("ЛІК", json.dumps({"|".join(к): v for к, v in sorted(лік.items())}, ensure_ascii=False), file=out)
out.close(); print("готово")

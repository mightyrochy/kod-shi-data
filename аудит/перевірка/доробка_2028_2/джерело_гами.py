"""Звірка всіх поєднань джерела на 315 входах у трьох гамах.

python аудит/перевірка/доробка_2028_2/джерело_гами.py <дерево> <вихід.json>
"""
import gzip
import itertools
import json
import pathlib
import sys
from collections import Counter


def головна():
    """Друкує законність кінцевих пар і наборів, зберігає кожен провал."""
    корінь = pathlib.Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(корінь / "джерела"))
    import bridge as М
    import palettes as П
    import colorspace as КС
    import колір_річ as КР
    import колір_відношення as КВ
    базові = json.loads(gzip.decompress((корінь / "аудит/перевірка/кольори_9858/персони.json.gz").read_bytes()))
    результати = []
    for гама in ("середні", "приглушені", "насичені"):
        вади, набори, пари, без_тріади = [], Counter(), Counter(), []
        координати_не_з_hex = 0
        for і, персона in enumerate(базові):
            вхід = персона["вхід"]
            F = М._features(вхід)[0]
            контраст = П.контраст_особи(F).get("рівень")
            пал = П.палітра_практична(F, самозвіт=вхід.get("самозвіт"), контраст_рівень=контраст, насиченість=гама)
            координати_не_з_hex += sum(tuple(к["lab"]) != tuple(КС.hx(к["hex"])) for к in пал["кольори"])
            if not any(п["прийом"] == "тріада" for п in пал["поєднання"]):
                без_тріади.append(і)
            for п in пал["поєднання"]:
                прийом = п["прийом"]
                кольори = [dict(к, lab=КС.hx(к["hex"])) for к in п["кольори"]]
                for к in кольори:
                    к["L"], к["C"], к["h"] = КС.lch(к["lab"])
                набори[прийом] += 1
                if not П.набір_законний(кольори, контраст)[0]:
                    вади.append(dict(персона=і, прийом=прийом, причина="набір", hex=[к["hex"] for к in кольори]))
                клас = {"тріада": "triadic", "аналогова": "analogous", "приглушена_комплементарна": "complementary"}.get(прийом)
                if not клас:
                    continue
                кольорові = [к for к in кольори if к["роль"] == "колір"]
                for а, б in itertools.combinations(кольорові, 2):
                    сила = КВ.сила(КР.запис_кольору(а), КР.запис_кольору(б), клас)[0]
                    пари[прийом] += 1
                    if сила < 0.5 or КР.та_сама_сім_я(а, б) != "ні":
                        вади.append(dict(персона=і, прийом=прийом, причина="пара", сила=сила, hex=[а["hex"], б["hex"]]))
        р = dict(гама=гама, персон=len(базові), набори=dict(набори), пари=dict(пари),
                 без_тріади=без_тріади, координати_не_з_hex=координати_не_з_hex, вади=вади)
        результати.append(р)
        print(json.dumps(dict(р, вади=len(вади)), ensure_ascii=False), flush=True)
    pathlib.Path(sys.argv[2]).write_text(json.dumps(результати, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    головна()

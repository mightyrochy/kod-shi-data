# -*- coding: utf-8 -*-
"""Скретч: аркуш 40 речей, що змінили вердикт за варіантом (а'): суд K-PAL-03/09/10/14 (виміри й слова) і K-PAL-17.
Одна зміна на річ, вибір — сід. Клітинка: фото, річ | край дуги (чи очі) | центр дуги на L*, C* речі; ДО→ПІСЛЯ."""
import sys, os, json, pickle, random, collections as K
SP = os.path.dirname(os.path.abspath(__file__)) + "/"; sys.path.insert(0, SP); import foto
сід = int(sys.argv[1]); кут = lambda a, b: min(abs(a - b) % 360, 360 - abs(a - b) % 360)
def край(h, д): return д[0] if кут(h, д[0]) < кут(h, д[1]) else д[1]
з = []
for p in pickle.load(open(SP + "зм_а.pkl", "rb")):
    з.append(dict(p, дж="суд", до=p["в005"], пс="ні", край_h=край(p["h"], p["д"]), центр_h=p["ц"]))
for p in pickle.load(open(SP + "зм_а_сл.pkl", "rb")):
    з.append(dict(p, дж="суд-сл", до=p["в005"], пс=p["нове"], край_h=край(p["h"], p["д"]), центр_h=p["ц"]))
sys.path.insert(0, "."); import colorspace as cs
ВК = {}
for p in pickle.load(open(SP + "вар.pkl", "rb"))["пари"]:
    if p["мн"] == "вікно" and (p["ід"] not in ВК or p["с"][0] > ВК[p["ід"]]["с"][0]): ВК[p["ід"]] = p
for p in pickle.load(open(SP + "зм_17.pkl", "rb")):
    eL, eC, eh = cs.lch(cs.hx(p["очі"]))
    if p["до"]["роль"] != p["пс"]["роль"]:
        з.append(dict(p, дж="17-очі", мн="очі", ім=p["очі"], ц=eh, пів=0, д=(eh, eh), вим=True, до=p["до"]["роль"][:6], пс=p["пс"]["роль"][:6],
                      край_h=None, центр_h=eh, очі_lab=cs.hx(p["очі"])))
    else:
        в = ВК[p["ід"]]
        з.append(dict(p, дж="17-стан", мн="сім'я", ім=в["ім"], ц=в["ц"], пів=в["пів"], д=в["д"], вим=True,
                      до=p["до"]["стан"][:7], пс=p["пс"]["стан"][:7], край_h=край(p["h"], в["д"]), центр_h=в["ц"]))
по = {}
ф = sys.argv[2] if len(sys.argv) > 2 else "True"
for p in random.Random(сід).sample(з, len(з)):
    if eval(ф, {}, p): по.setdefault(p["ід"], p)
print("змін", K.Counter(p["дж"] for p in з), "речей", len(по), K.Counter(p["дж"] for p in по.values()))
вибір = list(по.values())[:40]; рр = []
for p in вибір:
    за = max(0.0, кут(p["h"], p["ц"]) - p["пів"])
    рр.append(dict(p, підпис="%s %s/%s h%.0f ц%.0f±%.0f +%.1f° L%.0f C%.0f" % (p["дж"], str(p["мн"])[:5], str(p["ім"])[:4], p["h"], p["ц"], p["пів"], за, p["L"], p["C"])))
foto.аркуш(рр, SP + (sys.argv[3] if len(sys.argv) > 3 else "аркуш_а") + "_%d.png")
json.dump([{k: v for k, v in р.items() if k not in ("с", "до_п", "пс_п")} for р in рр], open(SP + (sys.argv[3] if len(sys.argv) > 3 else "аркуш_а") + ".json", "w"), ensure_ascii=False, indent=0, default=str)

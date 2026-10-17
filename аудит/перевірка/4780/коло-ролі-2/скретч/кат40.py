# -*- coding: utf-8 -*-
"""КОЛО-РОЛІ (рядок 4780): аркуш 40 змінених речей каталогу. Кольорові речі пакета стенда × унікальні дуги ролей схем
(12 якорів): ДО — суд K-PAL-03 на main (тверда дуга CIELAB ±пів із запасом 10°), ПІСЛЯ — код (`колір_річ.у_дугах_кола`,
зріз `КІНЕЦЬ_ЗГАСАННЯ`). Випадкові 40 змінених (сід з аргументу) — аркуші з фото: річ | центр ролі на L*, C* речі.
Запуск із джерела/: python3 кат40.py <тека виводу> <сід>"""
import sys, os, json, random, collections as K
ТУТ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ТУТ); sys.path.insert(0, ".")
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ, палітра_схеми as ПС, foto
вих, сід = sys.argv[1], int(sys.argv[2])
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); B.виклик("запити", json.dumps(вх0, ensure_ascii=False))
кат = [r for r in B.каталог_останнього_пакета() if КР.межі_кольору(r) and КР.нейтраль_меж(r) == "ні"]
def до_дуга(x, д, запас):
    д = ((д[0] - запас) % 360, (д[1] + запас) % 360); м = КР.межі_кольору(x)
    if КР.не_вимір(x) is None: return "так" if КР._на_дузі(м[4][0] % 360, д) else "ні"
    if м[4] is None: return "невідомо"
    вл = {КР._на_дузі(h, д) for h in КР._тони_дуги((м[4][0] % 360, м[4][1] % 360), [д])}
    return "так" if вл == {True} else "ні" if вл == {False} else "невідомо"
ролі = {}
for i in range(12):
    for сх, з in ПС.СХЕМИ.items():
        for роль, д in з["тон"](cs.з_кола_художника(30.0 * i)).items():
            if isinstance(д, tuple): ролі.setdefault(д, (сх, роль))
ЗМ, Л = [], K.Counter()
for д, (сх, роль) in ролі.items():
    ц, пів = КВ._параметри_дуги(д)
    for x in кат:
        до, пс = до_дуга(x, д, 10.0), КР.у_дугах_кола(x, [д], КВ.КІНЕЦЬ_ЗГАСАННЯ)
        if до != пс:
            L, C, h = cs.lch(x["lab"]); Л[(до + "→" + пс, "C<34" if C < 34 else "C≥34", "слово" if КР.не_вимір(x) else "вимір")] += 1
            ЗМ.append(dict(ід=x["id"], lab=tuple(x["lab"]), фото=(x.get("фото") or [None])[0], центр_h=ц, до=до, пс=пс,
                           підпис="%s/%s %s h%.0f→ц%.0f±%.0f L%.0f C%.0f" % (сх[:6], роль[:4], "сл" if КР.не_вимір(x) else "вим", h, ц, пів, L, C)))
print("кольорових речей %d, ролей %d, пар %d, змін %d" % (len(кат), len(ролі), len(кат) * len(ролі), len(ЗМ)))
for k, n in sorted(Л.items(), key=lambda kv: -kv[1]): print("  %-14s %-5s %-6s %5d" % (*k, n))
вибір = random.Random(сід).sample(ЗМ, 40)
foto.аркуш(вибір, os.path.join(вих, "аркуш40_%d.png"))
json.dump([dict(в, lab=list(в["lab"])) for в in вибір], open(os.path.join(вих, "аркуш40.json"), "w"), ensure_ascii=False, indent=0)

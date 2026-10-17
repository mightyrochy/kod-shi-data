# -*- coding: utf-8 -*-
"""Скретч: каталог × унікальні дуги ролей — змінені вердикти (ДО тверда дуга CIELAB ±пів+10, ПІСЛЯ у_дугах_кола) з фото."""
import sys, os, json, random, pickle
SP = "/tmp/claude-0/-home-user-kod-shi-data/9a5eb989-d513-548d-aefc-237879e686bd/scratchpad/"
os.chdir("/home/user/kod-shi-data/джерела"); sys.path.insert(0, "."); sys.path.insert(0, SP)
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ, палітра_схеми as ПС
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
ЗМ = []
for д, (сх, роль) in ролі.items():
    м0, пів = cs.тон_манселла(д[0]), ((cs.тон_манселла(д[1]) - cs.тон_манселла(д[0])) % 360) / 2
    ц = cs.з_манселла(м0 + пів)
    for x in кат:
        до, пс = до_дуга(x, cs._arc(ц, пів), 10.0), КР.у_дугах_кола(x, [д], КВ.КІНЕЦЬ_ЗГАСАННЯ)
        if до != пс:
            ЗМ.append(dict(ід=x["id"], lab=tuple(x["lab"]), фото=(x.get("фото") or [None])[0], назва=x.get("назва"), url=x.get("url"),
                           слово=КР.не_вимір(x) is not None, центр=ц, пів=пів, сх=сх, роль=роль, до=до, пс=пс))
print("змін", len(ЗМ))
pickle.dump(ЗМ, open(SP + "кат_зм.pkl", "wb"))

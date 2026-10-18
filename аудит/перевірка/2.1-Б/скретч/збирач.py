# Скретч 2.1-Б: вердикти тону суду (кінець згасання) на ролях і вікнах + K-PAL-17 (стан, роль) — для різниці ДО/ПІСЛЯ.
# Запуск з теки джерела/ потрібного дерева: python3 збирач.py <вихід.json>
import json, glob, sys, inspect; sys.path.insert(0, ".")
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ, палітра_схеми as ПС, palettes as ПЛ, річ_з_фото as РФ
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); B.виклик("запити", json.dumps(вх0, ensure_ascii=False))
речі = [r for r in B.каталог_останнього_пакета() if КР.межі_кольору(r) and КР.нейтраль_меж(r) == "ні"]
нове = "до_кінця_згасання" in inspect.signature(КР.у_дугах_кола).parameters
суд = (lambda x, д: КР.у_дугах_кола(x, [д], до_кінця_згасання=True)) if нове else (lambda x, д: КР.у_дугах_кола(x, [д], КВ.КІНЕЦЬ_ЗГАСАННЯ))
ролі = {д: ("%s/%s" % (зн, ім)) for i in range(12) for зн, з in ПС.СХЕМИ.items() for ім, д in з["тон"](cs.з_кола_художника(30.0 * i)).items() if isinstance(д, tuple)}
жінки = [вх0] + [dict(вх0, шкіра=Ж["skin"][0], волосся=Ж["hair"], очі=Ж["eyes"]) for Ж in (json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob("../аудит/проби/жінки/ж*.json")))]
П = [ПЛ.палітра_практична(B._features(вх)[0]) for вх in жінки]
вікна = {tuple(д): ("вікно/%s" % с) for п in П for с, дд in п["вікна"]["сім_ї"].items() if с != "очі" for д in дд}
дуги = {**{д: ("роль/" + к) for д, к in ролі.items()}, **вікна}
out = {"тон": {}, "17": {}, "речі": {}}
for x in речі:
    L, C, h = cs.lch(tuple(x["lab"])); вим = КР.не_вимір(x) is None
    out["речі"][x["id"]] = dict(lab=list(x["lab"]), L=L, C=C, h=h, вим=вим, фото=x.get("фото"), назва=x.get("назва"), колір=x.get("колір_назва"))
    for д, к in дуги.items(): out["тон"]["%s|%s|%s" % (x["id"], к, json.dumps(list(д)))] = суд(x, д)
    if вим and КР.нейтраль(tuple(x["lab"])) is None:
        for i, п in enumerate(П):
            м = РФ.членство_в_палітрі(x["lab"], п); out["17"]["%s|%d" % (x["id"], i)] = [м["стан"], м["роль"][:6], жінки[i]["очі"]]
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False)
print(len(речі), len(дуги), len(out["тон"]), len(out["17"]))

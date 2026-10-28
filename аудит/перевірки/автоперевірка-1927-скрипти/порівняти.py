"""ДО/ПІСЛЯ каталогу за id: типи, центри у вимірі, lab в інтервалах, приклади наряду, нові записи, нейтраль центру проти вікна.
Аргументи: дерево_голови база.json голова.json"""
import json, os, sys, collections as К
шл = [os.path.abspath(п) for п in sys.argv[2:4]]
дж = os.path.abspath(os.path.join(sys.argv[1], "джерела")); os.chdir(дж); sys.path.insert(0, дж)
import колір_річ as КР, colorspace as CS, verify as V
до = {r["id"]: r for r in json.load(open(шл[0], encoding="utf-8"))["каталог"]}
пі = {r["id"]: r for r in json.load(open(шл[1], encoding="utf-8"))["каталог"]}
print("записів ДО", len(до), "ПІСЛЯ", len(пі), "втрачено id", len(set(до) - set(пі)), "нових", len(set(пі) - set(до)))
print("типи ПІСЛЯ", dict(К.Counter(КР.тип_кольору(r) for r in пі.values())))
print("колір_тип поле ПІСЛЯ", dict(К.Counter(r.get("колір_тип") for r in пі.values())))
print("не-вимір з lab ПІСЛЯ", sum(1 for r in пі.values() if КР.тип_кольору(r) != "вимір" and r.get("lab")))
# центр вікна з типом вимір: lab ПІСЛЯ рівний lab ДО, де ДО джерело назва_вікно
центри = [i for i, r in пі.items() if КР.тип_кольору(r) == "вимір" and i in до and до[i].get("джерело_кольору") == "назва_вікно"
          and r.get("lab") and до[i].get("lab") and max(abs(a - b) for a, b in zip(r["lab"], до[i]["lab"])) < 0.05]
print("вимір ПІСЛЯ з lab = центр вікна ДО:", len(центри), центри[:5])
пер = К.Counter((до[i].get("джерело_кольору"), "інтервал" if КР.не_вимір(до[i]) else "вимір", КР.тип_кольору(r)) for i, r in пі.items() if i in до)
for к, н in sorted(пер.items(), key=lambda x: -x[1]): print("ДО джерело/тип → ПІСЛЯ тип", к, н)
for і in ("ж-00378@vilni.store", "ж-00994@vilni.store", "ж-01020@vilni.store", "ж-00276@gepur.com", "ж-02454@ricamare.com.ua",
          "ж-05743@cultboutique.com.ua", "ж-00260@25union.com.ua"):
    а, б = до.get(і) or {}, пі.get(і) or {}
    print(і, "| ДО", а.get("джерело_кольору"), а.get("колір_назва"), [round(x) for x in а.get("lab") or []],
          "| ПІСЛЯ", КР.тип_кольору(б), б.get("колір_назва"), "lab", [round(x) for x in б.get("lab") or []],
          "вимір", {к: б.get("колір_вимір", {}).get(к) for к in ("hex", "придатний", "чому")})
нові = [пі[i] for i in set(пі) - set(до)]
print("нові: слоти", dict(К.Counter(r.get("слот") for r in нові).most_common(8)), "типи", dict(К.Counter(КР.тип_кольору(r) for r in нові)),
      "з фото", sum(1 for r in нові if r.get("фото")), "з колір_назва", sum(1 for r in нові if r.get("колір_назва")))
for r in нові[:6]: print("  новий", r["id"], r.get("слот"), (r.get("назва") or "")[:50], "|", r.get("колір_назва"), "| вимір", (r.get("колір_вимір") or {}).get("hex"))
# нейтраль: центр ДО (точка) проти вікна ПІСЛЯ
н = К.Counter()
for i, r in пі.items():
    if i not in до or КР.тип_кольору(r) != "інтервал" or not до[i].get("lab") or not КР.не_вимір(до[i]): continue
    н[(bool(КР.нейтраль(tuple(до[i]["lab"]))), КР.нейтраль_меж(r))] += 1
print("інтервали: (центр ДО нейтраль, нейтраль_меж ПІСЛЯ) →", dict(н))

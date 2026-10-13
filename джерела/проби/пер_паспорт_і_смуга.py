# -*- coding: utf-8 -*-
"""ПЕР-492: паспорт, пояснення_мови, хід мовної моделі і образи рук 1–2 нижче смуги з файлу вердиктів стенда. Запуск: python3 джерела/проби/пер_паспорт_і_смуга.py <тека запуску з вердикти.txt[.gz]>"""
import sys, json, re, os, collections
тека = os.path.abspath(sys.argv[1])
Д = "/home/user/kod-shi-data/джерела"; sys.path.insert(0, Д); os.chdir(Д)
import feed as F; F.каталог_на_диску("каталог_повний.xml")
import фід_каталог as ФК, фід_слот as ФС, композитор_придатні as КП, формальність as ФО
import gzip
д_ = os.path.join(тека, "вердикти.txt")
d = json.load(gzip.open(д_ + ".gz", "rt", encoding="utf-8") if os.path.exists(д_ + ".gz") else open(д_, encoding="utf-8"))
g = d["спільне"]; п = g.get("паспорт") or {}
print("== ", тека)
print("паспорт: нагода=%s місце=%s ошатність=%s година=%s джерело=%s пояснення_мови=%r" % (п.get("нагода"), п.get("місце"), п.get("ошатність"), п.get("година"), п.get("джерело"), п.get("пояснення_мови")))
print("виміри: ", {k: v for k, v in (п.get("виміри") or {}).items() if v not in ("unknown", None, "none", [], "usual")})
print("випадок_моделі:", g.get("випадок_моделі"))
for ч in g.get("чат", []):
    for м in ч.get("мова_шару", []) or []:
        print("  хід:", м.get("де"), json.dumps(м.get("внутрішня"), ensure_ascii=False)[:700])
        print("  ноти:", "stylist_note" in json.dumps(м, ensure_ascii=False))
    print("  чат:", ч["хто"], ч["текст"][:300])
сц = {"ошатність": п.get("ошатність")}; смуга = ФО.смуга_ошатності(сц)
print("смуга для проби:", смуга)
lo = смуга[0] if смуга else None
за = collections.defaultdict(list)
for r in ФК._прочитати_каталог("каталог_повний.xml", 0)["каталог"]: за[(ФС.назва_для_людини(r), r.get("ціна"))].append(r)
ID = re.compile(r"\{.*\}", re.S)
for в in d["прогони"][0]["вердикти"]:
    в["рука"] = int(re.sub(r"\D", "", str(в["рука"])) or 0)
    if в["рука"] not in (1, 2): continue
    виклики = в["етапи"]["виклики"]; зб = виклики[0]; пакет = json.loads(зб["запит"]["текст"][зб["запит"]["текст"].index("{"):])
    пул = {р["n"]: за.get((р["name"], р.get("price"))) or [] for р in пакет.get("pool", [])}
    вер = lambda н: (пул.get(н) or [{}])[0]
    відп = зб["відповідь_сира"]; обр = json.loads(відп[відп.index("{"):])["outfits"]
    рядки = []; всього = 0; нев = set()
    for о in обр:
        п_ = [н for н in о["items"] if lo is not None and вер(н) and КП.нижче_смуги(вер(н), lo)]
        рядки.append((о["id"], len(о["items"]), п_)); всього += len(п_); нев.update(п_)
    наз = {р["n"]: р["name"] for р in пакет.get("pool", [])}
    print("рука %d · пул %d · нижче смуги в пулі %d · образів %d · образів з недоречною %d · різних недоречних %d" % (в["рука"], len(пул), sum(1 for н in пул if lo is not None and вер(н) and КП.нижче_смуги(вер(н), lo)), len(обр), sum(1 for _, _, x in рядки if x), len(нев)))
    for н in sorted(нев): print("     ", н, наз.get(н, "")[:60], "|", КП.нижче_смуги(вер(н), lo), "| слот", вер(н).get("слот"))

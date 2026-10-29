# -*- coding: utf-8 -*-
"""5511, 5239: промпт ремонту на стенді (`стенд_вх.json`, каталог_повний, 10 образів), без моделі — порядок образів
«verdict» за сідом руки (двічі той самий сід — той самий порядок), запис порядку, розмір промпту, ключі за схемою
відповіді, підписи «chosen» і «set.bold», і чи промпт вибору лишився той самий (sha). Та сама проба на main — «до».
Запуск: cd джерела && python3 проби/ремонт_порядок_5511.py"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge as B, протокол as P
вх0 = dict(json.load(open("стенд_вх.json", encoding="utf-8")), варіантів=10, ремонт_варіантів=5, бюджет_символів=120000, без_фото=1)
for сід in (4242, 4242, 13, 7):
    вх = dict(вх0, сід=сід)
    пул = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["пакети"]["1"]["пул"]
    н = lambda с, k: пул[с][k % len(пул[с])]["н"]
    образи = [dict(ід="о%d" % (і + 1), підпис="образ %d" % (і + 1), полюс=P.ПОЛЮСИ[і % 6], день="Офіс, стіл, коротка дорога.",
                   речі=([н("сукня", і)] if і % 2 else [н("верх", і), н("низ", і)]) + [н(с, і % 3) for с in ("взуття", "сумка")])
              for і in range(10)]
    в = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, текст_моделі=json.dumps(dict(версія="1", образи=образи),
                                                                                    ensure_ascii=False)), ensure_ascii=False)))
    т = в["промпт_ремонту"]; п = json.loads(т)
    порядок = [о["your_outfit"]["id"] for о in п["verdict"]]
    зап = (в.get("порядок_запитів") or {}).get("промпт_ремонту") or {}
    ск = п["answer_schema"]
    print("сід %d: verdict %s · запис %s · промпт %d симв. · за схемою %s · вибір sha %s" % (
        сід, " ".join(порядок), "образи=так" if [str(x).replace("о", "o") for x in зап.get("образи") or []] == порядок
        else "образи=—", len(т),
        list(п)[list(п).index("answer_schema") + 1:] or "—", hashlib.sha1(в["промпт_лише_вибору"].encode()).hexdigest()[:10]))
print("chosen[].id:", ск["chosen"][0]["id"])
print("chosen[].why:", ск["chosen"][0]["why"])
print("outfits[].items:", ск["outfits"][0]["items"][0])
print("now:", п.get("now", "—"))

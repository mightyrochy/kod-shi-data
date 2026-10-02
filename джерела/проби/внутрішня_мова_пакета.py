# -*- coding: utf-8 -*-
"""ВМ-2 (рядки 304, 483, 484): ОДИН пакет кожного виклику функціональної моделі — складання, ремонт, вибір, ОЦІНКА,
ТУРНІР — живим шляхом `bridge` на `стенд_вх.json` («офіс·18°C», сід 3). (1) Усі англійські рядки пакета (листки без
кирилиці, з латиницею: «task», визначення кодів, коди й рядки, які код складає на льоту) — крізь R-LNG-01
(`language_gate.перевірити_внутрішню_мову`): брудних N. (2) Кирилиця поза її словами й словами крамниці (назва, колір
крамниці, рядок особливостей) — символів N і де; `style_rules` лічиться окремо (його пише бриф, наряд ВМ-1).
Запуск із `джерела`: python3 проби/внутрішня_мова_пакета.py"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, стенд_знімок as СЗ, language_gate as LG
КИР, ЛАТ = re.compile("[а-яіїєґА-ЯІЇЄҐ]"), re.compile("[A-Za-z]{2}")   # нижче: її слова й слова крамниці — не мова коду
ЇЇ = {"name", "shop_color", "features", "event", "her_words", "goal_quote", "intent_quote", "her_other_words", "beliefs",
      "she_refuses", "types", "wishes", "mood", "caption", "day", "items", "case"}
вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сценарій=СЗ.СЦЕНАРІЇ["офіс·18°C"], випадок="офіс·18°C", сід=3)
к = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
ід = [рч[0]["id"] for с, рч in к["кандидати"].items() if рч and с in ("верх", "низ", "взуття", "сумка")]
вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=[ід, ід[1:] + ід[:1]]), ensure_ascii=False)))
вибір = lambda с: json.loads(B.виклик("від_моделі", json.dumps(dict(вх, вибір_речей={"спосіб": с}), ensure_ascii=False)))
ПАКЕТИ = {"складання": к["B"], "ремонт": вм.get("промпт_ремонту"), "вибір": вм.get("промпт_лише_вибору"),
          "ОЦІНКА": вибір("оцінка")["вибір_речей"]["запити"][0]["текст"], "ТУРНІР": вибір("турнір")["вибір_речей"]["запити"][0]["текст"]}
def листки(в, шлях=""):
    if isinstance(в, dict):
        for кл, v in в.items():
            if КИР.search(str(кл)): yield шлях + ".KEY", str(кл)
            yield from листки(v, шлях + "." + str(кл))
    elif isinstance(в, (list, str)): yield from ([(шлях, в)] if isinstance(в, str) else (x for v in в for x in листки(v, шлях + "[]")))
усього = 0                                                               # «case» — наряд НП-в
for назва, текст in ПАКЕТИ.items():
    лл, кир, де = list(листки(json.loads(текст or "{}"))), collections.Counter(), collections.Counter()
    en = {"%s#%d" % (ш, і): т for і, (ш, т) in enumerate(лл) if ЛАТ.search(т) and not КИР.search(т)}
    брудні = LG.перевірити_внутрішню_мову(en)["брудні"]; усього += len(брудні)
    for ш, т in лл:
        н = len(КИР.findall(т)); ключ = re.sub(r"\[\]", "", ш).split(".")[-1]
        if not н or ключ in ЇЇ or ".case." in ш: continue
        (кир.update(rules=н) if ".style_rules" in ш else (кир.update(code=н), де.update({ключ: н})))
    print("%-9s рядків %4d · R-LNG-01 брудних %d%s · кирилиці коду %5d%s · style_rules %d" % (назва, len(en), len(брудні),
          "".join(" [%s: %s]" % (б["код"], б["збіги"]) for б in брудні), кир["code"],
          " (" + ", ".join("%s %d" % кн for кн in де.most_common(6)) + ")" if де else "", кир["rules"]))
print("УСЬОГО брудних R-LNG-01: %d" % усього)

# -*- coding: utf-8 -*-
"""Мовний шар на ВХОДІ й ВИХОДІ (збережені слова з проходів): її слова → внутрішня мова (модель
шару) → паспорт (код) → репліка стилістки (модель шару). Друкує внутрішню мову повністю, поле за
полем «очікували → вийшло» і текст репліки. Без MODEL — лише промпт першого випадку.
Запуск: cd джерела && MODEL=mamaylm-gemma-3-12b-it-v2.0 [MODEL_URL=…] python3 проби/мова_входу_вимір.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import мова_спільне as С
М, вийшло = С.М, lambda вн, к: json.dumps(вн.get(к, "unknown"), ensure_ascii=False)
def є(вн, к, v):
    """Чи внутрішня мова несе очікуване: "unknown" — поля нема; список речей — кожна з ознаками."""
    if v == "unknown":
        return к not in вн
    if isinstance(v, list):
        return all(any(x == о or (isinstance(о, dict) and isinstance(x, dict) and all(x.get(а) == б for а, б in о.items()))
                       for x in вн.get(к) or []) for о in v)
    return вн.get(к) == v
збіглось = всього = 0
for в in json.load(open(os.path.join(С.ТУТ, "мова_входу_збережені.json"), encoding="utf-8")):
    вид = в.get("вид", "scenario")
    відп, с1 = С.модель(М.промпт_входу(вид, в["слова"], в.get("контекст")))
    if відп is None:
        print(М.промпт_входу(вид, в["слова"], в.get("контекст")))
        break
    р = М.прийняти_вхід(вид, відп)
    вн = р["внутрішня"]
    print("── %s · %.1f с\n   СЛОВА: %s\n   ВНУТРІШНЯ: %s%s" % (в["де"], с1, в["слова"], json.dumps(вн, ensure_ascii=False),
          "".join("\n   ✗ %s: %s" % пара for пара in (("незнайомі", р["незнайомі"]), ("причина", р["причина"])) if пара[1])))
    for к, v in в["очікуємо"].items():
        ok = є(вн, к, v)
        збіглось, всього = збіглось + ok, всього + 1
        print("   %s %s: очікували %s → %s" % ("✔" if ok else "✗", к, json.dumps(v, ensure_ascii=False), вийшло(вн, к)))
    if вид == "scenario":
        ш = json.loads(М.мова({"паспорт_з": вн, "сценарій": {}, "слова_ходу": в["слова"]}))
        реп = {к: v for к, v in (("recorded", {к: v for к, v in вн.items() if к != "question"}),
               ("advice_topics", ш["теми_поради"]), ("required", ш["обовʼязкове"])) if v}
        т, с2 = С.модель(М.промпт_репліки(реп))
        print("   ПАСПОРТ: %s\n   РЕПЛІКА (%.1f с): %s" % (ш["випадок_людині"], с2, М.прийняти_репліку(т)["текст"] or "✗ " + str(т)[:200]))
print("\nМОДЕЛЬ ШАРУ: %s · ВХІД: збіглось %d з %d очікуваних полів" % (С.МОДЕЛЬ or "нема", збіглось, всього))

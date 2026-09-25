# -*- coding: utf-8 -*-
"""Ремонт: «твій_образ.речі» — самі номери, і gemma (s13, main ff625da0) підписала всі 25 речей «#н/слот» за
місцем у списку: 12 хибних. Тепер біля номера на дріт їде слот (`протокол._твій_образ_на_дріт`). На збережених
промптах і відповідях ремонту: скільки номерів у «твій_образ» ішли без слота до і після, скільки хибних підписів
дає копія поданого, і що стоїть біля номерів, які модель підписала хибно. Слот — пул своєї руки плюс вітрина
(те, що бачить суд). Друкує факт. Запуск: cd джерела && python3 проби/ремонт_слот_біля_номера.py <тека> <сід>"""
import json, os, re, sys
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д)
import протокол as ПР
тека, сід = sys.argv[1], sys.argv[2]
def ч(ф):
    т = open(os.path.join(тека, ф), encoding="utf-8").read(); п, _, в = т.partition("\n\n── ВІДПОВІДЬ")
    return п[п.index("\n") + 1:], (в[в.index("\n") + 1:] if "\n" in в else "")
def дж(т):
    м = re.search(r"```(?:json)?\s*([\s\S]*?)```", т or ""); т = (м.group(1) if м else т or "").strip()
    try: return json.loads(т[т.find("{"):т.rfind("}") + 1])
    except Exception: return {}
фф = sorted((x for x in os.listdir(тека) if x.startswith("seed" + сід + "_")), key=lambda x: int(x.split("_")[1]))
пули = [{р["н"]: с for с, рр in (дж(ч(x)[0]).get("пул") or {}).items() for р in рр} for x in фф if "ПАКЕТ_V1" in x]
for x in фф:
    if "ВЕРДИКТ_V1_ОБРАЗИ_V1" not in x: continue
    вп, вв = map(дж, ч(x))
    суд = [с.get("твій_образ") or {} for с in вп.get("вердикт") or []]
    н = {р for т in суд for р in т.get("речі") or []}
    р = max(range(len(пули)), key=lambda і: len(н & set(пули[і])))
    слот = dict(пули[р]); слот.update({рр["н"]: с for с, ррр in (вп.get("вітрина") or {}).items() for рр in ррр})
    нові = [ПР._твій_образ_на_дріт(dict(т, слоти=[слот.get(і, "") for і in т.get("речі") or []])) for т in суд]
    біля = {re.sub(r"/.*", "", і): і for т in нові for і in т["речі"]}
    без = lambda тт: sum("/" not in і for т in тт for і in т.get("речі") or [])
    копія = sum(1 for і in біля.values() if "/" in і and слот.get(і.split("/")[0]) != і.split("/")[1])
    хибні = [(нн, м) for о in вв.get("образи") or [] for і in о.get("речі") or []
             for нн, м in [re.match(r"\s*(#\d+·\d+)\s*/\s*(\S+)", str(і)).groups() if re.match(r"\s*(#\d+·\d+)\s*/", str(і)) else (0, 0)]
             if нн and слот.get(нн) and слот[нн] != м]
    print("ФАКТ · %s рука %d · номерів у «твій_образ» %d · без слота: до %d, після %d · хибних підписів у копії поданого: %d"
          % (x[:9], р + 1, sum(len(т.get("речі") or []) for т in суд), без(суд), без(нові), копія))
    print("ФАКТ ·   хибні підписи моделі: %d · біля того самого номера тепер стоїть: %s" % (len(хибні),
          "; ".join("%s/%s ← %s" % (нн, м, біля.get(нн, "номера нема в «твій_образ»")) for нн, м in хибні[:6]) or "—"))

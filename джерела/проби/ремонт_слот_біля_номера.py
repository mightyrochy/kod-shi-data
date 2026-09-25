# -*- coding: utf-8 -*-
"""Ремонт: «твій_образ.речі» — самі номери, і gemma (s13, main ff625da0) підписала всі 25 речей «#н/слот» за
місцем у списку: 12 хибних. Тепер річ на дроті — {н, слот, опис як у пулі} (`протокол._твій_образ_на_дріт`). На
збережених промптах і відповідях ремонту: скільки речей у «твій_образ» ішли без слота й опису до і після, скільки
хибних слотів дає копія поданого, що стоїть біля номерів, які модель підписала хибно, і на скільки подовшав промпт.
Слот і опис — обʼєкт речі в пулі своєї руки або у вітрині (те, що бачить модель). Друкує факт. Запуск: cd джерела && python3 проби/ремонт_слот_біля_номера.py <тека> <сід>"""
import json, os, re, sys
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д); тека, сід = sys.argv[1], sys.argv[2]
import протокол as ПР
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
    об = {рр["н"]: рр for x2 in фф if "ПАКЕТ_V1" in x2 for рр_ in (дж(ч(x2)[0]).get("пул") or {}).values() for рр in рр_}
    об.update({рр["н"]: рр for ррр in (вп.get("вітрина") or {}).values() for рр in ррр})
    нові = [ПР._твій_образ_на_дріт(dict(т, слоти=[слот.get(і, "") for і in т.get("речі") or []],
                                         описи=[об.get(і) or {} for і in т.get("речі") or []])) for т in суд]
    біля = {і["н"]: і for т in нові for і in т["речі"] if isinstance(і, dict)}
    без = lambda тт: sum(not (isinstance(і, dict) and і.get("слот") and і.get("назва")) for т in тт for і in т.get("речі") or [])
    копія = sum(1 for і in біля.values() if і.get("слот") and слот.get(і["н"]) != і["слот"])
    дж_ = lambda о: len(json.dumps(о, ensure_ascii=False)); дов = дж_(вп); дов2 = дов + sum(дж_(а) - дж_(б) for а, б in zip(нові, суд))
    хибні = [м.groups() for о in вв.get("образи") or [] for і in о.get("речі") or []
             for м in [re.match(r"\s*(#\d+·\d+)\s*/\s*(\S+)", str(і))] if м and слот.get(м.group(1)) not in (None, м.group(2))]
    print("ФАКТ · %s рука %d · речей у «твій_образ» %d · без слота й опису: до %d, після %d · хибних слотів у копії поданого: %d"
          % (x[:9], р + 1, sum(len(т.get("речі") or []) for т in суд), без(суд), без(нові), копія))
    print("ФАКТ ·   вердикт у промпті: %d → %d симв. (+%d, +%.0f%%)" % (дов, дов2, дов2 - дов, 100.0 * (дов2 - дов) / дов))
    print("ФАКТ ·   хибні підписи моделі: %d · біля того самого номера тепер стоїть: %s" % (len(хибні),
          "; ".join("%s/%s ← %s «%s»" % (нн, м, (біля.get(нн) or {}).get("слот", "—"), str((біля.get(нн) or {}).get("назва", ""))[:28]) for нн, м in хибні[:6]) or "—"))

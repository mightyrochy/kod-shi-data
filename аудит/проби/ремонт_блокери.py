"""#324 (25.09): що ремонт зробив із блокерами структури. На кожну руку прогону стенда: образ після ремонту
(промпт вибору) ↔ образ до ремонту (промпт ремонту) за найбільшим перетином речей; скільки образів після ремонту
без жодного блокера; які блокери ремонт зняв, які лишив і які з'явились НОВІ (їх до ремонту не було).
Рука — за порядком пакетів складання (1-й пакет = рука 1). Запуск: python аудит/проби/ремонт_блокери.py <тека VIDPOVIDI> <сід>"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
тека, сід = sys.argv[1], sys.argv[2]
def ч(ф):
    т = open(os.path.join(тека, ф), encoding="utf-8").read(); п = т.partition("\n\n── ВІДПОВІДЬ")[0]
    п = п[п.index("\n") + 1:]
    try: return json.loads(п[п.find("{"):п.rfind("}") + 1])
    except Exception: return {}
фф = sorted((x for x in os.listdir(тека) if x.startswith("seed" + сід + "_")), key=lambda x: int(x.split("_")[1]))
пули = [{р["н"] for рр in (ч(x).get("пул") or {}).values() for р in рр} for x in фф if "ПАКЕТ_V1" in x]
def образи(д):
    return [(set((с.get("твій_образ") or {}).get("речі") or []), sorted({б.get("код") for б in (с.get("структура") or {}).get("блокери") or []}))
            for с in д.get("вердикт") or [] if isinstance(с, dict)]
def рука(оо): return 1 + max(range(len(пули)), key=lambda і: len(set().union(*[о[0] for о in оо]) & пули[і]))
до, піс = {}, {}
for x in фф:
    if "ВЕРДИКТ_V1_ОБРАЗИ_V1" in x:
        оо = образи(ч(x))
        if len(оо) >= 2: до[рука(оо)] = оо
    elif "ВЕРДИКТ_V1_ВИБІР_V1" in x:
        оо = образи(ч(x)); піс[рука(оо)] = оо
for р in sorted(піс):
    нові, зняті, лиш, чисті = {}, {}, {}, 0
    for речі, бл in піс[р]:
        б0 = max(до.get(р, []), key=lambda о: len(о[0] & речі), default=(set(), []))[1]
        чисті += not бл
        for к in set(бл) - set(б0): нові[к] = нові.get(к, 0) + 1
        for к in set(б0) - set(бл): зняті[к] = зняті.get(к, 0) + 1
        for к in set(б0) & set(бл): лиш[к] = лиш.get(к, 0) + 1
    ф = lambda д: ", ".join("%s %d" % кв for кв in sorted(д.items())) or "—"
    print("рука %d · після ремонту без блокерів %d з %d · зняв: %s · лишив: %s · НОВІ: %s" % (р, чисті, len(піс[р]), ф(зняті), ф(лиш), ф(нові)))

# -*- coding: utf-8 -*-
"""#324 · що ремонт робить зі слотами: на кожен образ, який модель узяла в ремонт (її «ід» — номер образу вердикта,
тобто порядок складання), скільки образів мали річ у слоті ДО ремонту і ПІСЛЯ; і в скількох стоїть її закріплена
річ. Читає теку стенда (`VIDPOVIDI`): пакет складання, відповідь складання, промпт і відповідь ремонту своєї руки.
Слот речі — з пулу й вітрини її руки (не з підпису «/низ» моделі). Запуск: python3 проби/ремонт_слоти.py <тека> [сід]"""
import json, os, re, sys
тека, сід = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
def ч(ф):
    т = open(os.path.join(тека, ф), encoding="utf-8").read(); п, _, в = т.partition("\n\n── ВІДПОВІДЬ")
    return п[п.index("\n") + 1:], (в[в.index("\n") + 1:] if "\n" in в else "")
def дж(т):
    м = re.search(r"```(?:json)?\s*([\s\S]*?)```", т or ""); т = (м.group(1) if м else т or "").strip()
    try: return json.loads(т[т.find("{"):т.rfind("}") + 1])
    except Exception: return {}
номер = lambda р: re.match(r"#?\s*(\d+\s*·\s*\d{2})", str(р)) and "#" + re.sub(r"\s", "", re.match(r"#?\s*(\d+\s*·\s*\d{2})", str(р)).group(1))
ф = sorted(x for x in os.listdir(тека) if x.startswith("seed" + сід) and x.endswith(".txt"))
пакети = [(дж(ч(x)[0]), дж(ч(x)[1])) for x in ф if "ПАКЕТ_V1" in x]
for x in [x for x in ф if "ВЕРДИКТ_V1_ОБРАЗИ_V1" in x]:
    п, в = ч(x); вп = дж(п)
    суд = вп.get("вердикт") or []
    if len(суд) < 2: continue                                     # крок повноти, не ремонт
    н = {номер(р) for с in суд for р in (с.get("твій_образ") or {}).get("речі") or []}
    пак, скл = max(пакети, key=lambda пв: len(н & {р["н"] for рр in пв[0]["пул"].values() for р in рр}))
    слот = {р["н"]: с for с, рр in list(пак["пул"].items()) + list((вп.get("вітрина") or {}).items()) for р in рр}
    закр = set((пак.get("обмеження") or {}).get("закріплені") or [])
    до = {с["твій_образ"]["ід"]: [номер(р) for р in с["твій_образ"]["речі"]] for с in суд}
    після = {о.get("ід"): [номер(р) for р in о.get("речі") or []] for о in (дж(в).get("образи") or [])}
    взято = [і for і in після if і in до]
    слоти = sorted({слот.get(р, "?") for і in взято for р in до[і] + після[і]})
    print("%s · ремонт узяв %d образів (%s)" % (x[:9], len(взято), ", ".join(взято)))
    for с in слоти:
        а = sum(any(слот.get(р) == с for р in до[і]) for і in взято); б = sum(any(слот.get(р) == с for р in після[і]) for і in взято)
        print("   %-14s до %d · після %d%s" % (с, а, б, "  ← спорожнів" if а and not б else ""))
    print("   її річ: до %d · після %d з %d" % (sum(bool(закр & set(до[і])) for і in взято), sum(bool(закр & set(після[і])) for і in взято), len(взято)))

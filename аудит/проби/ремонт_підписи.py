"""#324 (25.09): у відповіді ремонту (ВЕРДИКТ_V1 → ОБРАЗИ_V1) — скільки речей модель підписала «#н/слот» і скільки
таких підписів не збігаються зі слотом речі в пулі своєї руки чи у вітрині (тобто модель вважає річ іншим слотом).
Рука — за найбільшим перетином з пулом пакета складання. Запуск: python аудит/проби/ремонт_підписи.py <тека VIDPOVIDI> <сід>"""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
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
    п, в = ч(x); вп, вв = дж(п), дж(в)
    if len(вп.get("вердикт") or []) < 2: continue
    н = {р for с in вп["вердикт"] for р in (с.get("твій_образ") or {}).get("речі") or []}
    р = max(range(len(пули)), key=lambda і: len(н & set(пули[і])))
    слот = dict(пули[р]); слот.update({рр["н"]: с for с, ррр in (вп.get("вітрина") or {}).items() for рр in ррр})
    усі = пп = неспів = 0; прик = []
    for о in вв.get("образи") or []:
        for р_ in о.get("речі") or []:
            м = re.match(r"\s*(#\s*\d+\s*·\s*\d+)\s*/\s*(\S+)", str(р_)); усі += 1
            if not м: continue
            пп += 1; нн = re.sub(r"\s", "", м.group(1))
            if слот.get(нн) and слот.get(нн) != м.group(2): неспів += 1; прик.append("%s/%s (у пулі: %s)" % (нн, м.group(2), слот.get(нн)))
    print("%s рука %d · речей у відповіді %d · з підписом «/слот» %d · підпис ≠ слот пулу %d%s" % (x[:9], р + 1, усі, пп, неспів,
          (" — " + "; ".join(прик[:6])) if прик else ""))

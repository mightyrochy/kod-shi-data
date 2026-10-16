# -*- coding: utf-8 -*-
"""Рядки 6205/6210–6212/6214: записані промпти (теки VIDPOVIDI аргументами) ДО → ПІСЛЯ правки дроту, у знаках.
Симуляція тими самими функціями `дріт_моделі`: чекліст без input_gaps, речі вердикта легшою формою + item_keys,
учасники знахідок «n», пул без повторних «n» і `pool_keys` з легендою ключів; statement_codes — лише вжиті коди."""
import os, sys, re, json, glob; ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import дріт_моделі as Д, збирач_промптів as З; дамп = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))
def річ(x): return Д._легше({**{к: v for к, v in x.items() if Д.ТИПОВІ_ПУЛУ.get(к, ...) != v}, **({} if "in_arc" in x else {"in_arc": "unknown"})}) if isinstance(x, dict) else x
def учасники(рч, назви): return [н for н in dict.fromkeys(x if not isinstance(x, str) or x.startswith("#") or re.fullmatch(r"o\d+", x) else Д._н_за_назвою(x, назви) for x in рч) if н]
ЛАД = re.compile(r"#\d+·\d\d(/\w+)?|o\d+")  # «n» речі (з половиною комплекту) чи ід образу
def поза_n(зз): return sum(1 for z in зз or [] for x in z.get("items") or [] if isinstance(x, str) and not ЛАД.fullmatch(x)) + sum(дамп(z.get(к)).count("free_text") for z in зз or [] for к in ("statements", "values"))
def усі_зн(д): return [z for о in д["verdict"] for z in о.get("findings") or []] + (д.get("set") or {}).get("findings", []) + [r for рр in (д.get("remarks_by_code") or {}).values() for r in рр]
def знахідки(зз, назви):
    for z in зз or []:
        if z.get("items"): z["items"] = учасники(z["items"], назви)
        z.get("items") or z.pop("items", None); z.update({к: Д._вільні_номерами(z[к], назви) for к in ("statements", "values") if к in z})
for тека in sys.argv[1:]:
    for ф in sorted(glob.glob(os.path.join(тека, "*_ВЕРДИКТ_V1_*.txt")) + glob.glob(os.path.join(тека, "*_ПАКЕТ_V1_*.txt"))):
        т = open(ф, encoding="utf8").read().split("\n\n── ВІДПОВІДЬ (")[0]; д = json.loads(т[т.find("{"):]); до = len(дамп(д))
        поза = прогалин = повторів = поза_до = 0
        if "verdict" in д:
            поза_до, усі = поза_n(усі_зн(д)), {x.get("n"): x.get("name") for о in д["verdict"] for x in о["your_outfit"].get("items", []) if isinstance(x, dict)}
            for о in д["verdict"]:
                прогалин += sum(len(дамп(б.pop("input_gaps"))) if "input_gaps" in б else 0 for б in (о.get("checklist") or {}).values())
                чк = {б: v for б, v in (о.pop("checklist", None) or {}).items() if v}; чк and о.update(checklist=чк)
                о["your_outfit"]["items"] = [річ(x) for x in о["your_outfit"].get("items", [])]
                знахідки(о.get("findings"), {x.get("n"): x.get("name") for x in о["your_outfit"]["items"] if isinstance(x, dict)})
            знахідки((д.get("set") or {}).get("findings"), усі); знахідки([r for рр in (д.get("remarks_by_code") or {}).values() for r in рр], усі)
            д["showcase"] = [річ(x) for x in д.get("showcase", [])]; речі = [x for о in д["verdict"] for x in о["your_outfit"]["items"]] + д["showcase"]
            д = {к2: v for к, v in д.items() for к2, v in ((("item_keys", Д.легенда_ключів(речі)), (к, v)) if к == "verdict" else ((к, v),))}
            д["task"]["input"].insert(2, '"item_keys" — what the keys of the items in «verdict» and «showcase» mean, and defaults for omitted values; read every item by these keys; restore every absent key that has an `absent =` default')
            поза = поза_n(усі_зн(д))
        if "pool" in д:     # таблицею (`збирач_промптів.таблиця`) чи, у записах до рядка 5540, переліком
            кол = д["pool"]["cols"] if isinstance(д["pool"], dict) else None
            усі = [{**dict(zip(кол, р)), **(р[len(кол)] if len(р) > len(кол) else {})} for р in д["pool"]["rows"]] if кол else д["pool"]
            лишок = [i for i, r in enumerate(усі) if r.get("n") not in {x.get("n") for x in усі[:i]}]
            повторів, д["pool"] = len(усі) - len(лишок), dict(д["pool"], rows=[д["pool"]["rows"][i] for i in лишок]) if кол else [усі[i] for i in лишок]
            д["pool_keys"] = Д.легенда_ключів([усі[i] for i in лишок])
            д["task"]["input"] = [x.replace("; «L_from», «hem_from» — what the number was read from; «branch» — where the colour lies against her palette: core, edge or break", "") for x in д["task"]["input"]]
        д["task"]["statement_codes"] = {к: v for к, v in д["task"].get("statement_codes", {}).items() if к in set(З.коди_заяв({к: v for к, v in д.items() if к != "task"}))}
        print("%s · %d → %d знаків (%+.1f %%) · input_gaps %d · учасників поза «n» %s · повторних «n» у pool %d" % (os.path.basename(ф)[:40], до, len(дамп(д)), 100.0 * (len(дамп(д)) - до) / до, прогалин, "%d→%d" % (поза_до, поза) if "verdict" in д else "—", повторів))

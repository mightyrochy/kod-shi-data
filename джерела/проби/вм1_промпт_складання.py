"""ВМ-1: промпт складання рук 1–2 — кирилиця сталої частини, метал і схема (рядки 408, 480–482).
Вхід: файл виклику стенда (`VIDPOVIDI=<тека>`, `seed3_08_ПАКЕТ_V1_ОБРАЗИ_V1.txt`). Друкує факт."""
import json, re, sys
т = open(sys.argv[1], encoding="utf-8").read()
П, _ = json.JSONDecoder().raw_decode(т[т.index("{"):])
КИР = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
# поза мірою: речі пулу (слова крамниці), її слова, рядки нагоди (наряд НП-в), назви відхилених речей
ПОЗА = {"pool", "event", "her_words", "free_text", "quote", "occasion_rules", "she_rejected_items", "beliefs",
        "mood", "wishes", "her_other_words", "goal_quote", "intent_quote"}
def чисте(в):
    if isinstance(в, dict):
        return {к: чисте(v) for к, v in в.items() if к not in ПОЗА}
    return [чисте(x) for x in в] if isinstance(в, list) else в
д = lambda x: len(json.dumps(x, ensure_ascii=False, separators=(",", ":")))
стала = {к: v for к, v in П.items() if к != "pool"}
кир = КИР.findall(json.dumps(чисте(стала), ensure_ascii=False))
print("промпт %d симв. · пул %d · стала частина %d · style_rules %d · occasion_rules %d"
      % (д(П), д(П.get("pool")), д(стала), д(П.get("style_rules") or []), д(П.get("occasion_rules") or [])))
print("кириличних літер у сталій частині поза її словами, назвами речей і рядками нагоди: %d" % len(кир))
for к, v in чисте(стала).items():
    н = len(КИР.findall(json.dumps(v, ensure_ascii=False)))
    if н:
        print("  %s: %d — %s" % (к, н, json.dumps(v, ensure_ascii=False)[:160]))
кл = lambda з: next(iter(з)) if isinstance(з, dict) else з
пр = [кл(з) for з in (П.get("style_rules") or [])]
пал = (П.get("person") or {}).get("palette") or {}
print("метал: заяв %d %s · palette.metal %s · прийом metal %s" % (
    sum(к == "jewellery_metal" for к in пр), [з for з in П.get("style_rules") or [] if кл(з) == "jewellery_metal"],
    пал.get("metal"), any(x.get("technique") == "metal" for x in пал.get("techniques") or [])))
print("схема: palette.scheme %s · заяви %s" % (пал.get("scheme"), [к for к in пр if к.startswith(("scheme", "base_"))]))
print("кодів style_rules %d, з визначенням %d" % (len(пр), sum(к in (П["task"].get("statement_codes") or {}) for к in пр)))

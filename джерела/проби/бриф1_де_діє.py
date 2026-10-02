"""БРИФ-1: де діє кожна заява, яку промпт складання більше не везе (`дріт_моделі.ЗАЯВИ_ДІЮТЬ_У_КОДІ`).
Кожне місце `pool:/judge:/explain:модуль.функція` перевіряється імпортом; заява — словником `внутрішня_мова.ЗАЯВИ`.
Аргументи (необов'язково): файли викликів стенда ПАКЕТ_V1_ОБРАЗИ_V1 — тоді ще style_rules ДО/ПІСЛЯ фільтра. Друкує факт."""
import importlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import дріт_моделі as Д, внутрішня_мова as ВМ
вади = []
for код, (прав, місця) in sorted(Д.ЗАЯВИ_ДІЮТЬ_У_КОДІ.items(), key=lambda кв: (str(кв[1][0]), кв[0])):
    if код.split("@")[0] not in ВМ.ЗАЯВИ:
        вади.append("заява поза ЗАЯВИ: " + код)
    for м in місця:
        вид, _, шлях = м.partition(":")
        if вид in ("pool", "judge", "explain"):
            мод, _, фн = шлях.rpartition(".")
            if not hasattr(importlib.import_module(мод), фн):
                вади.append("нема %s у %s" % (фн, мод))
    print("%-10s %-32s %s" % (прав or "—", код, " · ".join(місця)))
ст = {}
for к, (_, м) in Д.ЗАЯВИ_ДІЮТЬ_У_КОДІ.items():
    for в in {x.split(":")[0] for x in м}:
        ст[в] = ст.get(в, 0) + 1
print("заяв %d · за видом місця %s · вад %d %s" % (len(Д.ЗАЯВИ_ДІЮТЬ_У_КОДІ), ст, len(вади), вади))
кл = lambda з: next(iter(з)) if isinstance(з, dict) else з
for ф in sys.argv[1:]:
    т = open(ф, encoding="utf-8").read()
    П, _ = json.JSONDecoder().raw_decode(т[т.index("{"):])
    ст_ = П.get("style_rules") or []
    д = lambda x: len(json.dumps(x, ensure_ascii=False, separators=(",", ":")))
    стала = {к: v for к, v in П.items() if к != "pool"}
    print("%s: промпт %d симв. · стала частина %d · style_rules %d симв., %d заяв · statement_codes %d симв."
          % (os.path.basename(ф)[:24], д(П), д(стала), д(ст_), len(ст_), д(П["task"].get("statement_codes") or {})))
    print("   ", [кл(з) for з in ст_])

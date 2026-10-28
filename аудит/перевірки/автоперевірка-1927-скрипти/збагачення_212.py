"""Скільки записів збагачення несуть поверхню 2.12 (сегменти) і скільки з тоном невідомо."""
import gzip, json, sys, collections as К
д = json.load(gzip.open(sys.argv[1], "rt", encoding="utf-8"))
зап = д.get("записи", д) if isinstance(д, dict) else д
it = зап.values() if isinstance(зап, dict) else зап
л = К.Counter()
for з in it:
    if not isinstance(з, dict): continue
    л["всього"] += 1
    л["версія %s" % з.get("версія")] += 1
    if з.get("поверхня"): л["з поверхнею"] += 1
    к = з.get("колір_основний") or {}
    if "колір_тип" in к: л["колір_тип " + str(к["колір_тип"])] += 1
    if "тон невідомо" in str(з.get("поверхня") or ""): л["тон невідомо в поверхні"] += 1
print(dict(л))

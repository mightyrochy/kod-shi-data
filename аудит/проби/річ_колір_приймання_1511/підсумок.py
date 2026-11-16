"""Підсумок приймання 15.11 з ручних вердиктів `оцінки.tsv` і кодів `вибірка.tsv`. Вердиктів не ставить.

    python3 -I аудит/проби/річ_колір_приймання_1511/підсумок.py
"""
import collections, csv
from pathlib import Path

ТУТ = Path(__file__).resolve().parent
ПЕРШИЙ = ТУТ.parent / "річ_колір_розкид_очима_1411" / "вибірка.tsv"


def tsv(шлях):
    return list(csv.DictReader(open(шлях, encoding="utf-8"), delimiter="\t"))


оцінки, кадри = tsv(ТУТ / "оцінки.tsv"), tsv(ТУТ / "вибірка.tsv")
assert len(оцінки) == 40 and {о["номер"] for о in оцінки} == {к["номер"] for к in кадри}
за = collections.defaultdict(list)
for к in кадри:
    за[к["номер"]].append(к)
лік = collections.Counter(о["вердикт"] for о in оцінки)
print("речей 40, кадрів %d: правильних %d, межових %d, хибних %d (ціль ≥ 38 правильних)" % (
    len(кадри), лік["правильна"], лік["межова"], лік["хибна"]))
for в in ("хибна", "межова"):
    пр = collections.defaultdict(list)
    for о in оцінки:
        if о["вердикт"] == в:
            пр[о["причина"] or "—"].append(о["номер"])
    print("%s за причиною:" % в, "; ".join("%s %d (№%s)" % (п, len(н), ", ".join(н)) for п, н in
                                           sorted(пр.items(), key=lambda x: -len(x[1]))))
# код дав лише main: прогін #3315 кадру коду не дав, вікна main (#3405) дали
for в in ("правильна", "межова", "хибна"):
    н = [о["номер"] for о in оцінки if о["вердикт"] == в]
    лише = [x for x in н if all(к["код_прогону"] == "невідомо" for к in за[x])]
    print("%s: речей %d, з них код лише на main (прогін коду не дав у жодному кадрі) %d%s" % (
        в, len(н), len(лише), (" — №" + ", ".join(лише)) if лише else ""))
перші = {р["id"] for р in tsv(ПЕРШИЙ)}
спільні = sorted({к["id"] for к in кадри} & перші)
print("спільних речей з вибіркою зерна 20261114: %d%s" % (len(спільні), (" — " + ", ".join(спільні)) if спільні else ""))

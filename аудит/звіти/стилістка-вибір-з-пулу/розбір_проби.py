#!/usr/bin/env python3
"""Розбір проби (пункт 4): різні речі кожного слота за 20 запитів; чи не взяті за 20 разів збігаються з невзятими з пункту 2.
Вихід: проба-підсумок.json. Запуск з кореня: python3 -I аудит/звіти/стилістка-вибір-з-пулу/розбір_проби.py"""
import csv, gzip, json, math
from collections import Counter, defaultdict
from pathlib import Path
import importlib.util, sys
ТЕКА = Path(__file__).resolve().parent
ТЕКА_ = ТЕКА


def вілсон(k, n):
    z = 1.96
    if n == 0:
        return 0.0, 1.0
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def різниця(k1, n1, k2, n2):
    l1, u1 = вілсон(k1, n1); l2, u2 = вілсон(k2, n2); p1, p2 = k1 / n1, k2 / n2
    return p1 - p2, p1 - p2 - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), p1 - p2 + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def розібрати():
    пакет = ПР.запит_із_запису()
    cols = пакет["pool"]["cols"]
    пул = {r[0]: dict(zip(cols, r)) for r in пакет["pool"]["rows"]}
    рядки = [r for r in csv.DictReader(gzip.open(ТЕКА / "рядки.csv.gz", "rt", encoding="utf-8")) if r["запит"] == ПР.ЗАПИТ]
    слот_типу = Counter()
    for r in csv.DictReader(gzip.open(ТЕКА / "рядки.csv.gz", "rt", encoding="utf-8")):
        if r["слот"]:
            слот_типу[r["тип"], r["слот"]] += 1
    слот_за_типом = {}
    for (т, с), n in sorted(слот_типу.items(), key=lambda x: x[1]):
        слот_за_типом[т] = с
    ід_рядка = {r["n"]: r["ід"] for r in рядки}
    в_записі = {r["n"]: int(r["взято"]) for r in рядки}
    п2 = {r["ід"]: int(r["взято"]) for r in csv.DictReader((ТЕКА / "речі.csv").open(encoding="utf-8"))}
    запуски = []
    for ф in sorted((ТЕКА / "проба").glob("*.json")):
        o = json.loads(ф.read_text(encoding="utf-8"))
        try:
            в = ПР.П.розібрати_json(o["відповідь"])
            взято = [ПР.П.номер(x) for ou in в["outfits"] for x in ou["items"]]
            запуски.append(dict(сід=o["сід"], образів=len(в["outfits"]), взято=set(n for n in взято if n), поза_пулом=sum(n not in пул for n in взято if n), секунд=o["секунд"]))
        except Exception as е:
            запуски.append(dict(сід=o["сід"], помилка=repr(е)[:100], секунд=o["секунд"]))
    добрі = [з for з in запуски if "взято" in з]
    слот = lambda n: слот_за_типом.get(пул[n]["type"], "?")
    за_слотами = defaultdict(lambda: dict(у_пулі=0, різних_за_20=set(), в_запуску=[]))
    for n in пул:
        за_слотами[слот(n)]["у_пулі"] += 1
    for з in добрі:
        кількість = Counter(слот(n) for n in з["взято"] if n in пул)
        for с, k in кількість.items():
            за_слотами[с]["в_запуску"].append(k)
        з["взято"] = з["взято"] & set(пул)
        for n in з["взято"]:
            за_слотами[слот(n)]["різних_за_20"] |= {n}
    загалом = set().union(*(з["взято"] for з in добрі)) if добрі else set()
    частота = Counter(n for з in добрі for n in з["взято"])
    таблиця = {с: dict(у_пулі=v["у_пулі"], різних_за_20=len(v["різних_за_20"]), взято_за_запуск_сер=round(sum(v["в_запуску"]) / max(1, len(добрі)), 2))
               for с, v in sorted(за_слотами.items())}
    жодного = [n for n in пул if n not in загалом]
    невідомий_hex = lambda n: пул[n]["hex"] is None
    k1 = sum(невідомий_hex(n) for n in жодного); n1 = len(жодного)
    k2 = sum(невідомий_hex(n) for n in загалом); n2 = len(загалом)
    # збіг із записаними невзятими з п.2: серед речей цього запиту, що мають ід у когорті ≥5 показів
    когорта = {n: п2[ід_рядка[n]] for n in пул if ід_рядка.get(n) in п2}
    # Скільки зі «жодного за 20» мають когортний статус «не взято жодного разу» (п.2) і навпаки
    ніколи_20_і_ніколи_п2 = sum(1 for n, v in когорта.items() if n not in загалом and v == 0)
    ніколи_20_і_колись_п2 = sum(1 for n, v in когорта.items() if n not in загалом and v == 1)
    колись_20_і_ніколи_п2 = sum(1 for n, v in когорта.items() if n in загалом and v == 0)
    колись_20_і_колись_п2 = sum(1 for n, v in когорта.items() if n in загалом and v == 1)
    d = різниця(sum(невідомий_hex(n) for n in пул if n in загалом), len(загалом) or 1,
                sum(невідомий_hex(n) for n in пул if n not in загалом), len(жодного) or 1)
    вихід = dict(запит=ПР.ЗАПИТ, запусків=len(запуски), добрих=len(добрі), помилки=[з for з in запуски if "помилка" in з],
                 образів_за_запуск=[з["образів"] for з in добрі], у_пулі=len(пул), різних_за_20=len(загалом), жодного_за_20=len(жодного),
                 за_слотами=таблиця,
                 hex_невідомий_серед_взятих_хоч_раз=f"{sum(невідомий_hex(n) for n in загалом)}/{len(загалом)}",
                 hex_невідомий_серед_жодного_разу=f"{k1}/{n1}",
                 різниця_частки_невідомого_кольору_взяті_мінус_невзяті=[round(x, 3) for x in d],
                 у_пулі_з_когорти_п2=len(когорта),
                 перетин_з_п2=dict(ніколи_20_ніколи_п2=ніколи_20_і_ніколи_п2, ніколи_20_але_колись_п2=ніколи_20_і_колись_п2,
                                   колись_20_але_ніколи_п2=колись_20_і_ніколи_п2, колись_20_колись_п2=колись_20_і_колись_п2),
                 частота_топ=Counter({n: частота[n] for n in частота}).most_common(5),
                 у_запису_взято_в_цьому_запиті=sum(в_записі.values()))
    (ТЕКА / "проба-підсумок.json").write_text(json.dumps(вихід, ensure_ascii=False, indent=1, default=list) + "\n", encoding="utf-8")
    print(json.dumps(вихід, ensure_ascii=False, indent=1, default=list))


if __name__ == "__main__":
    розібрати()

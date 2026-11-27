#!/usr/bin/env python3
"""Пункти 1–3 виміру: чим відрізняються взяті речі від невзятих серед тих, що стилістка бачила щонайменше 5 разів.
Вхід: рядки.csv.gz і заяви.jsonl.gz (дані.py), ../крамниці-рівна-черга/вибір-речі.csv. Вихід: речі.csv, ознаки.csv, аналіз.json.
Запуск з кореня: python3 -I аудит/звіти/стилістка-вибір-з-пулу/аналіз.py"""
import csv, gzip, json, math, re, statistics
from collections import Counter, defaultdict
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
Z = 1.96
НЕВІД = ["н_L", "н_hex", "н_family", "н_fabric", "н_register", "н_cut", "н_length", "н_formality"]


def вілсон(k, n):
    if n == 0:
        return (0.0, 1.0)
    p = k / n; d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d; h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def різниця(k1, n1, k2, n2):
    """Різниця часток (група 1 мінус група 2) з довірчою межею Ньюкома."""
    if n1 == 0 or n2 == 0:
        return None
    l1, u1 = вілсон(k1, n1); l2, u2 = вілсон(k2, n2); p1, p2 = k1 / n1, k2 / n2
    return p1 - p2, p1 - p2 - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), p1 - p2 + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def hex_rgb(h):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", h or "")
    return tuple(int(m[1][i:i + 2], 16) for i in (0, 2, 4)) if m else None


def медіана(x):
    x = [v for v in x if v is not None]
    return statistics.median(x) if x else None


def головна(страта="слот"):
    речі_мітки = {r["ід"]: r for r in csv.DictReader((ТЕКА.parent / "крамниці-рівна-черга/вибір-речі.csv").open(encoding="utf-8"))}
    рядки = list(csv.DictReader(gzip.open(ТЕКА / "рядки.csv.gz", "rt", encoding="utf-8")))
    палітри = {}
    for р in map(json.loads, gzip.open(ТЕКА / "заяви.jsonl.gz", "rt", encoding="utf-8")):
        палітри[р["запит"]] = [rgb for a in р["палітра"] if (rgb := hex_rgb(a.split()[-1]))]
    за_ід = defaultdict(list)
    for r in рядки:
        if r["ід"]:
            за_ід[r["ід"]].append(r)
    речі = []
    for ід, rs in за_ід.items():
        м = речі_мітки.get(ід)
        if not м or int(м["однозначно_показано"]) < 5:
            continue
        взято = int(м["однозначно_взято"]) > 0
        слот = Counter(r["слот"] for r in rs).most_common(1)[0][0]
        відст = []
        for r in rs:
            c = hex_rgb(r["hex"]); п = палітри.get(r["запит"])
            if c and п:
                відст.append(min(math.dist(c, a) for a in п))
        ціни = [float(r["ціна"]) for r in rs if r["ціна"]]
        речі.append(dict(
            ід=ід, слот=слот, тип=Counter(r["тип"] for r in rs).most_common(1)[0][0], крамниця=м["крамниця"],
            показано=int(м["однозначно_показано"]), взято_разів=int(м["однозначно_взято"]), взято=int(взято),
            невідомо=round(statistics.mean(int(r["невідомо"]) for r in rs), 3),
            **{k: round(statistics.mean(int(r[k]) for r in rs), 3) for k in НЕВІД},
            назва=(rs[0]["назва_довж"] or None), опис=(rs[0]["опис_довж"] or None), фото=(rs[0]["фото"] or None),
            ціна=медіана(ціни), нейтральний=int(Counter(r["family"].startswith("neutral") for r in rs if r["family"]).most_common(1)[0][0]) if any(r["family"] for r in rs) else None,
            колір=Counter(r["колір"] for r in rs).most_common(1)[0][0],
            до_палітри=round(statistics.mean(відст), 1) if відст else None))
    for р in речі:
        for k in ("назва", "опис", "фото"):
            р[k] = int(р[k]) if р[k] is not None else None
    with (ТЕКА / (f"речі.csv" if страта=="слот" else "речі_тип.csv")).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(речі[0]), lineterminator="\n"); w.writeheader(); w.writerows(речі)

    слоти = Counter(р[страта] for р in речі)
    склад = {с: (sum(р["взято"] for р in речі if р["слот"] == с), n) for с, n in sorted(слоти.items())}
    # Ознаки: кожна — функція речі → рівень (рядок) або None. Пороги медіанні всередині слота.
    мед = {}
    for с in слоти:
        вибірка = [р for р in речі if р[страта] == с]
        мед[с] = {k: медіана(р[k] for р in вибірка) for k in ("невідомо", "назва", "опис", "ціна", "до_палітри")}

    def поділ(к):
        def f(р):
            v, m = р[к], мед[р[страта]][к]
            return None if v is None or m is None else ("вище медіани слота" if v > m else "не вище медіани слота")
        return f
    ознаки = {
        "невідомих полів у записі": поділ("невідомо"),
        "довжина назви": поділ("назва"),
        "довжина опису": поділ("опис"),
        "опис порожній": lambda р: None if р["опис"] is None else ("так" if р["опис"] == 0 else "ні"),
        "фото": lambda р: None if р["фото"] is None else ("немає" if р["фото"] == 0 else "є"),
        "кількість фото ≥ 3": lambda р: None if р["фото"] is None else ("так" if р["фото"] >= 3 else "ні"),
        "ціна": поділ("ціна"),
        "колір нейтральний": lambda р: None if р["нейтральний"] is None else ("так" if р["нейтральний"] else "ні"),
        "колір далекий від кольорів її палітри": поділ("до_палітри"),
        "колір у записі невідомий": lambda р: "так" if р["н_hex"] > 0.5 else "ні",
        "крій невідомий": lambda р: "так" if р["н_cut"] > 0.5 else "ні",
        "тканина невідома": lambda р: "так" if р["н_fabric"] > 0.5 else "ні",
        "довжина невідома": lambda р: "так" if р["н_length"] > 0.5 else "ні",
        "ошатність невідома": lambda р: "так" if р["н_formality"] > 0.5 else "ні",
        "регістр невідомий": lambda р: "так" if р["н_register"] > 0.5 else "ні",
        "яскравість невідома": lambda р: "так" if р["н_L"] > 0.5 else "ні",
    }
    рядки_ознак, підсумок = [], {}
    for назва, f in ознаки.items():
        # Порівняння «рівень проти решти» у кожному слоті, з'єднане вагами слотів.
        рівні = sorted({f(р) for р in речі} - {None})
        for рівень in рівні:
            числа = []
            for с in слоти:
                в = [р for р in речі if р[страта] == с and f(р) is not None]
                a = [р for р in в if f(р) == рівень]; b = [р for р in в if f(р) != рівень]
                if len(a) >= 5 and len(b) >= 5:
                    d = різниця(sum(р["взято"] for р in a), len(a), sum(р["взято"] for р in b), len(b))
                    числа.append((с, len(a), sum(р["взято"] for р in a), len(b), sum(р["взято"] for р in b), d))
                    рядки_ознак.append((назва, рівень, с, len(a), sum(р["взято"] for р in a), len(b), sum(р["взято"] for р in b),
                                        round(d[0], 4), round(d[1], 4), round(d[2], 4)))
            if not числа:
                continue
            # Зважена за слотами різниця й її межа (ваги — розміри слотів, дисперсія за Вілсоном/нормально).
            ваги = [a + b for _, a, _, b, _, _ in ((c[0], c[1], c[2], c[3], c[4], c[5]) for c in числа)]
            W = sum(ваги); середня = sum(w * c[5][0] for w, c in zip(ваги, числа)) / W
            дисп = 0
            for w, c in zip(ваги, числа):
                _, n1, k1, n2, k2, _ = c
                p1, p2 = (k1 + .5) / (n1 + 1), (k2 + .5) / (n2 + 1)
                дисп += (w / W) ** 2 * (p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
            пів = Z * math.sqrt(дисп)
            n_a = sum(c[1] for c in числа); k_a = sum(c[2] for c in числа); n_b = sum(c[3] for c in числа); k_b = sum(c[4] for c in числа)
            підсумок[f"{назва}: {рівень}"] = dict(різниця=round(середня, 4), нижня=round(середня - пів, 4), верхня=round(середня + пів, 4),
                                                   речей_з_ознакою=n_a, взято_з_ознакою=k_a, речей_решта=n_b, взято_решта=k_b,
                                                   слотів=len(числа))
    # Тип і крамниця — окремо, в межах усього когорти (слот і крамниця нестрого вкладені).
    за_типом = {}
    for t in sorted({р["тип"] for р in речі}):
        a = [р for р in речі if р["тип"] == t]
        if len(a) >= 15:
            за_типом[t] = (len(a), sum(р["взято"] for р in a), round(sum(р["взято"] for р in a) / len(a), 3))
    за_крамн = {}
    for t in sorted({р["крамниця"] for р in речі}):
        a = [р for р in речі if р["крамниця"] == t]
        if len(a) >= 15:
            за_крамн[t] = (len(a), sum(р["взято"] for р in a), round(sum(р["взято"] for р in a) / len(a), 3))
    # Скільки різниці між крамницями лишається після слота: очікувана частка за слотом проти фактичної.
    част_слота = {с: v[0] / v[1] for с, v in склад.items()}
    залишок = {}
    for t in за_крамн:
        a = [р for р in речі if р["крамниця"] == t]
        залишок[t] = round(sum(р["взято"] for р in a) - sum(част_слота[р[страта]] for р in a), 2)
    with (ТЕКА / ("ознаки.csv" if страта=="слот" else "ознаки_за_типом.csv")).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ознака", "рівень", "слот", "речей_з_ознакою", "взято_з_ознакою", "речей_решта", "взято_решта", "різниця", "нижня_межа", "верхня_межа"])
        w.writerows(рядки_ознак)
    всього = (len(речі), sum(р["взято"] for р in речі))
    (ТЕКА / ("аналіз.json" if страта=="слот" else "аналіз_за_типом.json")).write_text(json.dumps(dict(
        когорта=dict(речей=всього[0], взято=всього[1], не_взято=всього[0] - всього[1]),
        слоти=склад, ознаки=підсумок, за_типом=за_типом, за_крамницею=за_крамн, крамниця_мінус_очікуване_за_слотом=залишок),
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("страта:", страта, всього, len(склад), "страт")
    for k, v in sorted(підсумок.items(), key=lambda kv: -abs(kv[1]["різниця"]))[:25]:
        print(f"{v['різниця']:+.3f} [{v['нижня']:+.3f};{v['верхня']:+.3f}] {k} (з ознакою {v['взято_з_ознакою']}/{v['речей_з_ознакою']}, решта {v['взято_решта']}/{v['речей_решта']}, слотів {v['слотів']})")


if __name__ == "__main__":
    головна("слот")
    головна("тип")

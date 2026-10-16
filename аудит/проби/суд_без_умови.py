"""СУД-БЕЗ-УМОВИ (рядки 5224, 5225, 5228, 5314, 5315): скільки разів правило стоїть на образі без своєї умови.
Читає файли вердиктів (V3) і рахує по кожному образу кожного кроку (`етапи.виклики[].образи_кроку[].знахідки`)
спрацювання правила: «з умовою» — умова названа в записі того самого образу, «без» — нема. ПІСЛЯ правки
правило стоїть лише з умовою, тож «без» → 0, а «з умовою» лишається. Запуск: python3 суд_без_умови.py <файли>"""
import sys, json, collections

ЖЕСТИ = {"K-OUT-11", "K-OUT-19", "K-OUT-29", "K-OUT-32"}


def умова(п, зн, о, z_=None):
    """Чи має знахідка правила `п` свою умову серед знахідок `зн` того самого образу `о`."""
    пр = lambda r, f=lambda z: True: any(z.get("правило") == r and f(z) for z in зн)
    if п in ("K-OUT-11", "K-OUT-32", "K-OUT-34"):
        return пр("K-OUT-06", lambda z: z.get("сила") != "питання")
    if п == "K-OUT-42":
        return пр("K-OUT-41", lambda z: z.get("сила") == "strong")
    if п == "K-CRA-03":                       # жести, що лишаються після правки, — понад один
        return sum(1 for z in зн if z.get("правило") in ЖЕСТИ
                   and (z["правило"] in ("K-OUT-19", "K-OUT-29") or умова(z["правило"], зн, о))) > 1
    if п == "R-CHEV-08":                      # рядок 5314: умови заяви, слота й свідка
        мета, зони = о.get("_мета"), set(о.get("_зони") or ())
        коди = {x.get("code"): x.get("values") or {} for x in z_.get("заяви") or []}
        if any(k.endswith("goal_conceal") for k in коди) and мета != "приховати":
            ліч[("R-CHEV-08", "заява «мета — приховати» при іншій меті")] += 1
        слот = (о.get("слоти_ід") or {}).get((z_.get("речі") or [None])[0])
        if мета != "приховати" and "живіт" in зони and слот == "сумка" and "стегна" not in зони:
            return False                      # сумка не лежить на животі
        св = коди.get("item_draws_eye_by_itself_goal_conceal") or коди.get("item_draws_eye_by_itself_in_goal_zone")
        if св is not None and set(св.get("witnesses") or ()) == {"open_zone"} and зони \
                and not set(св.get("zones") or ()) & {ЗОНА.get(з, з) for з in зони}:
            return False                      # відкриває не зону мети
        return True
    return None


ЗОНА = {"живіт": "belly", "стегна": "hips", "руки": "arms", "груди": "chest", "плечі": "shoulders",
        "спина": "back", "ноги": "legs", "декольте": "neckline"}


ліч = collections.Counter()
for ф in sys.argv[1:]:
    д = json.load(open(ф, encoding="utf8"))
    for пр in д["прогони"]:
        па = dict(д.get("спільне") or {}, **(пр.get("спільне") or {})).get("паспорт") or {}
        for в in пр["вердикти"]:
            for к in ((в.get("етапи") or {}).get("виклики") or []):
                for о in (к.get("образи_кроку") or []):
                    зн = [z for z in (о.get("знахідки") or []) if isinstance(z, dict)]
                    о = dict(о, _мета=па.get("мета"), _зони=па.get("мета_зони"),
                             слоти_ід=dict(zip(о.get("ід") or [], [(о.get("слоти_н") or {}).get(н) for н in о.get("речі_н") or []])))
                    for z in зн:
                        п = z.get("правило")
                        if z.get("сила") == "питання":
                            continue
                        у = умова(п, зн, о, z)
                        if у is not None:
                            ліч[(п, "з умовою" if у else "без умови")] += 1
for (п, с), н in sorted(ліч.items()):
    print("%-9s %-10s %d" % (п, с, н))

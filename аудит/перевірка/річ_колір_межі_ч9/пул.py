# -*- coding: utf-8 -*-
"""Каталог ДО → ПІСЛЯ для зміненої поведінки (`палітра_запити.перетин_дуг`): рядки `запит_у_фід` обох дерев
(вихід `вимір.py`) і точки каталогу (знімок 05.11), що влучають у вікна кожного слота (`фід_добір.підходить`,
без слова й зони — лише точка). Друкує: специфікацій і рядків, які рядки різні й чим, пул слотів ДО → ПІСЛЯ
(речей увійшло / вийшло) і де на дузі стоїть тон кожної речі, що перейшла.
Запуск з джерела/: python3 ../аудит/перевірка/річ_колір_межі_ч9/пул.py <до.json.gz> <після.json.gz>"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.getcwd())
import warnings; warnings.filterwarnings("ignore")
import фід_добір as ФД, colorspace as cs, колір_тон as КТ

ТУТ = os.path.dirname(os.path.abspath(__file__))
до, після = (json.load(gzip.open(ш, "rt", encoding="utf-8"))["запит_у_фід"] for ш in sys.argv[1:3])
with gzip.open(os.path.join(ТУТ, "..", "річ_колір_межі_тон_20261105", "каталог_точки.json.gz"), "rt", encoding="utf-8") as ф:
    ТОЧКИ = [(р[0], tuple(р[1])) for р in json.load(ф) if р[1] is not None]
рядків_до, рядків_після, різних_рядків = 0, 0, 0
зс, зникли, з_ялись = collections.defaultdict(list), [], []
for а, б in zip(до, після):
    рядків_до += len(а); рядків_після += len(б)
    if а == б:
        continue
    # рядок без тону рядка (кінці дуги й дуга до обрізання) — ключ; однаковий ключ ДО і ПІСЛЯ — той самий рядок
    ключ = lambda q: json.dumps({к: в for к, в in q.items() if к not in ("h_from", "h_to")}, sort_keys=True, ensure_ascii=False)
    ба = collections.defaultdict(list); бб = collections.defaultdict(list)
    for q in а: ба[ключ(q)].append(q)
    for q in б: бб[ключ(q)].append(q)
    for к in set(ба) | set(бб):
        xs, ys = ба.get(к, []), бб.get(к, [])
        for x, y in zip(xs, ys):
            if x != y:
                різних_рядків += 1
                for п in ("h_from", "h_to"):
                    зс[п].append(round(КТ.різниця_на_колі(y[п], x[п]), 1))
        зникли += xs[len(ys):]; з_ялись += ys[len(xs):]
print("специфікацій: %d; рядків ДО %d → ПІСЛЯ %d; змінено кінці дуги: %d, зникло рядків: %d, з'явилось: %d"
      % (len(до), рядків_до, рядків_після, різних_рядків, len(зникли), len(з_ялись)))
for п, ds in sorted(зс.items()):
    print("  %s ПІСЛЯ − ДО (° CIELAB): мін %+.1f, макс %+.1f, медіана %+.1f" % (п, min(ds), max(ds), sorted(ds)[len(ds) // 2]))
for q in зникли[:5]:
    print("  зник: %s" % {к: q.get(к) for к in ("слот", "h_from", "h_to", "дуга_до_обрізання", "джерело_тону", "роль")})
print("  зниклі: h_from == h_to — %d з %d" % (sum(q.get("h_from") == q.get("h_to") for q in зникли), len(зникли)))
for q in з_ялись[:3]:
    print("  з'явився: %s" % {к: q.get(к) for к in ("слот", "h_from", "h_to", "дуга_до_обрізання", "джерело_тону", "роль")})
print("  зниклі й нові за (слот, джерело, дуга до обрізання): %s" % sorted(collections.Counter(
    (q.get("слот"), q.get("джерело_тону"), str(q.get("дуга_до_обрізання")), q.get("h_from"), q.get("h_to"), "зник" if q in зникли else "новий")
    for q in зникли + з_ялись).items())[:8])

# пул слота = точки, що влучають хоч в одне вікно слота (вікна слота — диз'юнкція)
КЕШ = {}
def влучання(q):
    """Точки каталогу у вікні рядка `q` (кеш за рядком: ті самі вікна повторюються між якорями)."""
    к = json.dumps(q, sort_keys=True, ensure_ascii=False)
    if к not in КЕШ:
        КЕШ[к] = frozenset(ід for ід, lab in ТОЧКИ if ФД.підходить(lab, q))
    return КЕШ[к]

def пули(запити, слоти):
    п = collections.defaultdict(set)
    for q in запити:
        if isinstance(q, dict) and q.get("L_min") is not None and q.get("слот") in слоти:
            п[q.get("слот")] |= влучання(q)
    return п
ТОЧКИ_Д = dict(ТОЧКИ)
увійшло, вийшло, пулів, пулів_змінено, речей_до, речей_після = 0, 0, 0, 0, 0, 0
де = collections.Counter()
for а, б in zip(до, після):
    if а == б:
        continue
    слоти = {q.get("слот") for q in а if q not in б} | {q.get("слот") for q in б if q not in а}
    па, пб = пули(а, слоти), пули(б, слоти)
    for с in set(па) | set(пб):
        пулів += 1
        x, y = па.get(с, set()), пб.get(с, set())
        речей_до += len(x); речей_після += len(y)
        if x != y:
            пулів_змінено += 1
        увійшло += len(y - x); вийшло += len(x - y)
        for ід in (y - x) | (x - y):
            lab = ТОЧКИ_Д[ід]
            h = cs.lch(lab)[2]
            # відстань тону речі до найближчого краю вікна ПІСЛЯ, що змінилось
            краї = [q[п] for q in б if isinstance(q, dict) and q.get("слот") == с and q.get("h_from") is not None
                    for п in ("h_from", "h_to")]
            d = min(КТ.відстань_тонів(h, к) for к in краї) if краї else None
            де[("увійшла" if ід in y else "вийшла", None if d is None else min(int(d), 3))] += 1
print("пулів слотів зі зміненими рядками: %d, змінено: %d; речей у пулах ДО %d → ПІСЛЯ %d (увійшло %d, вийшло %d)"
      % (пулів, пулів_змінено, речей_до, речей_після, увійшло, вийшло))
for (к, d), n in sorted(де.items(), key=str):
    print("  %s: тон за %s° від краю вікна ПІСЛЯ — %d" % (к, "≥3" if d == 3 else "<%d" % (d + 1) if d is not None else "?", n))

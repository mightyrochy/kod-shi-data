# -*- coding: utf-8 -*-
"""Е3-одна-величина ч37: звідки частка площі, яку читає `колір_світлота.межі_частки` (усі читачі `частка_понад`), на
стенді образів ч33/ч36 — 60 образів (зерно 33) × тіла 155/165/175, живий шлях `суд_від_моделі.перевірити_від_моделі`.
Журнал кожного читання: джерело частки (`джерело_площі`), число, поріг, читач (функція над `частка_понад`).
    python3 аудит/проби/Е3_ч37_похибка_частки/читання.py --кеш /tmp/кеш.pkl                 # код main / цієї гілки
    python3 аудит/проби/Е3_ч37_похибка_частки/читання.py --кеш /tmp/кеш.pkl --код /tmp/ч36/джерела   # читачі ч36
Прогноз для ч36: скільки з 180 пар (образ × тіло) мали б «так/ні» у читача, якби запис похибки мало джерело
`--джерело` (типово «піксель» — єдине, чий повтор міряє `кадри.py`): пара — коли кожне читання цього читача в ній
має це джерело, а межі частки не перетинають порога."""
import sys, pathlib, os, io, contextlib, json, random, pickle, collections, warnings; warnings.simplefilter("ignore")
КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
арг = lambda і, т=None: sys.argv[sys.argv.index(і) + 1] if і in sys.argv else т
код = pathlib.Path(арг("--код", КОРІНЬ / "джерела")).resolve(); кеш = арг("--кеш"); дж = арг("--джерело", "піксель")
os.chdir(код); sys.path.insert(0, str(код))
import feed as Ф, bridge as B, fit as ПС, суд_від_моделі as СМ, колір_світлота as КС
if not (кеш and pathlib.Path(кеш).exists()):   # той самий кеш, що в `Е3_ч33_частка.py` і `Е3_ч36_читачі.py`
    вх = json.load(open(код / "стенд_вх.json", encoding="utf-8")); вх.update(гілка=0)
    вх["каталог"] = Ф.каталог_на_диску(str(КОРІНЬ / "джерела" / "каталог_повний.xml"))
    with contextlib.redirect_stdout(io.StringIO()): B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    кеш and pickle.dump(B.каталог_останнього_пакета(), open(кеш, "wb"))
кат = pickle.load(open(кеш, "rb")) if кеш else B.каталог_останнього_пакета()
F = B._збірка(json.load(open(код / "стенд_вх.json", encoding="utf-8")))[0]
с = random.Random(33); за = lambda *сл: [c for c in кат if c.get("слот") in сл]
верх, низ, сукні, взуття, сумки = за("верх"), за("низ"), за("сукня", "комплект"), за("взуття"), за("сумка")
образи = [[с.choice(верх), с.choice(низ), с.choice(взуття), с.choice(сумки)] if і % 2 else
          [с.choice(сукні), с.choice(взуття), с.choice(сумки)] for і in range(60)]
_межі, журнал, пара = КС.межі_частки, [], [None]


def межі(e):
    """Обгортка точки: записує читання (джерело, число, поріг, читач) і віддає відповідь самої точки."""
    р, ф, поріг = _межі(e), sys._getframe(1), None
    if ф.f_code.co_name == "частка_понад":
        поріг, ф = ф.f_locals.get("поріг"), ф.f_back
    журнал.append((пара[0], "%s.%s" % (pathlib.Path(ф.f_code.co_filename).stem, ф.f_code.co_name), поріг,
                   e.get("джерело_площі") or ("—" if e.get("площа") is None else "без джерела"), e.get("площа"),
                   р if isinstance(р, str) or р is None else "межі"))
    return р


КС.межі_частки = межі
for зр in (155, 165, 175):
    тіло = ПС.тіло(зр, dict(плечі=98, груди=92, талія=74, стегна=100))
    for і, о in enumerate(образи):
        пара[0] = (і, зр)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            СМ.перевірити_від_моделі([r["id"] for r in о], F, кат, тіло, сценарій=dict(погода=dict(t=18)))
print("код: %s\nчитань частки: %d на %d парах (образ × тіло)" % (код, len(журнал), len({з[0] for з in журнал})))
print("читач · поріг · джерело · відповідь точки: читань (пар)")
лік = collections.defaultdict(set); n = collections.Counter()
for п, хто, поріг, джерело, _ч, р in журнал:
    к = (хто, поріг, джерело, р); n[к] += 1; лік[к].add(п)
for к in sorted(n, key=lambda к: -n[к]):
    print("  %s · %s · %s · %s: %d (%d)" % (*к, n[к], len(лік[к])))
числа = collections.Counter((з[3], round(з[4], 3)) for з in журнал if з[3] == "без джерела")
print("частки «без джерела» (заглушка `композитор_річ.у_річ` 1/N): %s" % dict(числа.most_common(5)))
print("прогноз (запис похибки лише в джерела «%s»): пар із «так/ні» у читача, зі 180:" % дж)
for хто in sorted({з[1] for з in журнал}):
    пари = collections.defaultdict(list)
    for з in журнал:
        if з[1] == хто: пари[з[0]].append(з[3])
    print("  %s: %d (пар із читанням %d; з них усі читання — «%s»: %d)"
          % (хто, sum(1 for v in пари.values() if all(x == дж for x in v)), len(пари), дж,
             sum(1 for v in пари.values() if all(x == дж for x in v))))

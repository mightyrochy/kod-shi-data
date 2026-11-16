# -*- coding: utf-8 -*-
"""Е3-одна-величина ч33 (п.6): частка площі без похибки — «невідомо» за будь-якого джерела; `одна_на_річ` без `>`.
Каталог `каталог_повний` (розпакований у `джерела/`), образи живим шляхом `суд_від_моделі.перевірити_від_моделі` на тілах
155/165/175 см; друкує лічбу (правило, сила) усіх знахідок і звірку полів речі з кількох колірних записів `outfit.елементи`.
    python3 аудит/проби/Е3_ч33_частка.py [--кеш /tmp/кеш.pkl]   # ПІСЛЯ;  --код /tmp/до/джерела — ДО"""
import sys, pathlib, os, io, contextlib, json, random, pickle, collections, warnings; warnings.simplefilter("ignore")
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
арг = lambda і, т=None: sys.argv[sys.argv.index(і) + 1] if і in sys.argv else т
код = pathlib.Path(арг("--код", КОРІНЬ / "джерела")).resolve(); кеш = арг("--кеш"); N = int(арг("--образів", 60))
os.chdir(код); sys.path.insert(0, str(код))
import feed as Ф, bridge as B, fit as ПС, outfit as O, суд_від_моделі as СМ
вх = json.load(open(код / "стенд_вх.json", encoding="utf-8")); вх.update(гілка=0)
if not (кеш and pathlib.Path(кеш).exists()):   # каталог мостом один раз, далі — кеш (той самий для ДО й ПІСЛЯ)
    вх["каталог"] = Ф.каталог_на_диску(str(КОРІНЬ / "джерела" / "каталог_повний.xml"))
    with contextlib.redirect_stdout(io.StringIO()): B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    кеш and pickle.dump(B.каталог_останнього_пакета(), open(кеш, "wb"))
кат = pickle.load(open(кеш, "rb")) if кеш else B.каталог_останнього_пакета()
F = B._збірка(json.load(open(код / "стенд_вх.json", encoding="utf-8")))[0]
с = random.Random(33); за = lambda *сл: [c for c in кат if c.get("слот") in сл]
верх, низ, сукні, взуття, сумки = за("верх"), за("низ"), за("сукня", "комплект"), за("взуття"), за("сумка")
образи = [[с.choice(верх), с.choice(низ), с.choice(взуття), с.choice(сумки)] if і % 2 else
          [с.choice(сукні), с.choice(взуття), с.choice(сумки)] for і in range(N)]
лог, _ел = [], O.елементи; лік, поля, речей = collections.Counter(), collections.Counter(), collections.Counter()
O.елементи = lambda *а, **к: (лог.append(_ел(*а, **к)) or лог[-1])
зн = lambda x: ([(x["правило"], x.get("сила"))] if isinstance(x, dict) and isinstance(x.get("правило"), str) and "сила" in x
               else []) + [п for v in (x.values() if isinstance(x, dict) else x if isinstance(x, list) else []) for п in зн(v)]
КОЛІР = {"lab", "hex", "колір_тип", "колір_не_вимір", "L", "C", "h", "rel_C", "гучний", "сім_я", "нейтраль", "гучність_межі",
         "сім_я_межі", "площа"}
for зр in (155, 165, 175):
    тіло = ПС.тіло(зр, dict(плечі=98, груди=92, талія=74, стегна=100))
    for о in образи:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            лік.update(set(зн(СМ.перевірити_від_моделі([r["id"] for r in о], F, кат, тіло, сценарій=dict(погода=dict(t=18))))))
for E in лог:
    for річ, n in collections.Counter(e["річ"] for e in E).items():
        зап = [e for e in E if e["річ"] == річ]; речей["записів 1" if n == 1 else "записів 2+"] += 1
        поля.update(к for к in зап[0] if к not in КОЛІР and any(repr(e.get(к)) != repr(зап[0].get(к)) for e in зап))
print(f"код: {код}\nобразів {N} × тіл 3; речей у викликах елементи(): {dict(речей)}; поля речі, що різняться між її записами "
      f"(крім кольору й площі): {dict(поля) or 0}\nлічба (правило, сила) по образах × тілах:")
print("\n".join("  %s · %s: %d" % (к[0], к[1], лік[к]) for к in sorted(лік, key=str)))

# -*- coding: utf-8 -*-
"""Рядок 196 (після приймання): та сама пара, що дісталась руці 1 в офіс із «без
підборів» — ж-11380 theoriginals (крамниця пише 13) і човники welfare ж-12402
(8.5). Що з ними робили ДО (модулі `фід_взуття`/`feed` з main, git show у
тимчасову теку) і ПІСЛЯ: яку висоту бачить код, чи знімає пару сенсорне вето
(`profile.СЕНСОРНІ`, K-PER-05) і чи вона вища за стелю каблука (K-SHO-16
`каблук_смуга_низ`). Запуск із `джерела`:
PYTHONPATH=. python3 проби/veto_bez_pidboriv_196b.py"""
import subprocess, sys, tempfile, os
if len(sys.argv) == 1:
    тека = tempfile.mkdtemp()
    for ф in ("фід_взуття.py", "feed.py"):
        open(os.path.join(тека, ф), "wb").write(subprocess.check_output(["git", "show", "origin/main:джерела/" + ф]))
    subprocess.run([sys.executable, __file__, тека], check=True)
    sys.argv.append("")
sys.path.insert(0, sys.argv[1] or "."); М = "ДО   " if sys.argv[1] else "ПІСЛЯ"
import feed as Ф, profile as П, аксесуари_реєстр as АР
offers, _ = Ф.читати_yml(Ф.каталог_на_диску())
СТЕЛЯ = АР.C["каблук_смуга_низ"]
висота = getattr(Ф, "висота_або_підлога", lambda r: r.get("каблук_см"))
for o in [x for x in offers if x["id"].startswith(("ж-11380@", "ж-12402@"))]:
    п = Ф._взуттєві_поля(o, Ф.тип_речі(o))
    р = dict(слот="взуття", id=o["id"], назва=o["назва"], каблук=п.get("каблук"),
             каблук_см=п.get("каблук_см"), каблук_від=п.get("каблук_від"))
    _, знято = П.жорстке_ні_фільтр([р], ["без підборів"])
    h = висота(р)
    print("%s · %s «%s»\n        поле крамниці: %s · каблук_см=%s · каблук=%s"
          "\n        вето «без підборів»: %s · вища за стелю %.0f см: %s"
          % (М, o["id"], str(o["назва"])[:44],
             {k: v for k, v in (o.get("параметри") or {}).items() if "підбор" in k.lower() or "каблук" in k.lower()},
             п.get("каблук_см"), п.get("каблук"), "знято" if знято else "ЛИШАЄТЬСЯ", СТЕЛЯ,
             "не знати (висоти нема)" if h is None else ("так" if h >= СТЕЛЯ else "ні")))

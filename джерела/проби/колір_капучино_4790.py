# -*- coding: utf-8 -*-
"""Рядок 4790: «капучино» — окреме слово лексикону (вікно вжитку), а не ключ «графіт». Проганяє весь
`каталог_повний.xml` двічі — лексиконом бази (git `main`, `verify.py`) і чинним — і друкує, скільки речей
змінили код кольору (`дріт_моделі.колір_код`) і слово `колір_назва`; з `-ф ШЛЯХ` пише перелік «id: ДО → ПІСЛЯ»
(колір_назва, код). Окремо: шість речей рядка 4790 і бомбер ж-05085@brenda.ua (рядок 3459а).
Запуск: cd джерела && gunzip -c ../каталог_повний.xml.gz > каталог_повний.xml && python3 проби/колір_капучино_4790.py [-ф файл]"""
import json, os, subprocess, sys, types
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
БАЗА = os.environ.get("БАЗА", "origin/main")
def прогін(стара):
    for ім in (("verify", "внутрішня_мова") if стара else ()):   # лексикон і таблиця кодів бази
        м = types.ModuleType(ім); м.__file__ = os.path.join(ТУТ, ім + ".py")
        exec(compile(subprocess.run(["git", "show", БАЗА + ":джерела/" + ім + ".py"], capture_output=True, text=True, check=True).stdout, м.__file__, "exec"), м.__dict__)
        sys.modules[ім] = м
    import feed, фід_каталог as FK, дріт_моделі as ДМ
    return {r["id"]: (r.get("колір_назва"), ДМ.колір_код(r.get("колір_назва"))[0], r.get("колір_hex")) for r in FK._прочитати_каталог(feed.каталог_на_диску(), 0)["каталог"]}
if "--дамп" in sys.argv:
    json.dump(прогін(sys.argv[-1] == "стара"), sys.stdout, ensure_ascii=False); sys.exit()
дамп = lambda к: json.loads(subprocess.run([sys.executable, __file__, "--дамп", к], capture_output=True, text=True, check=True).stdout)
до, після = дамп("стара"), дамп("нова")
зм = sorted(і for і in після if і in до and до[і][:2] != після[і][:2])
зм_код = [і for і in зм if до[і][1] != після[і][1]]
print("ФАКТ · речей %d; змінили слово кольору або код %d, з них код %d" % (len(після), len(зм), len(зм_код)))
ф = sys.argv[sys.argv.index("-ф") + 1] if "-ф" in sys.argv else None
if ф: open(ф, "w", encoding="utf-8").write("".join("%s: %s [%s] → %s [%s]\n" % (і, до[і][0], до[і][1], після[і][0], після[і][1]) for і in зм))
for і in ("ж-02244@maxa.ua", "ж-02639@sunwin-store.com", "ж-02716@sunwin-store.com", "ж-08158@attico.ua", "ж-08209@attico.ua", "ж-09676@attico.ua", "ж-05085@brenda.ua"):
    print("  %-28s ДО %s ПІСЛЯ %s" % (і, до.get(і), після.get(і)))

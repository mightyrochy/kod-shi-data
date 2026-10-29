# -*- coding: utf-8 -*-
"""Відтворення перевірки #2221 у тимчасовому дереві заданої голови.

Запуск: python аудит/перевірки/автоперевірка-2221-проба.py <тимчасове_дерево>
Таблиця в тимчасовому дереві відновлюється навіть після помилки.
"""
import collections
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

дерево = Path(sys.argv[1]).resolve()
голова = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=дерево, text=True).strip()
assert голова == "50db75e8e56f52249c0a0146eaa14ff0640143c0", голова
os.chdir(дерево / "джерела")
sys.path.insert(0, str(Path.cwd()))
import feed
import verify as V
import фід_каталог as FK
from фід_фото import файл_фото

проба = Path("проби/vikna_vzhytku.py").resolve()
база = subprocess.check_output(
    ["git", "merge-base", голова, "ae7aa01cd52056bf432e75afaaee71f7e372c509"],
    text=True).strip()
код_до = subprocess.check_output(
    ["git", "show", база + ":джерела/проби/vikna_vzhytku.py"], encoding="utf-8")
простір = {"__file__": str(проба), "__name__": "__main__"}
sys.argv = [str(проба)]
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(код_до, str(проба), "exec"), простір)
print("ДО: точок", sum(map(len, простір["т"].values())), flush=True)
print("ДО: слів таблиці поза методом", len({
    к for к in set(V.ВЖИТОК) | set(простір["нові"])
    if V.ВЖИТОК.get(к) != простір["нові"].get(к)}), flush=True)

таблиця = Path("verify.py")
початкові_байти = таблиця.read_bytes()
початкова_таблиця = V.ВЖИТОК
try:
    sys.argv = [str(проба), "--записати"]
    друк = io.StringIO()
    with contextlib.redirect_stdout(друк):
        після = runpy.run_path(str(проба), run_name="__main__")
    таблиця.write_bytes(початкові_байти)
    for рядок in друк.getvalue().splitlines():
        if "точки й відсів" in рядок or рядок.startswith("ЗАПИСАНО"):
            print(рядок, flush=True)
    інші = sorted(к for к in set(V.ВЖИТОК) | set(після["нові"])
                  if V.ВЖИТОК.get(к) != після["нові"].get(к))
    print("ПІСЛЯ: відмінних слів чинної таблиці", len(інші), інші, flush=True)
    print("ПІСЛЯ: жнив", len(після["зб"]), "із поверхнею",
          sum(bool(z.get("поверхня")) for z in після["зб"].values()), flush=True)
    for ід in ("ж-06805@dolcedonna.com.ua", "ж-04676@wearme.ua"):
        o = next(o for o in після["оф"] if o["id"].split("@")[0] == ід.split("@")[0])
        z = після["зб"][o["id"]]
        вар = після["FV"].варіант_кадру(o, після["сестри"])
        if not вар:
            print("СВІДОК:", o["id"], "варіант невідомий; не точка", flush=True)
            continue
        ск = V.слово_крамниці(вар["слово"])
        print("СВІДОК:", o["id"], "варіант", вар["слово"], "джерело", вар["джерело"],
              "у вікні", файл_фото(z["фото"]) in після["т"].get(ск["ім"], {}),
              "hex", z["колір_основний"].get("hex"), flush=True)

    # Один каталог і той самий код: із чинною та перерахованою таблицею.
    до = {r["id"]: r for r in FK.прочитати_каталог(feed.каталог_на_диску(), 0)["каталог"]}
    Path(os.environ["TEMP"], "2221_catalog_before.json").write_text(
        json.dumps(до, ensure_ascii=False, default=str), encoding="utf-8")
    print("КАТАЛОГ ДО: записів", len(до), flush=True)
    V.ВЖИТОК = після["нові"]
    піс = {r["id"]: r for r in FK.прочитати_каталог(feed.каталог_на_диску(), 0)["каталог"]}
    Path(os.environ["TEMP"], "2221_catalog_after.json").write_text(
        json.dumps(піс, ensure_ascii=False, default=str), encoding="utf-8")
    змінені = [і for і in до if до[і] != піс[і]]
    переходи = collections.Counter((до[і].get("джерело_кольору"),
                                    піс[і].get("джерело_кольору")) for і in змінені)
    print("КАТАЛОГ: записів", len(до), "змінено", len(змінені), "переходи", dict(переходи), flush=True)
    for і in змінені:
        print("ЗМІНА:", і, до[і].get("lab"), "→", піс[і].get("lab"),
              до[і].get("джерело_кольору"), "→", піс[і].get("джерело_кольору"), flush=True)
finally:
    V.ВЖИТОК = початкова_таблиця
    таблиця.write_bytes(початкові_байти)
    print("Тимчасову таблицю відновлено побайтово", flush=True)

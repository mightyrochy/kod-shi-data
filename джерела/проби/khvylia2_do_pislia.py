# -*- coding: utf-8 -*-
"""Хвиля 2, вимір «було → стало» на каталозі (п.4 наряду): скільки речей дістає кожне виправлене слово,
чи стала точка речі ближчою до виміру з фото, у кого з сусідів поменшало і чи ҐРАТКА ОСНОВ побайтово та
сама. ДО — verify з бази гілки (git show), ПІСЛЯ — чинний; каталог_повний. Одиниця тут — РІЧ каталогу
(рішення коду), на відміну від вибірки вікон, де одиниця — дизайн.
Запуск: cd джерела && python3 проби/khvylia2_do_pislia.py [база, типово origin/main]"""
import collections as К, subprocess, statistics as st, sys, types
sys.path.insert(0, ".")
import bridge, feed, фід_каталог as FK, фід_збагачення as FZ, verify as V, colorspace as cs
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
ДЖ = subprocess.run(["git", "show", "%s:джерела/verify.py" % БАЗА], capture_output=True, text=True, check=True).stdout
def прочитати(модуль):
    FK.V = FZ.V = модуль
    return {r["id"]: r for r in FK._прочитати_каталог("каталог_повний.xml", 0)["каталог"]}
до_V = types.ModuleType("verify"); до_V.__file__ = V.__file__; exec(ДЖ, до_V.__dict__)
до = прочитати(до_V); ґр_до = bridge._ґратка_основ()[0]
FK.V = FZ.V = V; після = прочитати(V); ґр_після = bridge._ґратка_основ()[0]
зб = feed.читати_збагачення()
# вимір з фото беремо тим самим правилом, що вікна: hex жнив v2, ПІДТВЕРДЖЕНИЙ свідком (#314)
не_вимір = lambda z, k: not k.get("hex") or (z.get("версія") or 1) < 2 or not FZ.колір_збагачення(z)[2].startswith("hex")
сл_до, сл_після = К.Counter(), К.Counter()
for i, r in після.items():
    сл_після[r.get("колір_ім")] += 1; сл_до[до[i].get("колір_ім")] += 1
змін = {с for с in set(сл_до) | set(сл_після) if с and сл_до[с] != сл_після[с]}
print("ФАКТ · слова, у яких змінилась кількість речей каталогу: %s" % (
      sorted(((сл_до[с], сл_після[с], с) for с in змін), key=lambda t: t[0] - t[1]) or "жодного"))
for с in sorted(змін, key=lambda с: сл_після[с] - сл_до[с], reverse=True):
    речі = [i for i, r in після.items() if r.get("колір_ім") == с and до[i].get("колір_ім") != с]
    пари = []
    for i in речі:
        z = зб.get(i) or {}; k = z.get("колір_основний") or {}
        if не_вимір(z, k) or not до[i].get("lab") or not після[i].get("lab"): continue
        пари.append((до[i]["lab"], після[i]["lab"], cs.hx(k["hex"])))
    if not пари: print("  %-14s речей %3d → %3d · виміру з фото на них нема" % (с, сл_до[с], сл_після[с])); continue
    д = [cs.de00(tuple(a), h) for a, _, h in пари]; п = [cs.de00(tuple(b), h) for _, b, h in пари]
    print("  %-14s речей %3d → %3d · ΔE00 точки до виміру на %d речах: медіана %.1f → %.1f, ближче стало %d" % (
          с, сл_до[с], сл_після[с], len(пари), st.median(д), st.median(п), sum(1 for x, y in zip(д, п) if y < x - 0.1)))
print("ФАКТ · ґратка основ: %s (%d чипів до, %d після)" % (
      "ПОБАЙТОВО ТА САМА" if ґр_до == ґр_після else "ЗМІНИЛАСЬ: " + str([a for a, b in zip(ґр_до, ґр_після) if a != b][:6]),
      len(ґр_до), len(ґр_після)))

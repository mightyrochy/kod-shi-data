# -*- coding: utf-8 -*-
"""Рядки 5663, 6630 (п.18): вибірка очима — 40 речей, що змінили колір відносно гілки ДО (типово origin/main):
точка ↔ вікно, інший hex точки чи інший код слова виміру. Каталог ДО будується в тимчасовому git worktree на тому
самому `каталог_повний.xml`. Друкує лічбу змін за родом і 40 рядків (сід 5663): id, слово крамниці, ДО → ПІСЛЯ, кадр.
Запуск: cd джерела && python3 -W ignore проби/вікна_5663_вибірка.py [ГІЛКА_ДО] [сід]"""
import collections, gzip, json, os, random, subprocess, sys, tempfile
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
ДО, СІД = (sys.argv[1:] + ["origin/main"])[0], int((sys.argv[2:] + ["5663"])[0])
ЗНІМОК = ("import json, feed, фід_каталог as FK; print(json.dumps({r['id']: [r.get('колір_hex_фото'), r.get('колір_назва_фото'),"
          " r.get('колір_назва_крамниці') or r.get('колір_назва'), r.get('слот')] for r in FK._прочитати_каталог("
          "feed.каталог_на_диску(), 0)['каталог']}, ensure_ascii=False))")
def знімок(тека):
    вих = subprocess.run([sys.executable, "-W", "ignore", "-c", ЗНІМОК], cwd=тека, capture_output=True, text=True, check=True)
    return json.loads(вих.stdout.strip().splitlines()[-1])
with tempfile.TemporaryDirectory() as т:
    subprocess.run(["git", "worktree", "add", "-q", "--detach", т, ДО], check=True)
    try:
        os.symlink(os.path.join(ТУТ, "каталог_повний.xml"), os.path.join(т, "джерела", "каталог_повний.xml"))
        до = знімок(os.path.join(т, "джерела"))
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", т], check=True)
піс, зб = знімок(ТУТ), json.load(gzip.open("каталог_збагачення.json.gz"))
def рід(а, б):
    if bool(а[0]) != bool(б[0]):
        return "точка → вікно" if а[0] else "вікно → точка"
    return "інший hex точки" if а[0] != б[0] else "інший код виміру" if а[0] and а[1] != б[1] else None
зм = {і: рід(до[і], піс[і]) for і in піс if і in до}
зм = {і: р for і, р in зм.items() if р}
print("ФАКТ · ДО %s; змінили колір %d з %d: %s" % (ДО, len(зм), len(піс), dict(collections.Counter(зм.values()))))
for н, і in enumerate(sorted(random.Random(СІД).sample(sorted(зм), min(40, len(зм)))), 1):
    а, б = до[і], піс[і]
    print("%2d %-32s %-11s крамниця «%s» %s %s → %s %s · %s" % (н, і, б[3], б[2], а[0] or "вікно", а[1] or "", б[0] or "вікно", б[1] or "",
                                                           (зб.get(і) or {}).get("фото")))

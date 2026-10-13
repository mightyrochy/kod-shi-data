# -*- coding: utf-8 -*-
"""Хвиля 2, найчистіша вада смарагду: слово ВЖЕ МАЄ вікно в ЛЕКСИКОНІ, але з поля крамниці до нього не
дійти — `слово_крамниці` веде в загальніше слово («кораловий» → рожевий, «малиновий» → червоний) або не
читає поля зовсім (маджента, петроль, трояндовий, хвойний, цегляний). Нового вікна не треба: питання лише
в тому, чи ВЛАСНЕ вікно тримає ці речі краще за те, куди їх складають. Вибірка як у `kolory_kramnyts.py`.
Запуск: cd джерела && python3 проби/khvylia2_nedosiazhni.py"""
import collections as К, math, statistics as st, sys
sys.path.insert(0, ".")
import feed, фід_збагачення as FZ, фід_каталог as FK, фід_розбір as FR, verify as V, colorspace as cs
СЛОВА = ("кораловий", "маджента", "малиновий", "петроль", "сливовий", "трояндовий", "хвойний", "цегляний")
зб, н = feed.читати_збагачення(), lambda s: " ".join(str(s or "").lower().split())
поля, гр = К.Counter(), К.defaultdict(lambda: К.defaultdict(dict))
корінь = dict(кораловий="корал", маджента="маджент", малиновий="малин", петроль="петрол",
              сливовий="слив", трояндовий="троянд", хвойний="хвой", цегляний="цегл")
for o in FR.читати_yml("каталог_повний.xml")[0]:
    п = н(o.get("колір_сирий"))
    if not п or len(FK._СЕП_КОЛЬОРУ.split(п)) > 1: continue
    for с in СЛОВА:
        if not п.startswith(корінь[с]): continue
        поля[(с, п)] += 1
        z = зб.get(o["id"]) or {}; к = z.get("колір_основний") or {}
        if not к.get("hex") or (z.get("версія") or 1) < 2 or not FZ.колір_збагачення(z)[2].startswith("hex"): break
        гр[с][п].setdefault(z.get("фото") or o.get("group_id") or o["id"], []).append(cs.hx(к["hex"])); break
бере = lambda w, l: w[0] <= l[0] <= w[1] and w[2] <= l[1] <= w[3] and (w[4] is None or l[1] < 10 or (l[2]-w[4][0]) % 360 <= (w[4][1]-w[4][0]) % 360)
ц = lambda w: (lambda L, C, h: (L, C*math.cos(math.radians(h)), C*math.sin(math.radians(h))))((w[0]+w[1])/2, (w[2]+w[3])/2, 0.0 if w[4] is None else (w[4][0] + ((w[4][1]-w[4][0]) % 360)/2) % 360)
print("ФАКТ · «жодного разу не стоять однослівним полем крамниці» (моє твердження в #314) — ПЕРЕВІРКА:")
for с in СЛОВА:
    оф = sum(n_ for (сл, _), n_ in поля.items() if сл == с)
    вар = ", ".join("%s×%d" % (п, n_) for (сл, п), n_ in sorted(поля.items(), key=lambda kv: -kv[1]) if сл == с)
    ск = V.слово_крамниці(с)
    print("  %-12s оферів %3d · веде в %-12s · поля: %s" % (с, оф, (ск and ск["ім"]) or "НЕ ЧИТАЄ", вар[:80] or "—"))
print("\nФАКТ · чи власне вікно тримає ці речі краще (дизайн; hex жнив v2, підтверджений свідком):")
for с in СЛОВА:
    labs = [tuple(st.median(x[i] for x in v) for i in range(3)) for д in гр[с].values() for v in [д[k] for k in д]]
    if not labs: print("  %-12s виміряних дизайнів 0 — сказати нічого" % с); continue
    лч = [cs.lch(l) for l in labs]; своє, ск = V.ЛЕКСИКОН[с], V.слово_крамниці(с)
    чуже = ск["вікно"] if ск else None
    цс = tuple(st.median(x[i] for x in labs) for i in range(3))
    print("  %-12s диз %3d · СВОЄ %-28s бере %2d, центр %4.1f ΔE00 · ЧУЖЕ (%s) %-26s бере %s, центр %s" % (
        с, len(labs), своє, sum(бере(своє, l) for l in лч), cs.de00(цс, ц(своє)),
        (ск and ск["ім"]) or "нема", str(чуже), sum(бере(чуже, l) for l in лч) if чуже else "—",
        ("%4.1f ΔE00" % cs.de00(цс, ц(чуже))) if чуже else "—"))

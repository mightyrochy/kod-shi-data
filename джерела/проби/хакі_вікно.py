# -*- coding: utf-8 -*-
"""Х-1 «хакі», було → стало: ДО — verify бази (git show, типово origin/main), ПІСЛЯ — чинний. Вибірка — офери з виміром з
фото (hex жнив v2, підтверджений свідком) на verify БАЗИ. Друкує: дизайни «хакі», що бере вікно, і його центр; офери «хакі»/
«олива», які приймає свідок; ґратку основ і м'ятні клітинки; речі, чия точка змінилась, і її відстань до виміру з фото.
Запуск: cd джерела && python3 проби/хакі_вікно.py [база]"""
import collections as К, statistics as st, subprocess, sys, types
sys.path.insert(0, ".")
import feed, міст_основи as МО, palettes as PS, фід_каталог as FK, фід_збагачення as FZ, фід_розбір as FR, verify as V, colorspace as cs
Б = types.ModuleType("verify"); Б.__file__ = V.__file__
exec(subprocess.run(["git", "show", "%s:джерела/verify.py" % (sys.argv[1:] or ["origin/main"])[0]], capture_output=True, text=True, check=True).stdout, Б.__dict__)
def на(M, f):
    """`f()` на ОДНОМУ verify: його беруть і модулі (FK/FZ/PS.V), і `import` усередині функцій, а ґратка кешується."""
    FK.V = FZ.V = PS.V = M; був, sys.modules["verify"] = sys.modules["verify"], M; МО._ҐРАТКА_КЕШ.clear()
    try: return f()
    finally: sys.modules["verify"] = був; FK.V = FZ.V = PS.V = V; МО._ҐРАТКА_КЕШ.clear()
зб, н, диз, оф, вим = feed.читати_збагачення(), lambda s: " ".join(str(s or "").lower().split()), К.defaultdict(list), [], {}
def вибірка():
    for o in FR.читати_yml("каталог_повний.xml")[0]:
        п, z = н(o.get("колір_сирий")), зб.get(o["id"]) or {}
        if not (z.get("колір_основний") or {}).get("hex") or (z.get("версія") or 1) < 2 or not FZ.колір_збагачення(z)[2].startswith("hex"): continue
        вим[o["id"]] = lab = cs.hx(z["колір_основний"]["hex"]); ск = п and len(FK._СЕП_КОЛЬОРУ.split(п)) == 1 and Б.слово_крамниці(п)
        if ск and ск["ім"] in ("хакі", "оливковий"): оф.append((ск["ім"], п, lab))
        if п == "хакі": диз[z.get("фото") or o.get("group_id") or o["id"]].append(lab)
на(Б, вибірка)
labs = [tuple(st.median(x[i] for x in v) for i in range(3)) for v in диз.values()]; ц = tuple(st.median(x[i] for x in labs) for i in range(3))
бере = lambda w, l: (lambda L, C, h: w[0] <= L <= w[1] and w[2] <= C <= w[3] and (C < 10 or V._у_дузі(h, w[4])))(*cs.lch(l))
ст = {ім: на(M, lambda: (dict(МО._ґратка_основ()[0]), list(МО._ґратка_основ()[1]), {r["id"]: r for r in FK._прочитати_каталог("каталог_повний.xml", 0)["каталог"]},
                        К.Counter((с, M.перевірити(l, назва=п)["вердикт"] != "відкинуто") for с, п, l in оф))) for ім, M in (("до", Б), ("після", V))}
for ім, M in (("до", Б), ("після", V)):
    w, св = M.ЛЕКСИКОН["хакі"], ст[ім][3]
    print("ФАКТ · %-5s «хакі» %s: дизайнів «хакі» %d із %d, центр вікна за %.1f ΔE00 від центру вибірки; свідок приймає оферів «хакі» %d із %d, «олива» %d із %d" % (
          ім, w, sum(бере(w, l) for l in labs), len(labs), cs.de00(PS._центр(w), ц), *(x for с in ("хакі", "оливковий") for x in (св[(с, True)], св[(с, True)] + св[(с, False)]))))
(ґд, пд, кд, _), (ґп, пп, кп, _) = ст["до"], ст["після"]
зм = [к for к in set(ґд) | set(ґп) if ґд.get(к) != ґп.get(к)]
print("ФАКТ · ґратка основ: %d чипів до, %d після — %s; м'ятних клітинок змінилось %d, усього %d %s" % (len(ґд), len(ґп),
      "ПОБАЙТОВО ТА САМА" if ґд == ґп and пд == пп else "ЗМІНИЛАСЬ", sum(к.startswith("м'ятний") for к in зм), len(зм), sorted(зм)[:6]))
т = [i for i in кд if i in кп and tuple(кд[i]["lab"]) != tuple(кп[i]["lab"])]; пари = [(cs.de00(tuple(кд[i]["lab"]), вим[i]), cs.de00(tuple(кп[i]["lab"]), вим[i])) for i in т if i in вим]
print("ФАКТ · каталог: речей %d → %d; точка змінилась у %d %s, інше поле — у %d; з виміром з фото %d: медіана ΔE00 точки до виміру %.1f → %.1f, ближче %d, далі %d" % (
      len(кд), len(кп), len(т), dict(К.Counter(кп[i].get("джерело_кольору") for i in т)), sum(1 for i in кд if i in кп and i not in т and кд[i] != кп[i]), len(пари),
      st.median(a for a, _ in пари or [(0, 0)]), st.median(b for _, b in пари or [(0, 0)]), sum(b < a - .1 for a, b in пари), sum(b > a + .1 for a, b in пари)))

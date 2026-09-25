# -*- coding: utf-8 -*-
"""Усі слова кольору крамниць проти лексикону (наряд «не тільки мокко», 25.09). Одиниця — ДИЗАЙН, не SKU (`фото`
жнив, інакше group_id, інакше id — як у `фід_добір.лексикон`); вимір — лише жнива v2 (рядок 141); поле з кількох
частин не рахується. Таблиця: дизайнів, у яке слово код складає, яка частка речей у тому вікні, розкид, вікно коду
проти виміряного, найближче слово — і класи (а) чуже слово, (б) своє вікно й речі поза ним, (в) не знає, (г) дубль.
Запуск: cd джерела && python3 проби/kolory_kramnyts.py"""
import collections as К, math, statistics as st, sys
sys.path.insert(0, ".")
import feed, фід_збагачення as FZ, фід_каталог as FK, фід_розбір as FR, verify as V, colorspace as cs
МІН = 10   # той самий поріг дизайнів, що в рядку 137
зб, н = feed.читати_збагачення(), lambda s: " ".join(str(s or "").lower().split())
гр, сім, таб, центри = К.defaultdict(dict), К.defaultdict(К.Counter), {}, {}
for o in FR.читати_yml("каталог_повний.xml")[0]:
    п = н(o.get("колір_сирий")); z = зб.get(o["id"]) or {}; к = z.get("колір_основний") or {}
    if not п or len(FK._СЕП_КОЛЬОРУ.split(п)) > 1 or not к.get("hex") or (z.get("версія") or 1) < 2: continue
    # ЛИШЕ ВИМІРЯНЕ З ФОТО (25.09.2026): hex жнив v2 береться, тільки коли його ПІДТВЕРДИВ
    # свідок — слово моделі або опис кадру (`колір_збагачення` → «hex+слово»/«hex+опис»).
    # Гілка «слово (hex суперечить)» — не вимір, а центр вікна слова моделі (рядок 141,
    # `колір_не_вимір`); рахувати з неї вікно означало б, що вікно підтверджує саме себе.
    if not FZ.колір_збагачення(z)[2].startswith("hex"): continue
    гр[п].setdefault(z.get("фото") or o.get("group_id") or o["id"], []).append(cs.hx(к["hex"])); сім[п][V.сім_я_слова(к["слово"])] += 1
пц = lambda xs, p: (lambda s, k: s[int(k)] + (s[min(int(k) + 1, len(s) - 1)] - s[int(k)]) * (k - int(k)))(sorted(xs), (len(xs) - 1) * p)
ц = lambda w: (lambda L, C, h: (L, C*math.cos(math.radians(h)), C*math.sin(math.radians(h))))((w[0]+w[1])/2, (w[2]+w[3])/2, 0.0 if w[4] is None else (w[4][0] + ((w[4][1]-w[4][0]) % 360)/2) % 360)
бере = lambda w, l: w[0] <= l[0] <= w[1] and w[2] <= l[1] <= w[3] and (w[4] is None or l[1] < 10 or (l[2] - w[4][0]) % 360 <= (w[4][1] - w[4][0]) % 360)
for сл, д in гр.items():
    labs = [tuple(st.median(x[i] for x in v) for i in range(3)) for v in д.values()]
    ск = V.слово_крамниці(сл); центри[сл] = центр = tuple(st.median(x[i] for x in labs) for i in range(3))
    if len(labs) >= МІН:
        лч = [cs.lch(l) for l in labs]; hs = [h for _, c, h in лч if c >= 10]
        с_ = math.degrees(math.atan2(sum(math.sin(math.radians(h)) for h in hs), sum(math.cos(math.radians(h)) for h in hs))) if hs else 0
        д_ = tuple(round((с_ + пц([((h - с_ + 180) % 360) - 180 for h in hs], p)) % 360) for p in (.05, .95)) if len(hs) >= 5 else None   # дуга — лише коли тон не шум
        таб[сл] = dict(n=len(labs), ім=ск and ск["ім"], вікно=ск and ск["вікно"], не_колір=V.не_колір_крамниці(сл),
                       розкид=round(st.median(cs.de00(центр, l) for l in labs), 1), сім=сім[сл].most_common(1), частка=round(sum(бере(ск["вікно"], l) for l in лч) / len(лч), 2) if ск else 0.0,
                       вим=(math.floor(пц([x[0] for x in лч], .05)), math.ceil(пц([x[0] for x in лч], .95)), math.floor(пц([x[1] for x in лч], .05)), math.ceil(пц([x[1] for x in лч], .95)), д_), близ=min(((cs.de00(центр, ц(V.ЛЕКСИКОН[с])), с) for с in V.ЛЕКСИКОН if not ск or с != ск["ім"]), key=lambda t: t[0]))
неві = [(с, len(гр[с])) for с in гр if not V.слово_крамниці(с) and not V.не_колір_крамниці(с)]   # (в) клас
print("ФАКТ · однослівних полів кольору: %d різних; з ≥%d дизайнів із виміром: %d; поза лексиконом %d слів, з них ≥%d дизайнів — %d (топ: %s)" % ( len(гр), МІН, len(таб), len(неві), МІН, sum(1 for _, n in неві if n >= МІН), sorted(неві, key=lambda t: -t[1])[:4]))
print("%-20s %4s %-12s %-5s %-5s %-27s %-27s %s" % ("слово", "диз", "код→", "част", "розк", "вікно коду", "вимір p5/p95", "найближче"))
for сл, d in sorted(таб.items(), key=lambda kv: -kv[1]["n"]):
    кл = "не колір" if d["не_колір"] else "(в)" if not d["ім"] else "" if d["частка"] >= .5 else "(б)" if d["ім"] == сл or d["ім"] in V.ВІКНА_КРАМНИЦЬ else "(а)"
    print("%-20s %4d %-12s %-5.2f %-5.1f %-27s %-27s %-11s %4.1f %s%s" % (сл, d["n"], d["ім"] or "—", d["частка"], d["розкид"], d["вікно"], d["вим"], d["близ"][1], d["близ"][0], кл, " СТАЛИЙ" if кл in ("(а)", "(б)", "(в)") and d["розкид"] < 10 else ""))
пари = [(cs.de00(центри[a], центри[b]), a, b) for i, a in enumerate(таб) for b in list(таб)[i + 1:]
        if таб[a]["розкид"] < 10 and таб[b]["розкид"] < 10 and not (таб[a]["не_колір"] or таб[b]["не_колір"])
        and (таб[a]["ім"] or a) != (таб[b]["ім"] or b) and cs.de00(центри[a], центри[b]) < 2.5]
print("ФАКТ · (г) два слова — один колір (центри ближчі за 2.5 ΔE00, обидва сталі): %d пар; найтісніші: %s" % (
      len(пари), ["%s↔%s %.1f (код: %s/%s)" % (a, b, e, таб[a]["ім"], таб[b]["ім"]) for e, a, b in sorted(пари)[:6]]))

# -*- coding: utf-8 -*-
"""Хвиля 2: скан слів із ВАДОЮ СМАРАГДУ — слово крамниці розчиняється в ЗАГАЛЬНОМУ вікні («без власного вікна
лишається загальним кольором на весь спектр, бо інші відтінки від нього не відокремлюються», слово власника).
ОЗНАКА — не частка (у смарагду вона 0.43) і не вужчість (вужчі й граматичні форми: «червона», «пломбір»), а
ВІДСТАНЬ центру слова до центру призначеного вікна: саме її смарагд і мав (L30C20 проти трав'яного L50C52).
Форми того самого слова (спільний префікс ≥4) і латинка відсіяні; поле з двох кольорових слів — п.3 наряду.
Запуск: cd джерела && python3 проби/khvylia2_kandydaty.py [мін_дизайнів=5]"""
import collections as К, math, statistics as st, sys
sys.path.insert(0, ".")
import feed, фід_збагачення as FZ, фід_каталог as FK, фід_розбір as FR, verify as V, colorspace as cs
МІН = int(sys.argv[1]) if len(sys.argv) > 1 else 5
ОКРЕМО = {"хакі", "золотий", "золото", "пудровий", "графіт", "графітовий"}   # п.2 і п.3: не вікном
зб, н = feed.читати_збагачення(), lambda s: " ".join(str(s or "").lower().split())
гр, сім = К.defaultdict(dict), К.defaultdict(К.Counter)
двоє = lambda п: sum(1 for т in п.replace("(", " ").replace(")", " ").split() if V.слово_крамниці(т)) > 1
преф = lambda a, b: len([1 for i in range(min(len(a), len(b))) if a[:i+1] == b[:i+1]])
for o in FR.читати_yml("каталог_повний.xml")[0]:
    п = н(o.get("колір_сирий")); z = зб.get(o["id"]) or {}; к = z.get("колір_основний") or {}
    if not п or len(FK._СЕП_КОЛЬОРУ.split(п)) > 1 or not к.get("hex") or (z.get("версія") or 1) < 2: continue
    if not FZ.колір_збагачення(z)[2].startswith("hex"): continue
    гр[п].setdefault(z.get("фото") or o.get("group_id") or o["id"], []).append(cs.hx(к["hex"]))
    сім[п][V.сім_я_слова(к["слово"])] += 1
пц = lambda xs, p: (lambda s, k: s[int(k)] + (s[min(int(k)+1, len(s)-1)] - s[int(k)]) * (k-int(k)))(sorted(xs), (len(xs)-1)*p)
бере = lambda w, l: w[0] <= l[0] <= w[1] and w[2] <= l[1] <= w[3] and (w[4] is None or l[1] < 10 or (l[2]-w[4][0]) % 360 <= (w[4][1]-w[4][0]) % 360)
ц = lambda w: (lambda L, C, h: (L, C*math.cos(math.radians(h)), C*math.sin(math.radians(h))))((w[0]+w[1])/2, (w[2]+w[3])/2, 0.0 if w[4] is None else (w[4][0] + ((w[4][1]-w[4][0]) % 360)/2) % 360)
ряд = []
for сл, д in гр.items():
    ск = V.слово_крамниці(сл)
    if len(д) < МІН or V.не_колір_крамниці(сл) or двоє(сл) or сл in ОКРЕМО or (ск and ск["ім"] in ОКРЕМО): continue
    if not all("а" <= c <= "я" or c in "іїєґ'’ -()" for c in сл): continue          # латинка — інша задача
    if ск and преф(сл, ск["ім"]) >= 4: continue                                     # граматична форма того самого слова
    labs = [tuple(st.median(x[i] for x in v) for i in range(3)) for v in д.values()]
    лч = [cs.lch(l) for l in labs]; hs = [h for _, c, h in лч if c >= 10]
    с_ = math.degrees(math.atan2(sum(math.sin(math.radians(h)) for h in hs), sum(math.cos(math.radians(h)) for h in hs))) if hs else 0
    д_ = tuple(round((с_ + пц([((h-с_+180) % 360)-180 for h in hs], p)) % 360) for p in (.05, .95)) if len(hs) >= 5 else None
    вік = (math.floor(пц([x[0] for x in лч], .05)), math.ceil(пц([x[0] for x in лч], .95)),
           math.floor(пц([x[1] for x in лч], .05)), math.ceil(пц([x[1] for x in лч], .95)), д_)
    центр = tuple(st.median(x[i] for x in labs) for i in range(3))
    ряд.append((len(д), сл, ск and ск["ім"] or "—", cs.de00(центр, ц(ск["вікно"])) if ск else None,
                sum(бере(ск["вікно"], l) for l in лч) / len(лч) if ск else 0.0,
                st.median(cs.de00(центр, l) for l in labs), вік, сім[сл].most_common(2), len(hs)))
print("ФАКТ · слів (≥%d дизайнів, не форма, не латинка, не перелік): %d · «далеко» = центр слова далі 10 ΔE00 від центру призначеного вікна" % (МІН, len(ряд)))
print("%-20s %4s %-12s %-6s %-5s %-5s %-30s %3s %s" % ("слово", "диз", "код→", "далеко", "част", "розк", "вікно з перцентилів", "C10", "сім'ї (з фото)"))
for n_, сл, ім, дал, ч, р, вік, см, c10 in sorted(ряд, key=lambda t: -(t[3] or 99)):
    print("%-20s %4d %-12s %-6s %-5.2f %-5.1f %-30s %3d %s" % (сл, n_, ім, ("%.1f" % дал) if дал is not None else "нема", ч, р, вік, c10, str(см)[:34]))

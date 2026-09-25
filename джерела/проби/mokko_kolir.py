# -*- coding: utf-8 -*-
"""«Мокко» — колір із власним вікном, а не форма «шоколадного» (слово власника 25.09). ДО — verify з 3be10c2
(git show), ПІСЛЯ — чинний; каталог_повний. Вибірку вікна дає третій verify, який слова не знає зовсім (інакше
вимір ріже спір зі «шоколадним»). Друк: вікно з розподілу, сусідні вікна, точка речі до/після, палітра стенда.
Запуск: cd джерела && python3 проби/mokko_kolir.py"""
import collections as К, math, statistics as st, subprocess, sys, types
sys.path.insert(0, "."); sys.path.insert(0, "проби")
import feed, фід_каталог as FK, фід_збагачення as FZ, фід_розбір as FR, фід_добір as Ф, verify as V, colorspace as cs
ДЖ = subprocess.run(["git", "show", "3be10c2:джерела/verify.py"], capture_output=True, text=True, check=True).stdout
def верифай(без_слова=False):
    м = types.ModuleType("verify"); м.__file__ = V.__file__; exec(ДЖ, м.__dict__)
    if без_слова: м.ФОРМИ.pop("мокк"); м.СЛОВА_КРАМНИЦЬ_ПОЛЯ.pop("моко")
    FK.V = FZ.V = м
    return м, {r["id"]: r for r in FK._прочитати_каталог("каталог_повний.xml", 0)["каталог"]}
_оф = FR.читати_yml("каталог_повний.xml")[0]
сир = {o["id"]: o.get("колір_сирий") for o in _оф}; гр_ід = {o["id"]: o.get("group_id") for o in _оф}
зб, н = feed.читати_збагачення(), lambda s: " ".join(str(s or "").lower().split())
_, вибірка = верифай(True); до_V, до = верифай(); FK.V = FZ.V = V
пі = {r["id"]: r for r in FK._прочитати_каталог("каталог_повний.xml", 0)["каталог"]}
# ЛИШЕ ВИМІРЯНЕ З ФОТО (25.09.2026): hex жнив v2, підтверджений свідком («hex+слово» /
# «hex+опис»). Гілка «слово (hex суперечить)» — центр вікна слова моделі, не вимір
# (рядок 141): рахувати з неї вікно означало б, що вікно підтверджує саме себе.
я = [i for i in сир if н(сир.get(i)) in ("мокко", "мокка", "моко")
     and ((зб.get(i) or {}).get("колір_основний") or {}).get("hex") and (зб[i].get("версія") or 1) >= 2
     and FZ.колір_збагачення(зб[i])[2].startswith("hex")]
# ОДИНИЦЯ — ДИЗАЙН, НЕ SKU (`фото` жнив, інакше group_id, інакше id — як у
# `фід_добір.лексикон`): сім SKU одного фото дали б сім однакових «вимірів».
_д = {}
for i in я: _д.setdefault(зб[i].get("фото") or гр_ід.get(i) or i, []).append(cs.hx(зб[i]["колір_основний"]["hex"]))
т = [cs.lch(tuple(st.median(x[k] for x in v) for k in range(3))) for v in _д.values()]
пц = lambda xs, p: (lambda s, k: s[int(k)] + (s[min(int(k) + 1, len(s) - 1)] - s[int(k)]) * (k - int(k)))(sorted(xs), (len(xs) - 1) * p)
hs = [h for _, c, h in т if c >= 10]; сер = math.degrees(math.atan2(sum(math.sin(math.radians(h)) for h in hs), sum(math.cos(math.radians(h)) for h in hs)))
вікно = (math.floor(пц([x[0] for x in т], .05)), math.ceil(пц([x[0] for x in т], .95)), math.floor(пц([x[1] for x in т], .05)), math.ceil(пц([x[1] for x in т], .95)), tuple(round((сер + пц([((h - сер + 180) % 360) - 180 for h in hs], p)) % 360) for p in (.05, .95)))
бере = lambda w, l: w[0] <= l[0] <= w[1] and w[2] <= l[1] <= w[3] and (w[4] is None or l[1] < 10 or (l[2] - w[4][0]) % 360 <= (w[4][1] - w[4][0]) % 360)
print("ФАКТ · дизайнів «мокко» з ПІДТВЕРДЖЕНИМ виміром з фото: %d (поріг 10; SKU %d); сім'ї з фото: %s" % (len(т), len(я), К.Counter(V.сім_я_слова(зб[i]["колір_основний"]["слово"]) for i in я).most_common(4)))
print("ФАКТ · вікно з перцентилів: %s; у ЛЕКСИКОНІ стоїть %s — %s" % (вікно, V.ЛЕКСИКОН["мокко"], "збіг" if V.ЛЕКСИКОН["мокко"] == вікно else "РОЗБІЖНІСТЬ"))
print("ФАКТ · цих %d речей приймає вікно: %s" % (len(т), ", ".join("%s %d" % (с, sum(бере(V.ЛЕКСИКОН[с], l) for l in т)) for с in ("мокко", "коричневий", "шоколадний", "кемел", "тауп"))))
ід = [i for i in пі if пі[i].get("колір_ім") == "мокко" and (зб.get(i) or {}).get("колір_основний", {}).get("hex")]
де = lambda к, i: cs.de00(tuple(к[i]["lab"]), cs.hx(зб[i]["колір_основний"]["hex"]))   # вимір з фото — найкраща правда, що є
зв = lambda к, с: sum(1 for r in к.values() if r.get("колір_ім") == с)
print("ФАКТ · речей зі словом кольору «мокко»: ДО %d, ПІСЛЯ %d; «шоколадний» по каталогу: ДО %d → ПІСЛЯ %d" % (зв(до, "мокко"), зв(пі, "мокко"), зв(до, "шоколадний"), зв(пі, "шоколадний")))
print("ФАКТ · точка речі (центр вікна слова) проти виміру з фото, ΔE00 на %d речах: ДО медіана %.1f сер. %.1f → ПІСЛЯ %.1f / %.1f; ближче стало %d" % (len(ід),
      st.median(де(до, i) for i in ід), st.mean(де(до, i) for i in ід), st.median(де(пі, i) for i in ід), st.mean(де(пі, i) for i in ід), sum(1 for i in ід if де(пі, i) < де(до, i))))
import pal_вимір as P
запити = P.пул_стенда()[3]   # ті самі рядки запиту, якими ходить продукт
лаб = lambda w: (lambda L, C, h: (L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h))))((w[0] + w[1]) / 2, (w[2] + w[3]) / 2, 0.0 if w[4] is None else (w[4][0] + ((w[4][1] - w[4][0]) % 360) / 2) % 360)
рядки = lambda w: [q for q in запити if Ф.частка_вікна(tuple(map(float, w[:4])) + (tuple(w[4]),), q) > 0 and Ф.описує_річ(лаб(w), q)]
for мітка, w in (("ДО   «шоколадний»", до_V.ЛЕКСИКОН["шоколадний"]), ("ПІСЛЯ «мокко»    ", V.ЛЕКСИКОН["мокко"])):
    print("ФАКТ · палітра стенда, %s: бере %d із %d рядків | слоти %s" % (мітка, len(рядки(w)), len(запити), sorted({q.get("слот") for q in рядки(w)})))
print("ФАКТ · слоти речей «мокко»: %s" % К.Counter(пі[i].get("слот") for i in пі if пі[i].get("колір_ім") == "мокко").most_common())

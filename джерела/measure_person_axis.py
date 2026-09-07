# -*- coding: utf-8 -*-
"""Вимір дискримінаційної сили ОСОБИСТОЇ колірної осі на живому укр. каталозі (7 597 SKU).

ПЕРЕЗНЯТО 28.08.2026: стара фікстура (рос. фід, разовий виняток 23.08) мертва й
порушувала мовне правило проєкту. Джерело тепер — каталог_повний.xml (46 укр. магазинів);
колір читається так само, як його читає живий шлях: читати_yml → колір_назва або назва.

Питання: коли ЛЮДИНА міняється, а каталог той самий — наскільки міняється множина
речей, які проходять колірні вікна? Якщо чотири протилежні колорити одержують
майже одну множину, вісь «які кольори речей якій людині» на реальних речах не працює,
хоч би скільки функцій її рахувало.

Колір речі — з param «Цвет» через лексикон (вікно LCh, T3), центр вікна як точка.
Дві умови зйомки: protocolized (тон дозволений) і uncontrolled (тон загейтовано K-PC-05).
"""
import sys, os, math
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import verify as V, outfit as O, palette as P, colorspace as cs, feed as F, trace as TR

ФІД = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "каталог_жіночий.xml")
СЛОТИ = ("верх", "низ", "сукня", "верхній_шар", "взуття", "сумка")
СХЕМИ = ("нейтрали+акцент", "тональна", "аналогова", "приглушена_комплементарна")

ЛЮДИ = {
 "тепла-світла":  ("#deb295", "#f1dbaa", "#759087"),
 "холодна-темна": ("#5c4636", "#241c18", "#3f4a55"),
 "холодна-світла":("#f0d5c8", "#4a4644", "#6b8cae"),
 "тепла-темна":   ("#c48f60", "#3b2416", "#6b4a2b"),
}

import re
def _усі_імена(текст):
    t = " " + текст.lower().replace("-", " ").replace("/", " ") + " "
    return {V.ФОРМИ[k] for k in V.ФОРМИ
            if re.search(r"(?:^|[^0-9a-zа-яіїєґ'])" + re.escape(k), t)}
def розвязати(значення):
    ц = V.назва_кольору(значення.lower()); зн = _усі_імена(значення)
    if len(зн) >= 2: return None, "мульти"
    if ц: return ц, "ціле"
    if len(зн) == 1: return next(iter(зн)), "частина"
    return None, "мовчить"
def _lab(L, C, h):
    r = math.radians(h); return (L, C*math.cos(r), C*math.sin(r))
def центр_вікна(в):
    Llo, Lhi, Clo, Chi, д = в
    if д is None: return _lab((Llo+Lhi)/2, (Clo+Chi)/2, 0.0)
    a, b = д; h = (a + ((b - a) % 360)/2) % 360
    return _lab((Llo+Lhi)/2, (Clo+Chi)/2, h)

# ── фід: тим самим читачем, що й живий шлях ──
offers, _діаг = F.читати_yml(ФІД)[:2]
sku = []
for o in offers:
    колір = (o.get("колір_назва") or o.get("назва") or "").strip()
    ім, як = розвязати(колір)
    sku.append(dict(id=o["id"], назва=o["назва"], колір=колір, ім=ім, як=як,
                    lab=(центр_вікна(V.ЛЕКСИКОН[ім]) if ім else None)))
статус = Counter(s["як"] for s in sku)
одно = [s for s in sku if s["lab"]]
print("SKU %d · розв'язка кольору %s · з Lab-точкою %d (%.0f%%)" %
      (len(sku), dict(статус), len(одно), 100*len(одно)/len(sku)))
верд = Counter(("нейтраль" if O.нейтраль(s["lab"]) is not None else "колір") for s in одно)
print("ярус 2 (нейтраль/колір за центром вікна):", dict(верд))

# ── людина → рядки запиту ──
def рядки(hexи, схема, source):
    Fp = cs.features(*[cs.hx(x) for x in hexи])
    спец = P.специфікація(Fp, схема, СЛОТИ, source=source)
    return Fp, P.запит_у_фід(спец)

def пройшло(рядки_запиту):
    """множина id, що проходять ХОЧ ОДИН рядок запиту свого слота; і по осях — чому відкинуто"""
    ok = set(); чому = Counter()
    за_слотом = defaultdict(set)
    for q in рядки_запиту:
        if not isinstance(q, dict) or q.get("L_min") is None: continue
        for s in одно:
            if F.підходить(s["lab"], q):
                ok.add(s["id"]); за_слотом[q["слот"]].add(s["id"])
    return ok, за_слотом

for source in ("protocolized", "uncontrolled"):
    print("\n══════ source = %s ══════" % source)
    for схема in СХЕМИ:
        мн = {}; осі = {}
        for кого, hexи in ЛЮДИ.items():
            Fp, з = рядки(hexи, схема, source)
            тон_рядків = sum(1 for q in з if isinstance(q, dict) and q.get("h_from") is not None)
            b_рядків = sum(1 for q in з if isinstance(q, dict) and q.get("b_min") is not None)
            ok, за_сл = пройшло(з)
            мн[кого] = ok
            осі[кого] = (len(з), тон_рядків, b_рядків)
        n = len(одно)
        print("\n  схема %-26s" % схема)
        for кого in ЛЮДИ:
            print("    %-15s рядків %2d (з тоном %2d, з b* %2d) · впущено %5d/%d (%.0f%%)" %
                  ((кого,) + осі[кого] + (len(мн[кого]), n, 100*len(мн[кого])/n)))
        ключі = list(ЛЮДИ)
        for i in range(len(ключі)):
            for j in range(i+1, len(ключі)):
                a, b = мн[ключі[i]], мн[ключі[j]]
                jac = len(a & b)/len(a | b) if (a | b) else 1.0
                print("    Жаккар %-15s × %-15s = %.2f · лише-перша %4d · лише-друга %4d" %
                      (ключі[i], ключі[j], jac, len(a - b), len(b - a)))

# ── РІВЕНЬ РІШЕННЯ (28.08.2026): не «пропустило хоч одне вікно», а ПУЛ ────────────
# Ворота-об'єднання ~100 рядків насичуються (76–81 % впущено, Жаккар 0.95–0.99) — але
# живий шлях обирає топ-K найближчих до ЦЕНТРУ вікна свого слота. Дискримінація осі
# або живе тут, або її нема ніде.
print("\n══════ рівень рішення: топ-20 на слот за відстанню до центру (uncontrolled) ══════")
def топ_слота(рядки_запиту, слот, K=20):
    кращі = {}
    for q in рядки_запиту:
        if not isinstance(q, dict) or q.get("L_min") is None or q.get("слот") != слот: continue
        c = центр_вікна((q["L_min"], q["L_max"], q["C_min"], q["C_max"],
                         (q.get("h_from"), q.get("h_to")) if q.get("h_from") is not None else None))
        for s in одно:
            if not F.підходить(s["lab"], q): continue
            d = cs.de00(s["lab"], c)
            if d < кращі.get(s["id"], 1e9): кращі[s["id"]] = d
    return set(sorted(кращі, key=кращі.get)[:K])

for схема in СХЕМИ[:2]:
    print("\n  схема %s" % схема)
    пули = {}
    for кого, hexи in ЛЮДИ.items():
        _, з = рядки(hexи, схема, "uncontrolled")
        пули[кого] = {сл: топ_слота(з, сл) for сл in ("верх", "низ", "взуття", "сумка")}
    ключі = list(ЛЮДИ)
    for i in range(len(ключі)):
        for j in range(i + 1, len(ключі)):
            a, b = пули[ключі[i]], пули[ключі[j]]
            ж = []
            for сл in a:
                u = a[сл] | b[сл]
                ж.append(len(a[сл] & b[сл]) / len(u) if u else 1.0)
            print("    Жаккар топ-20 %-15s × %-15s = %s (середнє %.2f)" %
                  (ключі[i], ключі[j], " ".join("%.2f" % x for x in ж), sum(ж) / len(ж)))

# ── що саме різнить: по іменах кольорів, перша схема, protocolized ──
print("\n══════ де саме розходяться (protocolized, нейтрали+акцент) ══════")
мн = {}
for кого, hexи in ЛЮДИ.items():
    _, з = рядки(hexи, "нейтрали+акцент", "protocolized"); мн[кого], _ = пройшло(з)
ім_за_id = {s["id"]: s["ім"] for s in одно}
for a, b in (("тепла-світла", "холодна-темна"), ("тепла-світла", "холодна-світла"), ("холодна-темна", "тепла-темна")):
    лише_a = Counter(ім_за_id[i] for i in мн[a] - мн[b]); лише_b = Counter(ім_за_id[i] for i in мн[b] - мн[a])
    print("  %s без %s: %s" % (a, b, лише_a.most_common(6)))
    print("  %s без %s: %s" % (b, a, лише_b.most_common(6)))

# -*- coding: utf-8 -*-
"""Вигляд речі у вході пояснення ДО → ПІСЛЯ на записаних прогонах «як людина» 3 і 4 (наряд
Е2-опора-пояснення-без-опису-речі).

Лічить поля про вигляд речі (усе, крім того, чим річ назвати й знайти: n, kind, type, set_half, photos, no_photo, hers,
photo_other_colour), які йдуть у вхід опису не як причина: у речах образу й запасних заміни і в адресі речі заяви
(словник з `item_id`). Три стовпці: «запис» — що реально пішло в модель у прогоні; «дерево» — ті самі речі через
складач дерева, з якого запущено (`знання_речі.певне`, `дріт_моделі._адреси_без_вигляду`, коли він є): на `main` — ДО,
на гілці — ПІСЛЯ. Речі відновлено з дроту запису: вид — ключем ядра, колір — словом і hex виміру, кадр іншого кольору,
кадри, ознаки. Окремо — промпт опису дерева: довжина завдання (роль, правила, межі, поля входу й схеми) і місця, де він
просить описати річ. Повтор входу, не відповідей: відповіді моделі правки не міряють (наряд).
Запуск з кореня дерева: python3 <шлях>/вхід_пояснення.py"""
import collections, glob, gzip, json, re, sys
sys.path.insert(0, "джерела")
import внутрішня_мова as ВМ, знання_речі as ЗН, дріт_моделі as Д, розбір_відповідей as РВ

НАЗВА_Й_КОД = {"n", "kind", "type", "set_half", "photos", "no_photo", "hers", "photo_other_colour"}
ВИГЛЯД_АДРЕСИ = ("color", "hex")
адреси = getattr(Д, "_адреси_без_вигляду", lambda в: в)


def річ_з_дроту(x):
    return dict(н=x.get("n"), слот=ВМ.ключ("slot", x["kind"]) if x.get("kind") else None,
                тип=ВМ.ключ("item_type", x["type"]) if x.get("type") else None,
                частина={"top": "верх", "bottom": "низ"}.get(x.get("set_half")), код_кольору=x.get("color"),
                hex=x.get("hex"), кадр_колір=x.get("photo_other_colour"), фото_номери=x.get("photos"),
                без_кадру=x.get("no_photo"), її_річ=x.get("hers"),
                ознаки={к: v for к, v in x.items() if к not in НАЗВА_Й_КОД | {"color", "hex"}})


def дріт_опису(т):
    і = т.find('"outfit": {"id"')
    return json.JSONDecoder().raw_decode("{" + т[і:])[0] if і >= 0 else None


def вигляд_адрес(в):
    """Скільки полів вигляду в адресах речей (словник з `item_id`) усього значення."""
    if isinstance(в, dict):
        return sum(1 for к in ВИГЛЯД_АДРЕСИ if "item_id" in в and к in в) + sum(вигляд_адрес(x) for x in в.values())
    if isinstance(в, list):
        return sum(вигляд_адрес(x) for x in в)
    return 0


л, поля_запис, поля_дерево = collections.Counter(), collections.Counter(), collections.Counter()
for шлях in sorted(glob.glob("аудит/проби/живий-як-людина-[34]/стенд/службове/*/обміни.jsonl.gz")):
    for з in gzip.open(шлях, "rt"):
        з = json.loads(з)
        try:
            тексти = [b["text"] for m in json.loads(з["запит"])["messages"] for b in (m["content"] if isinstance(
                m["content"], list) else [dict(type="text", text=m["content"])]) if b.get("type") == "text"]
        except (ValueError, KeyError, TypeError):
            continue
        for т in тексти:
            д = дріт_опису(т) if '"about_items"' in т else None
            if not д:
                continue
            л["викликів опису"] += 1
            речі = д["outfit"]["items"] + ((д.get("swap_spares") or {}).get("spares") or [])
            for x in речі:
                л["речей (образ і запасні)"] += 1
                до = [к for к in x if к not in НАЗВА_Й_КОД]
                після = [к for к in ЗН.певне(річ_з_дроту(x)) if к not in НАЗВА_Й_КОД]
                поля_запис.update(до)
                поля_дерево.update(після)
                л["речей із полем вигляду: запис"] += bool(до)
                л["речей із полем вигляду: дерево"] += bool(після)
            заяви = {к: в for к, в in д.items() if к not in ("task", "outfit", "swap_spares")}
            л["полів вигляду в адресах заяв: запис"] += вигляд_адрес(заяви)
            л["полів вигляду в адресах заяв: дерево"] += вигляд_адрес(адреси(заяви))
for к, v in л.items():
    print("%s: %d" % (к, v))
print("полів вигляду в речах: запис %d → дерево %d" % (sum(поля_запис.values()), sum(поля_дерево.values())))
print("  за ключем, запис:", ", ".join("%s %d" % кв for кв in поля_запис.most_common()))
print("  за ключем, дерево:", ", ".join("%s %d" % кв for кв in поля_дерево.most_common()) or "—")

# ── промпт опису дерева: що він просить про річ ─────────────────────────────────────
об = РВ.промпт_опису(РВ.опис_обʼєкт([dict(н="#1·01", назва="x", слот="сукня", тип="сукня", код_кольору="green",
                                         hex="#2e8b57", фото_номери=[1])], фото_є=True))
завдання = json.dumps(об["task"], ensure_ascii=False)
ПРОСИТЬ_ВИГЛЯД = (r"[Dd]escribe", r"supported properties", r"«color»", r"«hex»", r"by their codes", r"use its codes",
                  r"properties as codes")
print("промпт опису: знаків завдання %d; рядок речі на дроті: %s" % (
    len(завдання), json.dumps(об["outfit"]["items"][0], ensure_ascii=False)))
print("промпт опису: місць, що просять описати річ чи її вигляд, %d (%s)" % (
    sum(len(re.findall(в, завдання)) for в in ПРОСИТЬ_ВИГЛЯД),
    ", ".join("%s %d" % (в, len(re.findall(в, завдання))) for в in ПРОСИТЬ_ВИГЛЯД if re.search(в, завдання)) or "—"))

# -*- coding: utf-8 -*-
"""ВИМІР дефектів D1–D10 на фікстурі трьох діалектів YML.

ЧЕСНА МЕЖА, до всіх чисел: це ФІКСТУРА, а не живий фід. Вона побудована рівно за
специфікаціями (Rozetka p185/p188/p205, Prom 360004963538, Google Merchant), тому
доводить, що ПАРСЕР тепер читає те, що специфікації описують. Вона НЕ доводить, що
реальний магазин пише саме так, і не дає жодного з шести чисел, яких вимагає
тема-7 частина 7. Живий фід не парсився жодного разу — це і лишається блокером.

Прогін: `python3 аудит_фіду.py`
"""
import os, tempfile
import feed

ФІКСТУРА = """<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="2026-08-20">
 <shop>
  <name>тест</name>
  <categories>
    <category id="1">Одяг</category>
    <category id="2" parentId="1">Сукні</category>
    <category id="3" parentId="1">Спідниці</category>
  </categories>
  <offers>

    <!-- ROZETKA-діалект: жодного group_id, один оффер на РОЗМІР, article = модель,
         двомовний param, кома як сепаратор, stock_quantity як авторитет -->
    <offer id="RZ1" available="true">
      <name>Сукня міді олива, розмір S</name><categoryId>2</categoryId>
      <price>1450</price><vendor>Gepur</vendor><article>GP-8841</article>
      <stock_quantity>4</stock_quantity>
      <picture>https://x/8841.jpg</picture>
      <param name="Колір"><value lang="uk">Олива</value><value lang="ru">Олива</value></param>
    </offer>
    <offer id="RZ2" available="true">
      <name>Сукня міді олива, розмір M</name><categoryId>2</categoryId>
      <price>1450</price><vendor>Gepur</vendor><article>GP-8841</article>
      <stock_quantity>2</stock_quantity>
      <picture>https://x/8841.jpg</picture>
      <param name="Колір"><value lang="uk">Олива</value></param>
    </offer>
    <offer id="RZ3" available="true">
      <name>Сукня міді олива, розмір L</name><categoryId>2</categoryId>
      <price>1450</price><vendor>Gepur</vendor><article>GP-8841</article>
      <stock_quantity>0</stock_quantity>
      <picture>https://x/8841.jpg</picture>
      <param name="Колір"><value lang="uk">Олива, Хакі</value></param>
    </offer>
    <offer id="RZ4" available="true">
      <name>Спідниця олива</name><categoryId>3</categoryId>
      <price>900</price><vendor>Gepur</vendor><article>GP-9002</article>
      <stock_quantity>7</stock_quantity>
      <picture>https://x/9002.jpg</picture>
      <param name="Колір">Олива<br/>Друге значення</param>
    </offer>

    <!-- PROM-діалект: group_id як АТРИБУТ, «|» як сепаратор, available="" = НЕМА -->
    <offer id="PR1" available="" group_id="551">
      <name>Блуза шовк</name><name_ua>Блуза шовкова</name_ua><categoryId>1</categoryId>
      <price>1200</price><picture>https://x/551a.jpg</picture>
      <param name="колір">Чорний|Білий</param>
    </offer>
    <offer id="PR2" available="склад" group_id="551">
      <name>Блуза шовк</name><name_ua>Блуза шовкова</name_ua><categoryId>1</categoryId>
      <price>1200</price><picture>https://x/551b.jpg</picture>
      <param name="колір">Олива</param>
    </offer>

    <!-- PROM→ROZETKA експорт: group_id як ДИТИНА; type='vendor.model' — name ігнорується -->
    <offer id="PX1" available="true" type="vendor.model">
      <group_id>770</group_id><categoryId>3</categoryId>
      <typePrefix>Спідниця</typePrefix><vendor>MustHave</vendor><model>міді 7712</model>
      <name>НЕ ЧИТАТИ ЦЕ</name>
      <price>1100</price><picture>https://x/7712.jpg</picture>
      <param name="Колір"><value lang="uk">Олива</value></param>
    </offer>

    <!-- GOOGLE-подібний: колір «/» за помітністю -->
    <offer id="GG1" available="true" group_id="880">
      <name>Сукня трикотаж</name><categoryId>2</categoryId>
      <price>1600</price><picture>https://x/880.jpg</picture>
      <param name="color">Black/Green</param>
    </offer>

  </offers>
 </shop>
</yml_catalog>
"""

СТАРИЙ_ЛЕКСИКОН_ВХІД = None


def _старий_лексикон(каталог, мін_n=3, мін_впевненість=0.5):
    """Стара реалізація — щоб різницю ПОКАЗАТИ, а не заявити."""
    import statistics
    from collections import defaultdict
    from colorspace import lch, de00
    гр = defaultdict(list)
    for c in каталог:
        if c.get("колір_назва") and c["впевненість"] >= мін_впевненість:
            гр[c["колір_назва"].strip().lower()].append(c["lab"])
    out = {}
    for назва, labs in гр.items():
        if len(labs) < мін_n: continue
        центр = tuple(statistics.median(x[i] for x in labs) for i in range(3))
        розкид = statistics.median(de00(центр, l) for l in labs) if len(labs) > 1 else 0.0
        out[назва] = dict(n=len(labs), розкид=round(розкид, 1), придатна=розкид < 10.0)
    return out


def прогін():
    шлях = os.path.join(tempfile.gettempdir(), "фікстура.xml")
    open(шлях, "w", encoding="utf-8").write(ФІКСТУРА)
    offers, діаг = feed.читати_yml(шлях)

    print("=" * 78); print("ПАРСЕР ФІДУ: фікстура трьох діалектів"); print("=" * 78)
    print(f"\nофферів: {діаг['офферів']}   ключ моделі розв'язано: "
          f"{діаг['ключ_моделі_покриття']:.0%}  (R-FEED-02)")
    print(f"  гілки ключа:        {діаг['ключ_моделі_гілки']}")
    print(f"  гілки назви:        {діаг['назва_гілки']}")
    print(f"  гілки доступності:  {діаг['доступність_гілки']}")

    print("\n%-5s %-13s %-30s %-9s %s" % ("id", "ключ", "назва", "наявн.", "колір"))
    for o in offers:
        акц = ("  +акценти %s" % o["кольори_акценти"]) if o["кольори_акценти"] else ""
        print("%-5s %-13s %-30s %-9s %s%s" % (
            o["id"], str(o["group_id"])[:13], o["назва"][:30],
            {True: "є", False: "НЕМА", None: "?"}[o["available"]],
            o["колір_назва"], акц))

    print("\n── ГЕЙТИ (кожен ловить названий дефект) " + "─" * 37)
    гейти = [
        ("D1 group_id-атрибут (Prom)",
         next(o for o in offers if o["id"] == "PR1")["group_id"] == "551"),
        ("D1 group_id-дитина (Prom→Rozetka)",
         next(o for o in offers if o["id"] == "PX1")["group_id"] == "770"),
        ("D1/D2 Rozetka: 3 розміри → ОДНА модель через article",
         len({o["group_id"] for o in offers if o["id"].startswith("RZ") and o["id"] != "RZ4"}) == 1),
        ("D4 Prom available=\"\" читається як НЕ в наявності",
         next(o for o in offers if o["id"] == "PR1")["available"] is False),
        ("D5 stock_quantity=0 перемагає available=true",
         next(o for o in offers if o["id"] == "RZ3")["available"] is False),
        ("D6 <value lang=\"uk\"> більше не губиться",
         next(o for o in offers if o["id"] == "RZ1")["колір_назва"] == "Олива"),
        ("D7 кома (Rozetka) розділяє домінанту й акцент",
         next(o for o in offers if o["id"] == "RZ3")["кольори_акценти"] == ["Хакі"]),
        ("D7 «|» (Prom) розділяє",
         next(o for o in offers if o["id"] == "PR1")["кольори_акценти"] == ["Білий"]),
        ("D7 «/» (Google) розділяє за помітністю",
         next(o for o in offers if o["id"] == "GG1")["колір_назва"] == "Black"),
        ("D8 <br/> не обриває параметр",
         "Друге" in (next(o for o in offers if o["id"] == "RZ4")["параметри"].get("колір") or "")),
        ("D9 name_ua має пріоритет над name",
         next(o for o in offers if o["id"] == "PR2")["назва"] == "Блуза шовкова"),
        ("D9 type='vendor.model' збирає назву, ігноруючи <name>",
         next(o for o in offers if o["id"] == "PX1")["назва"] == "Спідниця MustHave міді 7712"),
        ("D10 гілка ключа звітується для кожного оффера",
         all(o["ключ_гілка"] for o in offers)),
    ]
    впало = 0
    for назва, ок in гейти:
        print(("  ✓ " if ок else "  ✗ ПРОВАЛ ") + назва)
        впало += (not ок)

    # ── R-FEED-06: гейт розкиду, що сам себе перемагав ────────────────────────
    print("\n── R-FEED-06: лексикон на дизайн проти лексикона на SKU " + "─" * 22)
    # ВАЖЛИВО, і це ПОПРАВКА до механізму, як його описує тема-7 §2.3.
    # Файл каже «кожен дубльований дизайн тягне медіанний розкид до нуля». Прогін
    # показує: при РІВНОМІРНОМУ дублюванні медіана не рухається взагалі — кожне
    # значення повторюється однакове число разів, медіана та сама, роздувається лише n.
    # Розкид падає тільки при НЕРІВНОМІРНІЙ глибині розмірної сітки — а вона на
    # реальному каталозі нерівномірна саме так: ходовий дизайн лежить у 6–7 розмірах,
    # рештки — в одному. Тому фікстура моделює нерівномірність, а не рівномірність.
    центр = (50, -10, 24)
    краї = [(30, -22, 6), (36, -19, 10), (66, -2, 38), (72, 2, 44), (78, 6, 50)]
    каталог = []
    for розмір in range(7):        # ходовий дизайн: повна розмірна сітка
        каталог.append(dict(id="hit-%d" % розмір, group_id="M0",
                            фото_ключ="https://x/0.jpg", lab=центр, впевненість=0.8,
                            колір_назва="олива", слот="сукня", назва="Сукня олива",
                            ціна=1000))
    for d, lab in enumerate(краї):  # рештки: по одному розміру
        каталог.append(dict(id="tail-%d" % d, group_id="M%d" % (d + 1),
                            фото_ключ="https://x/%d.jpg" % (d + 1), lab=lab,
                            впевненість=0.8, колір_назва="олива", слот="сукня",
                            назва="Сукня олива", ціна=1000))
    стар = _старий_лексикон(каталог)["олива"]
    нов = feed.лексикон(каталог)["олива"]
    print("  на SKU (було):    n=%-3d розкид=%.1f  придатна=%s" %
          (стар["n"], стар["розкид"], стар["придатна"]))
    print("  на дизайн (стало): n=%-3d розкид=%.1f  придатна=%s" %
          (нов["n"], нов["розкид"], нов["придатна"]))
    print("  → ходовий дизайн голосував 7 разів (одне фото × 7 розмірів), рештки — по разу.\n"
          "    Гейт показував НАЙВИЩУ впевненість (розкид 0.0) саме там, де доказ\n"
          "    найнадлишковіший, і ховав, що назва покриває ΔE00 ≈ 17.\n"
          "    ПОПРАВКА до теми-7 §2.3: при РІВНОМІРНОМУ дублюванні медіана не рухається —\n"
          "    роздувається лише n. Розкид падає тільки при нерівномірній глибині сітки.")
    if стар["придатна"] and not нов["придатна"]:
        print("  ✓ назва більше НЕ входить у робочий словник кольорів на дублікатах")
    else:
        впало += 1
        print("  ✗ ПРОВАЛ: дедуплікація не змінила вердикт")

    print("\n" + "=" * 78)
    print(("ВСІ ГЕЙТИ ПРОЙДЕНО" if not впало else "ПРОВАЛІВ: %d" % впало) +
          "  —  але це ФІКСТУРА. Жодного живого українського фіду не парсили.")
    print("=" * 78)
    return впало


if __name__ == "__main__":
    raise SystemExit(прогін())

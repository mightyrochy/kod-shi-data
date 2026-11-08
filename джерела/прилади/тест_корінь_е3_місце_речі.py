# -*- coding: utf-8 -*-
"""Проби приладу `корінь_е3_місце_речі.py` на малому дереві продукту — на обидва боки: справжнє місце лічиться
(стала класу, обгортка, поле `near` без походження, власний літерал слотів, середнє голосів волосся, волосся проти
шкіри), читач запису й копія — ні. Прилад лише розбирає AST, модулі дерева не імпортуються.
Запуск: python3 -m unittest джерела/прилади/тест_корінь_е3_місце_речі.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import обсяг_приладу as ОБСЯГ  # noqa: E402
import корінь_е3_місце_речі as П  # noqa: E402

ДЕРЕВО = {
    "slots.py": '''
КЛЮЧІ = {"top": "верх", "bottom": "низ", "scarf": "шарф", "jewelry": "прикраси", "bag": "сумка"}
_SLOT_TYPES = {"top": ("blouse",), "jewelry": ("earrings", "bracelet")}
''',
    "внутрішня_мова.py": '''
ТАБЛИЦЯ = {"zone": {"arms": "руки"}, "item_type": {"earrings": "сережки", "bracelet": "браслет"}}
ЗОНИ_ВЕТО = tuple(ТАБЛИЦЯ["zone"].values())
''',
    "колір_річ.py": '''
SLOT_NEAR_FALLBACK = {"шарф": 0.9, "верх": 0.6, "сережки": 0.9, "низ": 0.1}
NEAR_МІН = 0.4
def near_слота(слот, дистанція=None):
    база = SLOT_NEAR_FALLBACK.get(слот, 0.2)
    return база if дистанція is None else база * дистанція
''',
    "обгортка.py": '''
from колір_річ import near_слота as _ns
import колір_річ as _КР
ДАЛЕКІ = [с for с, в in _КР.SLOT_NEAR_FALLBACK.items() if в < 0.2]
def біля_обличчя(слот):
    return _ns(слот) >= _КР.NEAR_МІН
''',
    "правила.py": '''
import обгортка as О
from колір_річ import NEAR_МІН
def суд(речі):
    return [р for р in речі if О.біля_обличчя(р["слот"])]            # місце: виклик обгортки
def далекі(речі):
    return [р for р in речі if р["слот"] in О.ДАЛЕКІ]               # місце: похідна таблиця
def приобличчя(E):
    return [e for e in E if e["near"] >= NEAR_МІН]                   # місце: near без походження
def приобличчя_виміряне(E):
    return [e for e in E if e["near_виміряний"] and e["near"] >= NEAR_МІН]   # не місце: походження
def зона_місце(р):
    return р.get("місце") == "шия"                                    # не місце: запис місця
def копія(m):
    return dict(near=m["near"], площа=1)                              # не місце: копія
def метал_біля_обличчя(р):
    return р.get("слот") in ("сережки", "шарф")                       # місце: власний літерал слотів
def краї(р):
    return р.get("слот") == "верх"                                    # не місце: функція не про місце
''',
    "обличчя.py": '''
def value(F):
    вол = [v["L"] for k, v in F.items() if k.startswith("волосся")]
    return 0.5 * sum(вол) / len(вол) + 0.5 * F["шкіра"]["L"]          # місце: середнє голосів
def контраст(F):
    шк = F["шкіра"]
    hair = [v for k, v in F.items() if k.startswith("волосся")]
    Lh = sum(h["L"] for h in hair) / len(hair)                        # місце: середнє голосів
    return abs(Lh - шк["L"])                                          # місце: волосся проти шкіри
def хрома(F):
    C = [v["C"] for k, v in F.items() if k.startswith("волосся")]
    return sum(C) / len(C)                                            # місце: згортка хроми голосів
def сивина(F):
    return any(v["C"] < 5 for k, v in F.items() if k.startswith("волосся"))   # місце: «хоч один голос»
def по_голосу(F):
    return {k: v["L"] for k, v in F.items() if k.startswith("волосся")}       # не місце: кожен голос окремо
def чи_є_волосся(F):
    return any(k.startswith("волосся") for k in F)                    # не місце: є голос чи нема
def за_записом(F, образ):
    if образ.get("місце_джерело") is None:
        return None
    вол = [v["L"] for k, v in F.items() if k.startswith("волосся")]
    return sum(вол) / len(вол)                                        # не місце: читач запису
''',
    "шари.py": '''
def елементи(речі, стан):
    пальто = next((r for r in речі if r["слот"] == "верхній_шар"), None)      # місце: шар узято за слотом
    out = []
    for r in речі:
        s = r["слот"]
        if пальто and s in ("верх", "сукня"):                         # місце: що під шаром
            if not bool(пальто.get("розстібнуте")):                   # місце: «невідомо» стає «застебнуто»
                continue
        out.append(dict(r, near=r.get("near")))                       # не місце: копія в словник
    return out
def повна(речі):
    return [р for р in речі if р["слот"] in ("верх", "низ")]          # не місце: без шару й не про місце
''',
    "потік.py": '''
import приймач as П
def суд(e):
    return П.якір(1, near=e.get("near"), сила=e["near"] * 2)          # місце: передано далі
def ознака(р):
    return dict(біля=bool(р.get("біля_обличчя")))                     # місце: копія через bool
def зразок(r):
    return dict(r, near=0.3)                                          # місце: поле записано сталою
''',
    "приймач.py": '''
def якір(x, near=None, сила=0.0):
    вага = 0.2 if near is None else near                              # місце: споживач near
    return вага * x + сила
def поріг(сила):
    return сила < 0.05                                                # не місце: загальний помічник
''',
    "силует_пропорції.py": '''
ЗОНИ_ПАРИ = dict(верх=("плечі", "груди"), низ=("стегна",))
def ролі(t):
    return {z: 1 for п, зз in ЗОНИ_ПАРИ.items() for z in зз}
''',
    "стенд_щось.py": '''
from колір_річ import SLOT_NEAR_FALLBACK
X = SLOT_NEAR_FALLBACK["шарф"]                                         # поза обсягом продукту
''',
}


def setUpModule():
    global ТЕКА, МІСЦЯ, ПРИЛАД
    ТЕКА = tempfile.TemporaryDirectory()
    os.makedirs(os.path.join(ТЕКА.name, "джерела"))
    for ім, текст in ДЕРЕВО.items():
        with open(os.path.join(ТЕКА.name, "джерела", ім), "w", encoding="utf-8") as ф:
            ф.write(текст)
    ПРИЛАД = П.Прилад(ТЕКА.name)
    МІСЦЯ = ПРИЛАД.лічити()


def tearDownModule():
    ТЕКА.cleanup()
    ОБСЯГ.скинути()


def рядок(файл, мітка):
    """Номер рядка дерева з міткою (текстом коду)."""
    for н, р in enumerate(ДЕРЕВО[файл].splitlines(), 1):
        if мітка in р:
            return н
    raise AssertionError("нема рядка «%s» у %s" % (мітка, файл))


class Місця(unittest.TestCase):
    def пункт(self, файл, мітка):
        return (МІСЦЯ.get((файл, рядок(файл, мітка))) or (None,))[0]

    def test_стала_класу_й_обгортка(self):
        self.assertEqual(self.пункт("колір_річ.py", "база = SLOT_NEAR_FALLBACK"), 1)
        self.assertEqual(self.пункт("правила.py", "О.біля_обличчя(р"), 1)
        self.assertEqual(self.пункт("обгортка.py", "return _ns(слот)"), 1)
        self.assertIn(("обгортка", "біля_обличчя"), ПРИЛАД.обгортки)

    def test_похідна_таблиця(self):
        self.assertEqual(self.пункт("правила.py", "in О.ДАЛЕКІ"), 1)
        self.assertIsNone(self.пункт("обгортка.py", "ДАЛЕКІ = ["), "визначення похідної — не місце")

    def test_near_без_походження(self):
        self.assertEqual(self.пункт("правила.py", 'e["near"] >= NEAR_МІН]  '), 2)

    def test_власний_літерал(self):
        self.assertEqual(self.пункт("правила.py", '("сережки", "шарф")'), 3)

    def test_шар_над_шаром(self):
        self.assertEqual(self.пункт("шари.py", "пальто = next("), 5)
        self.assertEqual(self.пункт("шари.py", 'if пальто and s in'), 5)
        self.assertEqual(self.пункт("шари.py", 'bool(пальто.get("розстібнуте"))'), 2)

    def test_потік_поля(self):
        self.assertEqual(self.пункт("потік.py", 'near=e.get("near")'), 2)
        self.assertEqual(self.пункт("приймач.py", "вага = 0.2 if near is None"), 2)
        self.assertEqual(self.пункт("потік.py", 'bool(р.get("біля_обличчя"))'), 2)
        self.assertEqual(self.пункт("потік.py", "near=0.3"), 2)

    def test_волосся(self):
        self.assertEqual(self.пункт("обличчя.py", "return sum(C)"), 4)
        self.assertEqual(self.пункт("обличчя.py", 'any(v["C"] < 5'), 4)
        self.assertEqual(self.пункт("обличчя.py", "0.5 * sum(вол)"), 4)
        self.assertEqual(self.пункт("обличчя.py", "Lh = sum"), 4)
        self.assertEqual(self.пункт("обличчя.py", "abs(Lh -"), 4)


class НеМісця(unittest.TestCase):
    def test_запис_і_копія(self):
        for файл, мітка in (("правила.py", 'e["near_виміряний"]'), ("правила.py", 'р.get("місце")'),
                            ("правила.py", 'near=m["near"]'), ("правила.py", 'р.get("слот") == "верх"'),
                            ("обличчя.py", "return sum(вол) / len(вол)"), ("обличчя.py", 'return {k: v["L"]'),
                            ("обличчя.py", "return any(k.startswith"), ("шари.py", 'near=r.get("near")'),
                            ("шари.py", 'in ("верх", "низ")'), ("приймач.py", "return сила < 0.05"),
                            ("силует_пропорції.py", "for п, зз in ЗОНИ_ПАРИ")):
            with self.subTest(мітка=мітка):
                self.assertNotIn((файл, рядок(файл, мітка)), МІСЦЯ)

    def test_не_таблиця_й_обсяг(self):
        self.assertNotIn(("внутрішня_мова", "ЗОНИ_ВЕТО"), ПРИЛАД.таблиці, "частина іншої сталої — не вся вона")
        self.assertFalse([к for к in МІСЦЯ if к[0].startswith("стенд")], "стенд — поза обсягом продукту")


if __name__ == "__main__":
    unittest.main()

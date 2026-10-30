"""Звіряє повний облік області методу на V=0/10.

Власна перевірка виконавця, не незалежне приймання сімей кольору.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest


КОРІНЬ = Path(__file__).resolve().parents[2]
ШЛЯХ = КОРІНЬ / "джерела/лабораторія/колір_сім_ї_кінці.py"
СПЕЦИФІКАЦІЯ = importlib.util.spec_from_file_location("кінці", ШЛЯХ)
МОДУЛЬ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ)
СПЕЦИФІКАЦІЯ.loader.exec_module(МОДУЛЬ)
ОСНОВА = МОДУЛЬ.ОСНОВА


class ПеревіркаКінців(unittest.TestCase):
    """Зіставляє перетини, явні відмови й нейтральні точки з джерелами."""

    @classmethod
    def setUpClass(клас):
        """Читає округлений артефакт і чинний рушій renotation."""
        клас.бібліотека = ОСНОВА.залежності()
        клас.перетворити = staticmethod(МОДУЛЬ.зробити_перетворення(клас.бібліотека))
        клас.вхід = json.loads(МОДУЛЬ.ВХІД.read_text(encoding="utf-8"))
        клас.вихід = json.loads(МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))
        клас.нейтраль = json.loads(МОДУЛЬ.НЕЙТРАЛЬ.ВИХІД.read_text(encoding="utf-8"))

    def test_облік_всіх_граней(self):
        """Вибирає весь клас із джерела, зокрема необмежені та нейтральні частини."""
        очікувані = {i for i, грань in enumerate(self.вхід["межі"])
                     if грань["вісь"] == "V" and грань["координата"] in (0, 10)}
        номери = [x["грань"] for x in self.вихід["грані"]]
        self.assertEqual(set(номери), очікувані)
        self.assertEqual(len(номери), len(очікувані))
        self.assertEqual(self.вихід["раніше"], sorted(
            self.нейтраль["раніше"] + [x["грань"] for x in self.нейтраль["грані"]]))
        всі = номери + self.вихід["раніше"] + [x["грань"] for x in self.вихід["відкладені"]]
        self.assertEqual(sorted(всі), list(range(len(self.вхід["межі"]))))
        self.assertTrue(all(x["причина"] for x in self.вихід["відкладені"]))
        точки = sum(bool(x["образ"]) for x in self.вихід["грані"])
        self.assertEqual(self.вихід["підсумок"], {
            "попередніх_граней": len(self.вихід["раніше"]),
            "точкових_перетинів": точки,
            "порожніх_перетинів": len(номери) - точки,
            "відкладено": len(self.вихід["відкладені"]),
        })
        print(f"Облік: {len(номери)} кінцевих граней, {точки} точки, "
              f"{len(номери) - точки} порожніх; раніше {len(self.вихід['раніше'])}; "
              f"відкладено {len(self.вихід['відкладені'])}")

    def test_повне_розбиття_області(self):
        """Визначена й невизначена частини без прогалин точно відтворюють джерело."""
        променів = 0
        for запис in self.вихід["грані"]:
            джерело = self.вхід["межі"][запис["грань"]]
            self.assertEqual(запис["джерело"], джерело)
            H, C = джерело["інтервали"]
            область = запис["область"]
            self.assertEqual(len(область["невизначено"]), 1)
            невизначено = область["невизначено"][0]
            self.assertEqual(невизначено["H"], H)
            self.assertEqual(невизначено["C"], C)
            self.assertEqual(невизначено["замкненість_C"], [C[0] > 0, C[1] != "+inf"])
            променів += C[1] == "+inf"
            if C[0] == 0:
                self.assertEqual(область["визначено"], [{
                    "H": H, "C": [0, 0], "замкненість_C": [True, True]}])
                self.assertEqual(len(запис["образ"]), 1)
                self.assertIn("нейтральна точка", запис["статус"])
            else:
                self.assertEqual(область["визначено"], [])
                self.assertEqual(запис["образ"], [])
                self.assertIn("порожній перетин", запис["статус"])
        print(f"Повне розбиття: збережено {променів} необмежених C-променів")

    def test_відмова_чинної_бібліотеки(self):
        """Звіряє фактичну хроматичну гілку бібліотеки по всьому класу кінців."""
        from colour.notation.munsell import (
            munsell_colour_to_munsell_specification, munsell_specification_to_xyY)
        проб = 0
        for запис in self.вихід["грані"]:
            джерело = запис["джерело"]
            (a, b), (c, d) = джерело["інтервали"]
            C = [c, c + 1, c + 1000] if d == "+inf" else [c, (c + d) / 2, d]
            if c == 0:
                C[0] = 1e-12
            for H in (a, a + (b - a) * 0.137, (a + b) / 2, b):
                for хрома in C:
                    специфікація = munsell_colour_to_munsell_specification(
                        ОСНОВА.позначення(H, 5, хрома))
                    специфікація[1] = джерело["координата"]
                    with self.assertRaisesRegex(AssertionError, r"domain \[1, 9\]"):
                        munsell_specification_to_xyY(специфікація)
                    with self.assertRaisesRegex(ValueError, "не визначений"):
                        self.перетворити(H, джерело["координата"], хрома)
                    проб += 1
        print(f"Додатна C на кінцях: {проб} відмов бібліотеки й лабораторного адаптера")

    def test_нейтральні_точки_та_зшивання(self):
        """Точки збігаються з прямим N0/N10 і записаними кінцями нейтральної кривої."""
        максимум = 0
        for запис in self.вихід["грані"]:
            for образ in запис["образ"]:
                self.assertEqual(образ["вимірність"], 0)
                V = запис["джерело"]["координата"]
                посилання = образ["нейтраль"]
                self.assertEqual(посилання["V"], V)
                попередня = next(x for x in self.нейтраль["грані"]
                                  if x["грань"] == посилання["грань"])
                попередні = [вузол for відрізок in попередня["відрізки"]
                             for край, вузол in zip(відрізок["V"], відрізок["вузли"])
                             if край == V]
                self.assertEqual(попередні, [образ["вузол"]])
                lab, (θ, L, C) = образ["вузол"]
                self.assertIsNone(θ)
                self.assertAlmostEqual(L, lab[0])
                self.assertAlmostEqual(C, math.hypot(*lab[1:]))
                for H in (1, 2.5, 25, 50, 75, 100, 101):
                    точне = self.перетворити(H, V, 0)
                    self.assertIsNone(точне[1][0])
                    максимум = max(максимум, math.dist(lab, точне[0]))
        self.assertLess(максимум, 1e-8)
        self.assertEqual(self.перетворити(1, 0, 0), ((0, 0, 0), (None, 0, 0)))
        білий = self.перетворити(1, 10, 0)
        self.assertAlmostEqual(білий[1][1], 100, delta=0.0001)
        self.assertGreater(білий[1][2], 0)
        print(f"Кінці нейтралі: 14 проб; найбільша ΔLab76 округлення {максимум}")

    def test_непридатні_координати(self):
        """Необласні й невизначені входи не перетворюються на нейтральні точки."""
        for координати in ((0, 0, 0), (102, 10, 0), (1, 5, 0), (1, 0, -1),
                           (math.nan, 0, 0), (1, math.inf, 0), (1, 10, math.nan),
                           (1, 0, math.inf), (1, 0, -math.inf)):
            with self.assertRaises(ValueError):
                self.перетворити(*координати)
        for грань in (
                {"вісь": "H", "координата": 0},
                {"вісь": "V", "координата": 5},
                {"вісь": "V", "координата": 0, "інтервали": [[1, 101], [-1, 1]]},
                {"вісь": "V", "координата": 10, "інтервали": [[1, 101], [0, math.nan]]}):
            with self.assertRaises(ValueError):
                МОДУЛЬ.подати_грань(грань, self.перетворити, self.нейтраль)

    def test_походження(self):
        """Звіряє джерела, методи й транзитивне походження до зафіксованого рушія."""
        for запис in self.вихід["походження"] + self.вихід["походження_перетворення"]:
            назва = запис["файл"]
            if назва.startswith("colour/"):
                шлях = Path(self.бібліотека.__file__).parent / назва.removeprefix("colour/")
            else:
                шлях = МОДУЛЬ.ВХІД.parent / назва
                if not шлях.is_file():
                    шлях = ОСНОВА.ДЖЕРЕЛА / назва
            хеш = hashlib.sha256(шлях.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            self.assertEqual(хеш, запис["sha256_lf"], назва)
        раніше, нейтраль = МОДУЛЬ.звірити_попереднє(self.бібліотека, self.вхід)
        self.assertEqual(раніше, self.вихід["раніше"])
        self.assertEqual(нейтраль, self.нейтраль)


if __name__ == "__main__":
    unittest.main()

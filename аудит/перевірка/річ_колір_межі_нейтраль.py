"""Звіряє всю нейтральну криву, її кінці та границю хроматичних граней.

Власна числова перевірка виконавця, не незалежне приймання сімей.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest


КОРІНЬ = Path(__file__).resolve().parents[2]
ШЛЯХ = КОРІНЬ / "джерела/лабораторія/колір_сім_ї_нейтраль.py"
СПЕЦИФІКАЦІЯ = importlib.util.spec_from_file_location("нейтраль", ШЛЯХ)
МОДУЛЬ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ)
СПЕЦИФІКАЦІЯ.loader.exec_module(МОДУЛЬ)
ОСНОВА = МОДУЛЬ.ОСНОВА


class ПеревіркаНейтралі(unittest.TestCase):
    """Перевіряє облік, покриття, нейтральність та числову узгодженість."""

    @classmethod
    def setUpClass(клас):
        """Готує прямі методи та читає округлений файл кривої."""
        клас.бібліотека = ОСНОВА.залежності()
        клас.перетворити = staticmethod(МОДУЛЬ.зробити_перетворення(клас.бібліотека))
        клас.хроматичне = staticmethod(ОСНОВА.зробити_перетворення(клас.бібліотека))
        клас.вхід = json.loads(МОДУЛЬ.ВХІД.read_text(encoding="utf-8"))
        клас.вихід = json.loads(МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))

    def test_облік_всіх_граней(self):
        """Вибирає нейтральний клас із геометрії та звіряє весь перелік джерела."""
        очікувані = {i for i, x in enumerate(self.вхід["межі"])
                     if x["вісь"] == "C" and x["координата"] == 0}
        готові = [x["грань"] for x in self.вихід["грані"]]
        всі = готові + self.вихід["раніше"] + [x["грань"] for x in self.вихід["відкладені"]]
        self.assertEqual(set(готові), очікувані)
        self.assertEqual(len(готові), len(очікувані))
        self.assertEqual(sorted(всі), list(range(len(self.вхід["межі"]))))
        self.assertTrue(all(x["причина"] for x in self.вихід["відкладені"]))
        for x in self.вихід["грані"]:
            self.assertEqual(x["джерело"], self.вхід["межі"][x["грань"]])
        print(f"Облік: нейтраль {len(готові)}, раніше {len(self.вихід['раніше'])}, відкладено {len(self.вихід['відкладені'])}")

    def test_покриття_і_стики(self):
        """Крива покриває весь замкнений V без прогалин, перекриттів і різних вузлів стику."""
        for грань in self.вихід["грані"]:
            низ, верх = грань["джерело"]["інтервали"][1]
            відрізки = sorted(грань["відрізки"], key=lambda x: x["V"])
            край, вузол = низ, None
            self.assertEqual(грань["вимірність"], 1)
            for відрізок in відрізки:
                a, b = відрізок["V"]
                self.assertEqual(a, край)
                self.assertGreater(b, a)
                if вузол is not None:
                    self.assertEqual(вузол, відрізок["вузли"][0])
                край, вузол = b, відрізок["вузли"][1]
            self.assertEqual(край, верх)

    def test_невизначений_тон_і_залишкова_хрома(self):
        """Тон відсутній навіть за ненульового числового залишку хроми."""
        максимальна = 0
        for грань in self.вихід["грані"]:
            for відрізок in грань["відрізки"]:
                for lab, (θ, L, C) in відрізок["вузли"]:
                    self.assertIsNone(θ)
                    self.assertTrue(all(math.isfinite(x) for x in lab))
                    self.assertAlmostEqual(L, lab[0])
                    self.assertAlmostEqual(C, math.hypot(lab[1], lab[2]))
                    максимальна = max(максимальна, C)
        self.assertGreater(максимальна, 0)
        self.assertLess(максимальна, self.вихід["цілі_похибки"][2])
        print(f"Найбільша збережена залишкова C*: {максимальна}")

    def test_кінці_і_масштаб_яскравості(self):
        """Чорний і білий досягаються без відтинання або повторної поправки MgO."""
        чорний, білий = self.перетворити(0), self.перетворити(10)
        self.assertEqual(чорний, ((0, 0, 0), (None, 0, 0)))
        self.assertAlmostEqual(білий[1][1], 100, delta=0.0001)
        self.assertIsNone(білий[1][0])
        xyY = self.бібліотека.notation.munsell_colour_to_xyY("N10")
        self.assertAlmostEqual(float(xyY[2]), 1, places=12)
        L = [self.перетворити(i / 100)[1][1] for i in range(1001)]
        self.assertTrue(all(a < b for a, b in zip(L, L[1:])))

    def test_границя_всіх_тонів(self):
        """Звіряє C→0 старого хроматичного перетворення у вибірці всього кола."""
        максимуми = []
        for C in (1e-4, 1e-6, 1e-8):
            похибки = [math.dist(self.перетворити(V)[0], self.хроматичне(H, V, C)[0])
                       for H in range(1, 102, 10) for V in (1, 2.5, 5, 7.5, 9, 9.5)]
            максимуми.append(max(похибки))
        self.assertLess(максимуми[-1], 1e-6)
        self.assertTrue(all(b < a / 50 for a, b in zip(максимуми, максимуми[1:])))
        print(f"Границя C→0: 198 проб, максимуми ΔLab76 {максимуми}")

    def test_пряме_перетворення_округленого_файла(self):
        """Звіряє всі вузли та густу іншу вибірку кожного відрізка з прямим методом."""
        максимум = [0.0] * 3
        проб = 0
        відрізків = 0
        for грань in self.вихід["грані"]:
            for відрізок in грань["відрізки"]:
                відрізків += 1
                a, b = відрізок["V"]
                for V, вузол in zip((a, b), відрізок["вузли"]):
                    self.assertLess(math.dist(self.перетворити(V)[0], вузол[0]), 1e-8)
                for i in range(1, 100):
                    u = i / 100
                    # Незалежна лінійна хорда округлених вузлів.
                    lab = [(1 - u) * x + u * y for x, y in
                           zip(відрізок["вузли"][0][0], відрізок["вузли"][1][0])]
                    точне = self.перетворити(a + u * (b - a))[0]
                    вимір = (math.dist(точне, lab), abs(точне[0] - lab[0]),
                             abs(math.hypot(*точне[1:]) - math.hypot(*lab[1:])))
                    максимум = list(map(max, максимум, вимір))
                    проб += 1
        self.assertTrue(all(x <= ціль for x, ціль in zip(максимум, self.вихід["цілі_похибки"])))
        print(f"Крива: {відрізків} відрізків, {проб} інших проб; максимуми ΔLab76/L*/C*: {максимум}")

    def test_непридатний_вхід(self):
        """Невизначені та позаобласні координати не перетворюються на нейтраль."""
        for V in (-1, 10.001, math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                self.перетворити(V)

    def test_походження(self):
        """Усі джерела, методи й попередні артефакти мають чинний LF-хеш."""
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


if __name__ == "__main__":
    unittest.main()

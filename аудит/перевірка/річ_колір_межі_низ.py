"""Звіряє нижні часткові C-грані з прямим методом і повним джерелом.

Власна перевірка виконавця, не незалежне приймання сімей.
"""
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import unittest


КОРІНЬ = Path(__file__).resolve().parents[2]
ШЛЯХ = КОРІНЬ / "джерела/лабораторія/колір_сім_ї_низ.py"
СПЕЦИФІКАЦІЯ = importlib.util.spec_from_file_location("низ", ШЛЯХ)
МОДУЛЬ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ)
СПЕЦИФІКАЦІЯ.loader.exec_module(МОДУЛЬ)
ОСНОВА = МОДУЛЬ.ОСНОВА
СПЕЦИФІКАЦІЯ_ПРОБ = importlib.util.spec_from_file_location(
    "проби_контурів", Path(__file__).with_name("річ_колір_межі_контури.py"))
ПРОБИ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ_ПРОБ)
СПЕЦИФІКАЦІЯ_ПРОБ.loader.exec_module(ПРОБИ)


class ПеревіркаНизу(unittest.TestCase):
    """Перевіряє геометрію, область, незалежні числові проби та походження."""

    @classmethod
    def setUpClass(клас):
        """Читає записаний вихід, джерело й точну версію renotation."""
        клас.бібліотека = ОСНОВА.залежності()
        клас.вхід = json.loads(МОДУЛЬ.ВХІД.read_text(encoding="utf-8"))
        клас.вихід = json.loads(МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))
        клас.точне = staticmethod(ОСНОВА.зробити_перетворення(клас.бібліотека))
        клас.перетворити = staticmethod(МОДУЛЬ.зробити_перетворення(клас.бібліотека))

    def test_повний_клас_та_облік(self):
        """Вибирає клас із геометрії джерела незалежно від генератора."""
        очікувані = {i for i, g in enumerate(self.вхід["межі"])
                     if g["вісь"] == "C" and 0 < g["координата"] < 2
                     and g["інтервали"][1][0] == 0
                     and 1 < g["інтервали"][1][1] < 10}
        номери = [x["грань"] for x in self.вихід["грані"]]
        self.assertEqual(set(номери), очікувані)
        self.assertEqual(len(номери), len(очікувані))
        попередні = json.loads(МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8"))
        self.assertEqual(self.вихід["раніше"], sorted(
            попередні["раніше"] + [x["грань"] for x in попередні["грані"]]))
        всі = номери + self.вихід["раніше"] + [x["грань"] for x in self.вихід["відкладені"]]
        self.assertEqual(sorted(всі), list(range(len(self.вхід["межі"]))))
        self.assertTrue(all(x["причина"] for x in self.вихід["відкладені"]))
        print(f"Облік: нових {len(номери)}, попередніх {len(self.вихід['раніше'])}, "
              f"відкладено {len(self.вихід['відкладені'])}")

    def test_покриття_та_повна_область(self):
        """Основна сітка й нижня смуга розбивають кожну повну вихідну грань."""
        for запис in self.вихід["грані"]:
            джерело = self.вхід["межі"][запис["грань"]]
            self.assertEqual(запис["джерело"], джерело)
            H, (_, V1) = джерело["інтервали"]
            self.assertEqual(запис["область"], {
                "основна_HV": [H, [1, V1]], "нижня_HV": [H, [0, 1]],
                "нижня_замкненість_V": [True, False],
                "визначено_внизу": "предикат_нижньої_смуги",
                "невизначено_внизу": "not предикат_нижньої_смуги"})
            ПРОБИ.звірити_покриття(self, [H, [1, V1]], запис["ділянки"])

    def test_дійсна_нижня_область(self):
        """Зіставляє прийняття й відмови з бібліотекою, зокрема біля округлення."""
        from colour.notation.munsell import munsell_specification_to_xyY
        from colour.notation.munsell import munsell_colour_to_munsell_specification
        from colour.constants import THRESHOLD_INTEGER
        відмов, прийнято = 0, 0
        поріг = 1 - THRESHOLD_INTEGER
        значення = [0, 0.01, 0.5, 0.99, 0.998, 0.999, 0.9991, 0.9995,
                    1, 1.0005, 1.001, 1.01, поріг - 1e-10, поріг + 1e-10,
                    math.nextafter(поріг, -math.inf), math.nextafter(поріг, math.inf)]
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            (a, b), _ = грань["інтервали"]
            for H, V in itertools.product((a, a + (b - a) * 0.137, b), значення):
                # V=0 не приймає текстовий адаптер, тому парсимо при V=1
                # і підставляємо канонічно записане V у пряму специфікацію.
                специфікація = munsell_colour_to_munsell_specification(
                    ОСНОВА.позначення(H, 1, грань["координата"]))
                специфікація[1] = float(f"{V:.12g}")
                try:
                    munsell_specification_to_xyY(специфікація)
                except (AssertionError, ValueError):
                    self.assertFalse(МОДУЛЬ.визначено(V), (H, V))
                    with self.assertRaises(ValueError):
                        МОДУЛЬ.перетворити_грань(self.перетворити, грань, H, V)
                    відмов += 1
                else:
                    self.assertTrue(МОДУЛЬ.визначено(V), (H, V))
                    self.assertEqual(МОДУЛЬ.перетворити_грань(
                        self.перетворити, грань, H, V), self.точне(H, V, грань["координата"]))
                    прийнято += 1
        self.assertGreater(відмов, 0)
        self.assertGreater(прийнято, 0)
        print(f"Нижня область: {прийнято} прийнято, {відмов} явних відмов; збіг із бібліотекою")

    def test_фізична_область_xy(self):
        """Незалежно звіряє всі табличні вузли C2 та запас диска до краю xy."""
        from colour.notation.munsell import (xyY_from_renotation,
                                            CCS_ILLUMINANT_MUNSELL)
        білий = tuple(float(x) for x in CCS_ILLUMINANT_MUNSELL)
        відстань = min(білий[0], білий[1], (1 - sum(білий)) / math.sqrt(2))
        запас = math.inf
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            вузли = [xyY_from_renotation([H, V, 2, код])[:2]
                     for V in range(1, math.ceil(грань["інтервали"][1][1]) + 1)
                     for код in range(1, 11) for H in (2.5, 5, 7.5, 10)]
            радіус = max(math.dist(xy, білий) for xy in вузли) * грань["координата"] / 2
            межа = запис["обмеження_xy"]
            self.assertEqual(межа["вузлів_C2"], len(вузли))
            self.assertAlmostEqual(межа["радіус"], радіус, places=8)
            self.assertAlmostEqual(межа["запас_xy"], відстань - радіус, places=8)
            self.assertGreater(межа["запас_xy"], 0)
            запас = min(запас, відстань - радіус)
        print(f"Усі табличні вузли C2: мінімальний запас диска xy {запас:.9f}")

    def test_інші_внутрішні_проби(self):
        """Міряє округлений інтерполянт у точках, яких не було в генераторі."""
        максимум, проб = [0.0] * 4, 0
        цілі = self.вихід["цілі_похибки"]
        for запис in self.вихід["грані"]:
            C = запис["джерело"]["координата"]
            for ділянка in запис["ділянки"]:
                for u, v in ((0.137, 0.419), (0.817, 0.263)):
                    (a, b), (c, d) = ділянка["HV"]
                    точне = self.точне(a + u * (b - a), c + v * (d - c), C)
                    lab = ОСНОВА.наблизити([x[0] for x in ділянка["вузли"]], u, v)
                    похибки = ОСНОВА.похибки(точне, (lab, ОСНОВА.координати_з_lab(lab)))
                    self.assertTrue(all(x <= y for x, y in zip(похибки, цілі)), похибки)
                    максимум = list(map(max, максимум, похибки))
                    проб += 1
        print(f"Інші внутрішні проби {проб}; максимуми ΔLab/θ/L*/C*: {максимум}")

    def test_вузли_та_стики(self):
        """Звіряє всі вузли та внутрішні й міжгранні стики з прямим методом."""
        максимум, проб = [0.0] * 4, 0
        for запис in self.вихід["грані"]:
            C = запис["джерело"]["координата"]
            for ділянка in запис["ділянки"]:
                (a, b), (c, d) = ділянка["HV"]
                for (H, V), вузол in zip(((a, c), (b, c), (b, d), (a, d)), ділянка["вузли"]):
                    self.assertLess(math.dist(вузол[0], self.точне(H, V, C)[0]), 1e-8)
                for u, v in ((0, 0.371), (1, 0.371), (0.371, 0), (0.371, 1)):
                    точне = self.точне(a + u * (b - a), c + v * (d - c), C)
                    lab = ОСНОВА.наблизити([x[0] for x in ділянка["вузли"]], u, v)
                    похибки = ОСНОВА.похибки(точне, (lab, ОСНОВА.координати_з_lab(lab)))
                    self.assertTrue(all(x <= y for x, y in zip(
                        похибки, self.вихід["цілі_похибки"])), похибки)
                    максимум = list(map(max, максимум, похибки))
                    проб += 1
        # Точний метод дає тотожні вузли на спільних H-краях і шві H=1/101.
        for H in (1, 6, 24, 38, 60, 79, 101):
            сусіди = [x["джерело"] for x in self.вихід["грані"]
                      if H in x["джерело"]["інтервали"][0]]
            for V in (0.9995, 1, 1.137, 1.5):
                вузли = [МОДУЛЬ.перетворити_грань(self.перетворити, g, H, V)
                         for g in сусіди]
                self.assertTrue(all(x == вузли[0] for x in вузли))
        for V in (0.9995, 1, 1.137, 2):
            self.assertEqual(self.перетворити(1, V, 1), self.перетворити(101, V, 1))
        print(f"Проби країв {проб}; максимуми до прямого методу: {максимум}")

    def test_походження_та_відмова_на_підміну(self):
        """Звіряє хеші та відмову на зміну джерела попереднього виходу."""
        МОДУЛЬ.звірити_попереднє(self.бібліотека, self.вхід)
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
        інший = json.loads(json.dumps(self.вхід))
        інший["межі"][self.вихід["раніше"][0]]["сім_ї"] = ["підміна"]
        with self.assertRaisesRegex(ValueError, "джерело"):
            МОДУЛЬ.звірити_попереднє(self.бібліотека, інший)

    def test_непридатні_та_позаобласні_входи(self):
        """Не вигадує кольору за непридатних координат або іншої грані."""
        for H, V, C in ((math.nan, 1, 1), (1, math.inf, 1), (1, 1, math.nan),
                        (0, 1, 1), (102, 1, 1), (1, -1, 1), (1, 0, 1),
                        (1, 10, 1), (1, 1, 0), (1, 1, 2)):
            with self.assertRaises(ValueError):
                self.перетворити(H, V, C)
        грань = self.вихід["грані"][0]["джерело"]
        with self.assertRaisesRegex(ValueError, "вихідною"):
            МОДУЛЬ.перетворити_грань(self.перетворити, грань, 1, 1)
        with self.assertRaisesRegex(ValueError, "Інший клас"):
            МОДУЛЬ.перетворити_грань(self.перетворити, self.вхід["межі"][0], 1, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

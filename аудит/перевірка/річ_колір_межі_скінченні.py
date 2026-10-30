"""Зіставляє скінченні процедурні поверхні з прямим Colour та джерелом.

Власна перевірка виконавця, не незалежне приймання сімей чи оболонки.
"""
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch


КОРІНЬ = Path(__file__).resolve().parents[2]
ШЛЯХ = КОРІНЬ / "джерела/лабораторія/колір_сім_ї_скінченні.py"
СПЕЦИФІКАЦІЯ = importlib.util.spec_from_file_location("скінченні", ШЛЯХ)
МОДУЛЬ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ)
СПЕЦИФІКАЦІЯ.loader.exec_module(МОДУЛЬ)
ОСНОВА = МОДУЛЬ.ОСНОВА


class ПеревіркаСкінченних(unittest.TestCase):
    """Звіряє повний клас, область методу, точні образи та походження."""

    @classmethod
    def setUpClass(клас):
        """Читає вихід методу, повне джерело та зафіксовані залежності."""
        клас.бібліотека = ОСНОВА.залежності()
        клас.вхід = json.loads(МОДУЛЬ.ВХІД.read_text(encoding="utf-8"))
        клас.вихід = json.loads(МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))
        клас.точне = staticmethod(ОСНОВА.зробити_перетворення(клас.бібліотека))

    def пряме(self, H, V, C):
        """Кличе бібліотеку без нового предиката та перевіряє фізичний XYZ."""
        colour = self.бібліотека
        try:
            xyY = colour.notation.munsell_colour_to_xyY(ОСНОВА.позначення(H, V, C))
        except (AssertionError, ValueError):
            return None
        xyz = colour.xyY_to_XYZ(xyY)
        if not all(math.isfinite(float(x)) for x in xyz) or min(xyz) < 0:
            return None
        xyz = colour.adaptation.chromatic_adaptation_VonKries(
            xyz, ОСНОВА.БІЛІ["C"], ОСНОВА.БІЛІ["D65"], transform="Bradford")
        lab = colour.XYZ_to_Lab(xyz, illuminant=colour.XYZ_to_xy(ОСНОВА.БІЛІ["D65"]))
        return tuple(float(x) for x in lab)

    def зіставити(self, грань, u, v):
        """Звіряє належність області та образ без використання вибору проб генератора."""
        H, V, C = ((грань["координата"], u, v) if грань["вісь"] == "H"
                   else (u, v, грань["координата"]))
        пряме = self.пряме(H, V, C)
        запис = МОДУЛЬ.перетворити_грань(self.точне, грань, u, v)
        self.assertEqual(запис["HVC"], [H, V, C])
        if пряме is None:
            self.assertEqual(запис["стан"], "невизначено", (H, V, C))
            self.assertNotIn("Lab", запис)
            self.assertNotIn("θLC", запис)
            self.assertTrue(запис["причина"])
        else:
            self.assertEqual(запис["стан"], "визначено", (H, V, C))
            self.assertLess(math.dist(запис["Lab"], пряме), 1e-10)
            self.assertEqual(запис["θLC"], ОСНОВА.координати_з_lab(запис["Lab"]))
        return пряме is not None

    def test_повний_клас_та_облік(self):
        """Обирає весь клас незалежно від предиката нового генератора."""
        низ = json.loads(МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8"))
        очікувані = {x["грань"] for x in низ["відкладені"]
                     if all(isinstance(t, (int, float)) for p in
                            self.вхід["межі"][x["грань"]]["інтервали"] for t in p)}
        номери = [x["грань"] for x in self.вихід["грані"]]
        self.assertEqual(set(номери), очікувані)
        self.assertEqual(len(номери), len(очікувані))
        self.assertEqual(len(номери), 33)
        self.assertEqual(self.вихід["раніше"], sorted(
            низ["раніше"] + [x["грань"] for x in низ["грані"]]))
        всі = номери + self.вихід["раніше"] + [x["грань"] for x in self.вихід["відкладені"]]
        self.assertEqual(sorted(всі), list(range(len(self.вхід["межі"]))))
        for запис in self.вихід["відкладені"]:
            self.assertTrue(any("+inf" in p for p in self.вхід["межі"][запис["грань"]]["інтервали"]))
        print(f"Облік: {len(self.вихід['раніше'])} попередніх + {len(номери)} нових + "
              f"{len(self.вихід['відкладені'])} відкладених = {len(всі)}")

    def test_цілі_параметричні_області(self):
        """Повні замкнені прямокутники повторюють джерело, без обрізання кінців."""
        for запис in self.вихід["грані"]:
            грань = self.вхід["межі"][запис["грань"]]
            self.assertEqual(запис["джерело"], грань)
            self.assertEqual(запис["межі"], грань["інтервали"])
            self.assertEqual(запис["замкненість"], [[True, True], [True, True]])
            self.assertEqual(запис["параметри"], ["V", "C"] if грань["вісь"] == "H" else ["H", "V"])
            for u, v in itertools.product(*грань["інтервали"]):
                self.зіставити(грань, u, v)

    def test_інші_внутрішні_проби(self):
        """Звіряє прямий метод у нових точках усіх 33 граней, без інтерполяції."""
        прийнято = відмов = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            (a, b), (c, d) = грань["інтервали"]
            for s, t in itertools.product((0.031, 0.137, 0.419, 0.817, 0.973), repeat=2):
                if self.зіставити(грань, a + (b - a) * s, c + (d - c) * t):
                    прийнято += 1
                else:
                    відмов += 1
        self.assertGreater(прийнято, 0)
        self.assertGreater(відмов, 0)
        print(f"Інші внутрішні проби: {прийнято} прийнять, {відмов} відмов")

    def test_смуги_округлення_V(self):
        """Зіставляє гілки V з бібліотекою обабіч порогів і в сусідніх float."""
        from colour.constants import THRESHOLD_INTEGER
        значення = [0, 0.5, 0.998, 1, 1.001, 8.999, 9, 9.5, 9.998, 10]
        for межа in (1 - THRESHOLD_INTEGER, 10 - THRESHOLD_INTEGER):
            значення.extend((межа - 1e-10, math.nextafter(межа, -math.inf), межа,
                             math.nextafter(межа, math.inf), межа + 1e-10))
        прийнято = відмов = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            V_вісь = 0 if грань["вісь"] == "H" else 1
            for V in значення:
                if not грань["інтервали"][V_вісь][0] <= V <= грань["інтервали"][V_вісь][1]:
                    continue
                a, b = грань["інтервали"][1 - V_вісь]
                for t in (a, a + (b - a) * 0.263, b):
                    u, v = (V, t) if V_вісь == 0 else (t, V)
                    if self.зіставити(грань, u, v):
                        прийнято += 1
                    else:
                        відмов += 1
        print(f"Проби округлення V: {прийнято} прийнять, {відмов} відмов")

    def test_записані_свідки(self):
        """Скінченні записані образи відтворюються; відмови не містять координат."""
        прийнято = відмов = 0
        максимум = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            for свідок in запис["свідки"]:
                H, V, C = свідок["HVC"]
                u, v = (V, C) if грань["вісь"] == "H" else (H, V)
                поточний = МОДУЛЬ.перетворити_грань(self.точне, грань, u, v)
                self.assertEqual(ОСНОВА.округлити(поточний), свідок)
                if свідок["стан"] == "визначено":
                    максимум = max(максимум, math.dist(свідок["Lab"], self.пряме(H, V, C)))
                    self.assertTrue(all(math.isfinite(x) for x in свідок["Lab"] + свідок["θLC"]))
                    прийнято += 1
                else:
                    self.assertNotIn("Lab", свідок)
                    self.assertNotIn("θLC", свідок)
                    відмов += 1
        self.assertLess(максимум, 1e-8)
        print(f"Записані свідки: {прийнято} прийнять, {відмов} відмов; ΔLab округлення {максимум}")

    def test_походження_й_підміна(self):
        """Звіряє весь ланцюг SHA-256 та відмову при зміні попереднього джерела."""
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
        низ = json.loads(МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8"))
        інший["межі"][низ["грані"][0]["грань"]]["сім_ї"] = ["підміна"]
        with self.assertRaisesRegex(ValueError, "джерело"):
            МОДУЛЬ.звірити_попереднє(self.бібліотека, інший)
        with patch.object(МОДУЛЬ.ПОПЕРЕДНІЙ, "ВИХІД", МОДУЛЬ.ВИХІД):
            with self.assertRaises(ValueError):
                МОДУЛЬ.звірити_попереднє(self.бібліотека, self.вхід)

    def test_непридатні_виклики_не_стають_образом(self):
        """Помилки параметрів та неочікувані винятки не маскуються невизначеністю."""
        грань = self.вихід["грані"][0]["джерело"]
        (a, b), (c, d) = грань["інтервали"]
        for u, v in ((math.nan, c), (a, math.inf), (a - 1, c), (a, d + 1)):
            with self.assertRaises(ValueError):
                МОДУЛЬ.перетворити_грань(self.точне, грань, u, v)
        for інша in (self.вхід["межі"][x["грань"]] for x in self.вихід["відкладені"]):
            with self.assertRaisesRegex(ValueError, "Інший клас"):
                МОДУЛЬ.перетворити_грань(self.точне, інша, 1, 1)
        for інша in self.вхід["межі"]:
            if інша["вісь"] == "C" and інша["координата"] == 0:
                self.assertFalse(МОДУЛЬ.обрано(інша))
        with patch.object(ОСНОВА, "позначення", side_effect=RuntimeError("неочікувано")):
            точне = ОСНОВА.зробити_перетворення(self.бібліотека)
            with self.assertRaisesRegex(RuntimeError, "неочікувано"):
                МОДУЛЬ.перетворити_грань(точне, грань, (a + b) / 2, (c + d) / 2)

    def test_сумісність_стику_і_шва(self):
        """Точні спільні точки C/H-граней і шов H=1/101 дають той самий образ."""
        точок = 0
        H_грані = [x["джерело"] for x in self.вихід["грані"] if x["джерело"]["вісь"] == "H"]
        C_грані = [x["джерело"] for x in self.вихід["грані"] if x["джерело"]["вісь"] == "C"]
        for H_грань, C_грань in itertools.product(H_грані, C_грані):
            H, C = H_грань["координата"], C_грань["координата"]
            if not C_грань["інтервали"][0][0] <= H <= C_грань["інтервали"][0][1]:
                continue
            if not H_грань["інтервали"][1][0] <= C <= H_грань["інтервали"][1][1]:
                continue
            a = max(H_грань["інтервали"][0][0], C_грань["інтервали"][1][0])
            b = min(H_грань["інтервали"][0][1], C_грань["інтервали"][1][1])
            if a > b:
                continue
            for V in (a, (a + b) / 2, b):
                self.assertEqual(МОДУЛЬ.перетворити_грань(self.точне, H_грань, V, C),
                                 МОДУЛЬ.перетворити_грань(self.точне, C_грань, H, V))
                точок += 1
        self.assertGreater(точок, 0)
        for V in (0.9995, 1, 2.5, 6.5, 9, 9.5, 9.9985):
            for C in (1, 1.5, 2):
                self.assertEqual(self.точне(1, V, C), self.точне(101, V, C))
        print(f"Спільних точок H/C-граней: {точок}; проб циклічного шва: 21")


if __name__ == "__main__":
    unittest.main(verbosity=2)

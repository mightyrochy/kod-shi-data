"""Звіряє необмежені часткові поверхні з прямим Colour і повним джерелом.

Власна перевірка виконавця, не незалежне приймання сімей або оболонки.
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
ШЛЯХ = КОРІНЬ / "джерела/лабораторія/колір_сім_ї_необмежені.py"
СПЕЦИФІКАЦІЯ = importlib.util.spec_from_file_location("необмежені", ШЛЯХ)
МОДУЛЬ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ)
СПЕЦИФІКАЦІЯ.loader.exec_module(МОДУЛЬ)
ОСНОВА = МОДУЛЬ.ОСНОВА


class ПеревіркаНеобмежених(unittest.TestCase):
    """Перевіряє повноту класу, область, образи й необрізаний промінь C."""

    @classmethod
    def setUpClass(клас):
        """Читає вихід методу, повне джерело та зафіксований рушій."""
        клас.бібліотека = ОСНОВА.залежності()
        клас.вхід = json.loads(МОДУЛЬ.ВХІД.read_text(encoding="utf-8"))
        клас.вихід = json.loads(МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))
        клас.точне = staticmethod(ОСНОВА.зробити_перетворення(клас.бібліотека))

    def пряме(self, H, V, C):
        """Кличе Colour без нового предиката й перевіряє XYZ та бібліотечний Lab."""
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

    def зіставити(self, грань, u, C):
        """Зіставляє стан області та образ у точці, вибраній поза генератором."""
        H, V = (грань["координата"], u) if грань["вісь"] == "H" else (u, грань["координата"])
        пряме = self.пряме(H, V, C)
        запис = МОДУЛЬ.перетворити_грань(self.точне, грань, u, C)
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

    def test_повний_облік_і_області(self):
        """Незалежно обирає решту 37 граней і повністю покриває всі 234 номери."""
        попереднє = json.loads(МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8"))
        очікувані = {x["грань"] for x in попереднє["відкладені"]}
        номери = [x["грань"] for x in self.вихід["грані"]]
        self.assertEqual(set(номери), очікувані)
        self.assertEqual(len(номери), 37)
        self.assertEqual(self.вихід["відкладені"], [])
        self.assertEqual(self.вихід["раніше"], sorted(
            попереднє["раніше"] + [x["грань"] for x in попереднє["грані"]]))
        self.assertEqual(sorted(self.вихід["раніше"] + номери), list(range(234)))
        осі = []
        for запис in self.вихід["грані"]:
            грань = self.вхід["межі"][запис["грань"]]
            self.assertEqual(запис["джерело"], грань)
            self.assertEqual(запис["межі"], грань["інтервали"])
            self.assertEqual(запис["замкненість"], [[True, True], [True, False]])
            self.assertEqual(грань["інтервали"][1][1], "+inf")
            self.assertEqual(запис["параметри"], ["V", "C"] if грань["вісь"] == "H" else ["H", "C"])
            осі.append(грань["вісь"])
        self.assertEqual((осі.count("H"), осі.count("V")), (26, 11))
        print("Облік: 197 попередніх + 37 нових + 0 відкладених = 234")

    def test_інші_точки_включно_з_далеким_C(self):
        """Звіряє повні промені без припущення про монотонність області."""
        прийнято = відмов = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            (a, b), (c, _) = грань["інтервали"]
            for s, δ in itertools.product((0, 0.137, 0.419, 0.973, 1),
                                          (0, 0.317, 2.729, 9.31, 31.7, 127.1, 1e6)):
                if self.зіставити(грань, a + (b - a) * s, c + δ):
                    прийнято += 1
                else:
                    відмов += 1
        self.assertGreater(прийнято, 0)
        self.assertGreater(відмов, 0)
        print(f"Інші точки променів: {прийнято} прийнять, {відмов} відмов")

    def test_округлення_V(self):
        """Звіряє кінці та пороги округлення V з прямим методом."""
        from colour.constants import THRESHOLD_INTEGER
        значення = [0, 0.5, 1, 9, 9.5, 10]
        for межа in (1 - THRESHOLD_INTEGER, 10 - THRESHOLD_INTEGER):
            значення.extend((межа - 1e-10, math.nextafter(межа, -math.inf), межа,
                             math.nextafter(межа, math.inf), межа + 1e-10))
        прийнято = відмов = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            if грань["вісь"] != "H":
                continue
            (a, b), (c, _) = грань["інтервали"]
            for V in значення:
                if a <= V <= b:
                    for C in (c, c + 3.17, c + 127):
                        if self.зіставити(грань, V, C):
                            прийнято += 1
                        else:
                            відмов += 1
        print(f"Округлення V: {прийнято} прийнять, {відмов} відмов")

    def test_свідки(self):
        """Відтворює записані свідки, координати та причини невизначеності."""
        прийнято = відмов = 0
        максимум = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            for свідок in запис["свідки"]:
                H, V, C = свідок["HVC"]
                u = V if грань["вісь"] == "H" else H
                поточний = МОДУЛЬ.перетворити_грань(self.точне, грань, u, C)
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
        print(f"Свідки: {прийнято} прийнять, {відмов} відмов; ΔLab округлення {максимум}")

    def test_походження_та_підміна(self):
        """Звіряє транзитивні SHA-256 й відмову при підміні джерела або обліку."""
        МОДУЛЬ.звірити_попереднє(self.бібліотека, self.вхід)
        for запис in self.вихід["походження"] + self.вихід["походження_перетворення"]:
            назва = запис["файл"]
            шлях = (Path(self.бібліотека.__file__).parent / назва.removeprefix("colour/")
                    if назва.startswith("colour/") else МОДУЛЬ.ВХІД.parent / назва)
            if not шлях.is_file():
                шлях = ОСНОВА.ДЖЕРЕЛА / назва
            хеш = hashlib.sha256(шлях.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            self.assertEqual(хеш, запис["sha256_lf"], назва)
        інший = json.loads(json.dumps(self.вхід))
        попереднє = json.loads(МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8"))
        інший["межі"][попереднє["грані"][0]["грань"]]["сім_ї"] = ["підміна"]
        with self.assertRaisesRegex(ValueError, "джерело"):
            МОДУЛЬ.звірити_попереднє(self.бібліотека, інший)
        with patch.object(МОДУЛЬ.ПОПЕРЕДНІЙ, "ВИХІД", МОДУЛЬ.ВИХІД):
            with self.assertRaises(ValueError):
                МОДУЛЬ.звірити_попереднє(self.бібліотека, self.вхід)

    def test_параметри_винятки_і_відсутність_стелі(self):
        """Відмовляє на непридатні виклики й передає будь-яку скінченну C методу."""
        грань = self.вихід["грані"][0]["джерело"]
        (a, b), (c, _) = грань["інтервали"]
        for u, C in ((math.nan, c), (a, math.inf), (a, math.nan), (a, -math.inf),
                     (a - 1, c), (b + 1, c), (a, math.nextafter(c, -math.inf))):
            with self.assertRaises(ValueError):
                МОДУЛЬ.перетворити_грань(self.точне, грань, u, C)
        for інша in self.вхід["межі"]:
            if not МОДУЛЬ.обрано(інша):
                with self.assertRaisesRegex(ValueError, "Інший клас"):
                    МОДУЛЬ.перетворити_грань(self.точне, інша, a, c)
        u = (a + b) / 2
        with patch.object(ОСНОВА, "позначення", side_effect=RuntimeError("неочікувано")):
            with self.assertRaisesRegex(RuntimeError, "неочікувано"):
                МОДУЛЬ.перетворити_грань(ОСНОВА.зробити_перетворення(self.бібліотека), грань, u, c)
        def свідок(H, V, C):
            """Підтверджує передачу великої C без затиску до рушія."""
            self.assertEqual(C, 1e100)
            raise ValueError("відмова рушія")
        запис = МОДУЛЬ.перетворити_грань(свідок, грань, u, 1e100)
        self.assertEqual(запис["відмова"], "відмова рушія")
        self.assertEqual(запис["HVC"][2], 1e100)

    def test_спільні_ребра(self):
        """Зіставляє H/V-стики нових і скінченних граней при однакових HVC."""
        попереднє = json.loads(МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8"))
        точок = 0
        for запис in self.вихід["грані"]:
            грань = запис["джерело"]
            if грань["вісь"] != "H":
                continue
            (a, b), (c, _) = грань["інтервали"]
            H = грань["координата"]
            for інша in (x["джерело"] for x in self.вихід["грані"]):
                if інша["вісь"] != "V" or not a <= інша["координата"] <= b:
                    continue
                if not інша["інтервали"][0][0] <= H <= інша["інтервали"][0][1]:
                    continue
                V = інша["координата"]
                for C in (max(c, інша["інтервали"][1][0]), max(c, інша["інтервали"][1][0]) + 31.7):
                    self.assertEqual(МОДУЛЬ.перетворити_грань(self.точне, грань, V, C),
                                     МОДУЛЬ.перетворити_грань(self.точне, інша, H, C))
                    точок += 1
            for інша in (x["джерело"] for x in попереднє["грані"]):
                if інша["вісь"] != "C" or інша["координата"] < c:
                    continue
                if not інша["інтервали"][0][0] <= H <= інша["інтервали"][0][1]:
                    continue
                низ = max(a, інша["інтервали"][1][0])
                верх = min(b, інша["інтервали"][1][1])
                if низ <= верх:
                    for V in (низ, (низ + верх) / 2, верх):
                        C = інша["координата"]
                        self.assertEqual(МОДУЛЬ.перетворити_грань(self.точне, грань, V, C),
                                         МОДУЛЬ.ПОПЕРЕДНІЙ.перетворити_грань(self.точне, інша, H, V))
                        точок += 1
        self.assertGreater(точок, 0)
        print(f"Спільні точки нових/скінченних граней: {точок}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

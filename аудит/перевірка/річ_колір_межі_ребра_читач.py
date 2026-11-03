"""Звіряє спільні часткові криві з прямим Colour та геометрією джерела.

Власна перевірка виконавця, не незалежне приймання сімей чи оболонки.
Запуск із кореня: python аудит/перевірка/річ_колір_межі_ребра_читач.py
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


КОРІНЬ = Path(__file__).resolve().parents[2]
ШЛЯХ = КОРІНЬ / "джерела/лабораторія/колір_сім_ї_ребра_читач.py"
СПЕЦИФІКАЦІЯ = importlib.util.spec_from_file_location("ребра", ШЛЯХ)
МОДУЛЬ = importlib.util.module_from_spec(СПЕЦИФІКАЦІЯ)
СПЕЦИФІКАЦІЯ.loader.exec_module(МОДУЛЬ)
ОСНОВА = МОДУЛЬ.ОСНОВА


class ПеревіркаРебер(unittest.TestCase):
    """Перевіряє повні області, прямий Lab, спільність, нейтраль та відмови."""

    @classmethod
    def setUpClass(клас):
        """Читає первинні поверхні, зшивання й вихід нового методу."""
        клас.бібліотека = ОСНОВА.залежності()
        клас.джерело = json.loads(ОСНОВА.ВХІД.read_text(encoding="utf-8"))
        клас.комплекс = json.loads(МОДУЛЬ.ЗШИВАННЯ.ВИХІД.read_text(encoding="utf-8"))
        клас.вихід = json.loads(МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))
        клас.перетворити = staticmethod(МОДУЛЬ.зробити_перетворення(клас.бібліотека))

    def пряме(self, H, V, C):
        """Обчислює незалежний бібліотечний Bradford/Lab без нового предиката V."""
        colour = self.бібліотека
        try:
            if C == 0:
                позначення = f"N{V:.12g}"
            else:
                # Форматувальник дає лише H: V=0/10 доходить до самої Colour.
                тон = ОСНОВА.позначення(H, 5, C).split()[0]
                позначення = f"{тон} {V:.12g}/{C:.12g}"
            xyY = colour.notation.munsell_colour_to_xyY(позначення)
        except (AssertionError, ValueError):
            return None
        xyz = colour.xyY_to_XYZ(xyY)
        if not all(math.isfinite(float(x)) for x in xyz) or min(xyz) < 0:
            return None
        xyz = colour.adaptation.chromatic_adaptation_VonKries(
            xyz, ОСНОВА.БІЛІ["C"], ОСНОВА.БІЛІ["D65"], transform="Bradford")
        lab = colour.XYZ_to_Lab(xyz, illuminant=colour.XYZ_to_xy(ОСНОВА.БІЛІ["D65"]))
        return tuple(float(x) for x in lab)

    def зіставити(self, ребро, t):
        """Зіставляє довільну точку з прямим методом та відсутність фальшивого кольору."""
        точка = list(ребро["фіксовані"])
        точка.insert("HVC".index(ребро["вісь"]), t)
        запис = МОДУЛЬ.читати_ребро(self.перетворити, ребро, t)
        self.assertEqual(tuple(запис["HVC"]), tuple(точка))
        lab = self.пряме(*точка)
        if lab is None:
            self.assertEqual(запис["стан"], "невизначено", точка)
            self.assertNotIn("Lab", запис)
            self.assertNotIn("θLC", запис)
            self.assertTrue(запис["причина"])
            return False
        self.assertEqual(запис["стан"], "визначено", точка)
        self.assertLess(math.dist(lab, запис["Lab"]), 1e-10)
        if точка[2] == 0:
            self.assertIsNone(запис["θLC"][0])
            L, C, _ = ОСНОВА.lch(запис["Lab"])
            self.assertEqual(запис["θLC"][1:], (L, C))
        else:
            self.assertEqual(запис["θLC"], ОСНОВА.координати_з_lab(запис["Lab"]))
        return True

    def test_повні_області_й_інші_точки(self):
        """Звіряє всі ребра на інших внутрішніх пробах, промені до C₀+10⁶."""
        прийнять = відмов = 0
        self.assertEqual(len(self.вихід["ребра"]), len(self.комплекс["ребра"]))
        for i, (ребро, запис) in enumerate(zip(self.комплекс["ребра"], self.вихід["ребра"])):
            self.assertEqual(запис["ребро"], i)
            self.assertEqual(запис["межі"], ребро["інтервал"])
            self.assertEqual(запис["параметр"], ребро["вісь"])
            self.assertEqual(запис["замкненість"], [True, ребро["інтервал"][1] != "+inf"])
            a, b = ребро["інтервал"]
            точки = [a + d for d in (0.317, 9.31, 1e6)] if b == "+inf" else [
                a + (b - a) * s for s in (0.137, 0.613, 0.973)]
            for t in точки:
                if self.зіставити(ребро, t):
                    прийнять += 1
                else:
                    відмов += 1
        self.assertGreater(прийнять, 0)
        self.assertGreater(відмов, 0)
        print(f"Інші точки всіх ребер: {прийнять} прийнять, {відмов} відмов")

    def test_округлення_V(self):
        """Звіряє кінці та обидва боки бібліотечних порогів V на всіх V-ребрах."""
        from colour.constants import THRESHOLD_INTEGER
        значення = [0, 0.5, 1, 9, 9.5, 10]
        for межа in (1 - THRESHOLD_INTEGER, 10 - THRESHOLD_INTEGER):
            значення.extend((межа - 1e-10, math.nextafter(межа, -math.inf), межа,
                             math.nextafter(межа, math.inf), межа + 1e-10))
        прийнять = відмов = 0
        for ребро in self.комплекс["ребра"]:
            if ребро["вісь"] != "V":
                continue
            a, b = ребро["інтервал"]
            for V in значення:
                if a <= V <= b:
                    if self.зіставити(ребро, V):
                        прийнять += 1
                    else:
                        відмов += 1
        self.assertGreater(прийнять, 0)
        self.assertGreater(відмов, 0)
        print(f"Пороги V: {прийнять} прийнять, {відмов} відмов")

    def test_усі_суміжні_грані(self):
        """Обхід кожної грані читає той самий образ ребра з належною орієнтацією."""
        self.assertEqual(self.вихід["контури"], self.комплекс["контури"])
        self.assertEqual(self.вихід["оболонки_джерела"], self.комплекс["оболонки"])
        використань = процедурних = 0
        хроматичне = ОСНОВА.зробити_перетворення(self.бібліотека)
        for i, (грань, контур) in enumerate(zip(self.джерело["межі"], self.комплекс["контури"])):
            for посилання in контур:
                номер, знак = abs(посилання) - 1, 1 if посилання > 0 else -1
                ребро = self.комплекс["ребра"][номер]
                a, b = ребро["інтервал"]
                t = a + 0.419 if b == "+inf" else a + (b - a) * 0.419
                запис = МОДУЛЬ.читати_край(self.перетворити, self.комплекс, i, посилання, t)
                очікується = МОДУЛЬ.читати_ребро(self.перетворити, ребро, t)
                self.assertEqual(запис, dict(очікується, ребро=номер, орієнтація=знак))
                точка = list(очікується["HVC"])
                вісь = "HVC".index(грань["вісь"])
                # H=1 та H=101 — той самий шов, але параметри грані лишаються її власними.
                if вісь == 0 and точка[0] == 1 and грань["координата"] == 101:
                    точка[0] = 101
                if вісь != 0 and точка[0] == 1 and грань["інтервали"][0][0] > 1:
                    точка[0] = 101
                self.assertEqual(точка[вісь], грань["координата"])
                інші = [точка[j] for j in range(3) if j != вісь]
                for x, (низ, верх) in zip(інші, грань["інтервали"]):
                    self.assertGreaterEqual(x, низ)
                    self.assertLessEqual(x, math.inf if верх == "+inf" else верх)
                for метод in (МОДУЛЬ.СКІНЧЕННІ, МОДУЛЬ.ПОПЕРЕДНІЙ):
                    if метод.обрано(грань) and точка[2] > 0:
                        попереднє = метод.перетворити_грань(хроматичне, грань, *інші)
                        self.assertEqual(попереднє["стан"], запис["стан"])
                        if запис["стан"] == "визначено":
                            self.assertEqual(попереднє["Lab"], запис["Lab"])
                        процедурних += 1
                використань += 1
        print(f"Використань спільних ребер: {використань}; попередніх процедурних країв: {процедурних}")

    def test_нейтраль_вершини_й_кінці(self):
        """Ототожнення вершин рівно за V на C=0; усі кінці кривих тотожні вершинам."""
        відображення = self.вихід["вершини_джерела"]
        групи = {}
        for номер, (H, V, C) in enumerate(self.комплекс["вершини"]):
            ключ = (None if C == 0 else H, V, C)
            групи.setdefault(ключ, []).append(номер)
        self.assertEqual(len(групи), len(self.вихід["вершини"]))
        for ключ, джерельні in групи.items():
            індекси = {відображення[i] for i in джерельні}
            self.assertEqual(len(індекси), 1)
            вершина = self.вихід["вершини"][індекси.pop()]
            self.assertEqual(tuple(вершина["ключ"]), ключ)
            self.assertEqual(вершина["джерельні_вершини"], джерельні)
        максимальна = 0
        for ребро, запис in zip(self.комплекс["ребра"], self.вихід["ребра"]):
            for t, стара, нова in zip(ребро["інтервал"], ребро["вершини"], запис["вершини"]):
                if t == "+inf":
                    self.assertIsNone(стара)
                    self.assertIsNone(нова)
                    continue
                self.assertEqual(нова, відображення[стара])
                образ = self.вихід["вершини"][нова]["образ"]
                точне = МОДУЛЬ.читати_ребро(self.перетворити, ребро, t)
                self.assertEqual(образ["стан"], точне["стан"])
                if образ["стан"] == "визначено":
                    максимальна = max(максимальна, math.dist(образ["Lab"], точне["Lab"]))
                    self.assertLess(math.dist(образ["Lab"], точне["Lab"]), 1e-8)
                else:
                    self.assertNotIn("Lab", образ)
            if запис["виродження_H"]:
                self.assertEqual(запис["вершини"][0], запис["вершини"][1])
                lab = [x["Lab"] for x in запис["свідки"]]
                self.assertTrue(all(x == lab[0] for x in lab))
                self.assertTrue(all(x["θLC"][0] is None for x in запис["свідки"]))
        print(f"Вершин: {len(відображення)} → {len(групи)}; округлення Lab ≤ {максимальна:.3g}")

    def test_шов_і_виродження_без_затиску(self):
        """Повний H схлопується тільки на C=0; C>0 на V=0/10 не підміняється нейтраллю."""
        for V in (0, 0.5, 5, 10):
            нейтраль = [self.перетворити(H, V, 0) for H in (1, 37.29, 101)]
            self.assertTrue(all(x == нейтраль[0] for x in нейтраль))
            self.assertIsNone(нейтраль[0]["θLC"][0])
        for V in (0, 10):
            for C in (0.001, 1, 1024, 1e6):
                запис = self.перетворити(1, V, C)
                self.assertEqual(запис["стан"], "невизначено")
                self.assertNotIn("Lab", запис)
        self.assertEqual(self.перетворити(1, 5, 4), self.перетворити(101, 5, 4))
        self.assertNotEqual(self.перетворити(1, 5, 4)["Lab"], self.перетворити(51, 5, 4)["Lab"])

    def test_помилки_виклику_й_неочікувані(self):
        """Нескінченність, чужий край та помилка програми відхиляються до запису кольору."""
        ребро = self.комплекс["ребра"][0]
        a, b = ребро["інтервал"]
        for t in (math.inf, -math.inf, math.nan, a - 1, b + 1):
            with self.assertRaises(ValueError):
                МОДУЛЬ.читати_ребро(self.перетворити, ребро, t)
        for точка in ((0, 5, 4), (102, 5, 4), (1, -1, 0), (1, 11, 0), (1, 5, -1)):
            with self.assertRaises(ValueError):
                self.перетворити(*точка)
        for грань, посилання in ((-1, 1), (len(self.комплекс["контури"]), 1), (0, 0)):
            with self.assertRaises(ValueError):
                МОДУЛЬ.читати_край(self.перетворити, self.комплекс, грань, посилання, a)
        def збій(*_):
            """Імітує неочікуваний збій числового рушія."""
            raise RuntimeError("Не очікувана відмова області")
        with patch.object(ОСНОВА, "зробити_перетворення", return_value=збій):
            перетворити = МОДУЛЬ.зробити_перетворення(self.бібліотека)
            with self.assertRaises(RuntimeError):
                перетворити(1, 5, 4)

    def test_відтворення_та_підміна(self):
        """Повторне породження побайтове; зміна зшивання чи попередніх граней відхиляється."""
        текст = МОДУЛЬ.серіалізувати(МОДУЛЬ.породити())
        self.assertEqual(текст, МОДУЛЬ.ВИХІД.read_text(encoding="utf-8"))
        for модуль, джерело in ((МОДУЛЬ.ЗШИВАННЯ, self.комплекс),
                                (МОДУЛЬ.ПОПЕРЕДНІЙ, json.loads(
                                    МОДУЛЬ.ПОПЕРЕДНІЙ.ВИХІД.read_text(encoding="utf-8")))):
            підміна = copy.deepcopy(джерело)
            if "контури" in підміна:
                підміна["контури"][0].pop()
            else:
                підміна["грані"][0]["джерело"]["координата"] += 0.125
            with tempfile.TemporaryDirectory() as тека:
                файл = Path(тека) / "підміна.json"
                файл.write_text(json.dumps(підміна), encoding="utf-8")
                with patch.object(модуль, "ВИХІД", файл), self.assertRaises(ValueError):
                    МОДУЛЬ.породити()


if __name__ == "__main__":
    unittest.main(verbosity=2)

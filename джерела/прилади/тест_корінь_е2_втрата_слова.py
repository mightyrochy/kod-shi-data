# -*- coding: utf-8 -*-
"""Прилад кореня Е2-втрата-слова на малому дереві: місця класу лічить, не місця — ні (без запуску продукту).

Запуск: `python3 джерела/прилади/тест_корінь_е2_втрата_слова.py` з кореня репозиторію."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import корінь_е2_втрата_слова as К  # noqa: E402

ПАСПОРТ = '''
ПОЛЯ_ПАСПОРТА = {
    "подія": {"поле": "event", "її_мовою": True},
    "решта": {"поле": "rest", "її_мовою": True},
    "нагода": {"поле": "occasion", "показ": "плитка"},
    "місце": {"поле": "place", "показ": "плитка"},
    "темп_c": {"поле": "temperature_c", "показ": "плитка"},
    "погода_відчуття": {"поле": "weather_feel", "показ": "плитка"},
    "хвилини": {"поле": "minute", "показ": "плитка"},
}
'''
ШАР = '''
_ПОЛЯ_EN = {
    "event": "her event in her words",
    "rest": "the rest she said",
    "occasion": "occasion code",
    "place": "place code",
    "temperature_c": "degrees; when she gave only a feeling, weather_feel then stays absent",
    "weather_feel": "her feeling of the weather",
}
'''
ПРОДУКТ = '''
ТАБЛ = {"а": "b"}
ПОЛЯ = ("нагода", "місце", "темп_c")
ПОЛЯ_ПОВНІ = ("нагода", "місце", "темп_c", "погода_відчуття")


def зріз(п):
    м = п.get("нагода")
    return п.get("решта")[-6:]


def з_крапкою(п):
    м = п.get("нагода")
    р = п.get("решта")
    return р[-6:] + ["…"] if len(р) > 6 else р


def з_лічбою(п):
    м = п.get("нагода")
    р = п.get("решта")
    лишено = р[-6:]
    return {"усього": len(р), "слова": лишено}


def кодом(п):
    м = п.get("нагода")
    return ТАБЛ.get(п.get("решта"))[:3]


def групи(g):
    return g["решта"][:1]


def писач(с):
    return {к: с.get(к) for к in ПОЛЯ}


def писач_повний(с):
    return {к: с.get(к) for к in ПОЛЯ_ПОВНІ}


def читач(мета, зони=None):
    return мета


def клич(п):
    return читач(п.get("нагода"), п.get("місце"))
'''
ПОКАЗ = '''
function останні() { return ЧАТ_П.slice(-8); }
function без_нового() { return ЧАТ_П.slice(0, -1); }
'''


class Прилад(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.тека = tempfile.TemporaryDirectory()
        д = os.path.join(cls.тека.name, "джерела")
        os.makedirs(os.path.join(д, "показ"))
        for ім, т in (("паспорт_поля.py", ПАСПОРТ), ("мовний_шар.py", ШАР), ("продукт.py", ПРОДУКТ),
                      ("показ/чат.js", ПОКАЗ)):
            with open(os.path.join(д, ім), "w", encoding="utf-8") as ф:
                ф.write(т)
        cls.старий = К.КОРІНЬ
        К.КОРІНЬ = cls.тека.name
        місця, не_місця, _ = К.зібрати()
        cls.місця = {(ф, cls.функція(ф, р), п) for ф, р, п, _ in місця}
        cls.не_місця = {(ф, cls.функція(ф, р), п) for ф, р, п, _ in не_місця}

    @classmethod
    def tearDownClass(cls):
        К.КОРІНЬ = cls.старий
        cls.тека.cleanup()

    @classmethod
    def функція(cls, ф, р):
        """Імʼя функції (чи сталої) за рядком, щоб тест не залежав від номерів рядків."""
        with open(os.path.join(К.КОРІНЬ, ф), encoding="utf-8") as фл:
            рядки = фл.read().splitlines()
        for і in range(р - 1, -1, -1):
            for поч in ("def ", "function "):
                if рядки[і].startswith(поч):
                    return рядки[і][len(поч):].split("(")[0]
            if і == р - 1 and "=" in рядки[і] and not рядки[і].startswith(" "):
                return рядки[і].split("=")[0].strip()
        return None

    def test_зріз_її_слів_без_крапки(self):
        self.assertIn(("джерела/продукт.py", "зріз", 1), self.місця)

    def test_зріз_із_крапкою_чи_лічбою_не_місце(self):
        self.assertNotIn(("джерела/продукт.py", "з_крапкою", 1), self.місця)
        self.assertIn(("джерела/продукт.py", "з_крапкою", 1), self.не_місця)
        self.assertNotIn(("джерела/продукт.py", "з_лічбою", 1), self.місця)

    def test_код_із_таблиці_й_чуже_решта_не_слова(self):
        """Значення з таблиці за її словом — код; `g["решта"]` групи — не паспорт."""
        self.assertNotIn(("джерела/продукт.py", "кодом", 1), self.місця)
        self.assertNotIn(("джерела/продукт.py", "групи", 1), self.місця)

    def test_перелік_без_другої_форми_пари(self):
        self.assertIn(("джерела/продукт.py", "ПОЛЯ", 2), self.місця)

    def test_хвилини_поза_переліком_не_місце(self):
        self.assertNotIn(("джерела/продукт.py", "ПОЛЯ_ПОВНІ", 2), self.місця)

    def test_параметр_не_читає_її_поля(self):
        self.assertIn(("джерела/продукт.py", "читач", 5), self.місця)

    def test_js_стрічка_розмови(self):
        self.assertIn(("джерела/показ/чат.js", "останні", 1), self.місця)
        self.assertNotIn(("джерела/показ/чат.js", "без_нового", 1), self.місця)


if __name__ == "__main__":
    unittest.main()

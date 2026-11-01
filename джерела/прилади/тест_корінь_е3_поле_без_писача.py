# -*- coding: utf-8 -*-
"""Тест приладу `корінь_е3_поле_без_писача.py` на малому дереві продукту: які читачі — місця, які — ні.

Дерево будується в тимчасовій теці, прилад іде окремим процесом (`--корінь`, `--json`), щоб модулі дерева не змішались
із модулями репозиторію. Запуск: python3 джерела/прилади/тест_корінь_е3_поле_без_писача.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ПРИЛАД = os.path.join(os.path.dirname(os.path.abspath(__file__)), "корінь_е3_поле_без_писача.py")

ДЕРЕВО = {
    "bridge.py": '''
import ендпойнти as Е
def виклик(ім, вхід):
    return {"пакет": Е.пакет}[ім](вхід)
''',
    "ендпойнти.py": '''
import json
import правила as П
def пакет(вхід):
    d = json.loads(вхід)
    kw = dict(d.get("сценарій") or {})
    kw["дощ"] = bool(d.get("погода"))
    п = d.get("паспорт") or {}
    return json.dumps(dict(р=П.рішення(**kw), м=П.мета_правило(п.get("мета")), в=П.верх(kw.get("гардероб")),
                           паспорт=dict(мета="лестити")))
''',
    "правила.py": '''
def рішення(господар=False, місце=None, дощ=False, тренд_сезону=None, шлях_фіду=None):
    з = 0
    if господар:
        з += 1
    if місце == "парк":
        з += 2
    if дощ:
        з += 3
    if тренд_сезону:
        з += 4
    if шлях_фіду:
        з += 5
    return з

def мета_правило(мета):
    if мета == "приховати":
        return 1
    return 0

def верх(гардероб=None):
    """Гардероб не передали — входу нема, і так і кажемо."""
    if гардероб is None:
        return "входу нема"
    return len(гардероб)
''',
    "паспорт_поля.py": '''
ПОЛЯ_ПАСПОРТА = {к: {"сценарій": ("опис", ())} for к in ("господар", "місце", "дощ", "мета", "гардероб",
                                                       "тренд_сезону")}
''',
    "суд_чеклісти.py": '''
ЗОВНІШНІ_ВХОДИ = {"тренд_сезону": "входу нема: тренди сезону ніхто не пише"}
''',
    "показ/сцена.js": '''
const сц = {місце: 'парк'};
''',
}


def прогін(дерево):
    with tempfile.TemporaryDirectory() as т:
        for шлях, текст in дерево.items():
            повний = os.path.join(т, "джерела", шлях)
            os.makedirs(os.path.dirname(повний), exist_ok=True)
            with open(повний, "w", encoding="utf-8") as ф:
                ф.write(текст)
        р = subprocess.run([sys.executable, ПРИЛАД, "--корінь", т, "--json"], capture_output=True, text=True,
                           timeout=300)
        assert р.returncode == 0, р.stderr
        return json.loads(р.stdout[:р.stdout.rindex("місць:")])


class ПолеБезПисача(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.р = прогін(ДЕРЕВО)
        cls.місця = {(м["поле"], м["пункт"]) for м in cls.р["місця"]}

    def test_п1_без_писача(self):
        """`господар` приходить лише з `**сценарію`, ніхто його не пише — місце п.1."""
        self.assertIn(("господар", 1), self.місця)

    def test_писачі_не_місця(self):
        """`місце` пише показ, `дощ` — код у носій сценарію."""
        поля = {п for п, _ in self.місця}
        self.assertNotIn("місце", поля)
        self.assertNotIn("дощ", поля)

    def test_п2_літерал_поза_писачем(self):
        """Паспорт пише `мета="лестити"`, гілка чекає `"приховати"` — місце п.2."""
        self.assertIn(("мета", 2), self.місця)

    def test_не_місця_класу(self):
        """`ЗОВНІШНІ_ВХОДИ` чекліста, читач, що сам каже «входу нема», і параметр стенда — не місця."""
        поля = {п for п, _ in self.місця}
        self.assertNotIn("тренд_сезону", поля)
        self.assertNotIn("гардероб", поля)
        self.assertNotIn("шлях_фіду", поля)
        self.assertIn("гардероб", {к for _, _, к, _ in self.р["сам_каже"]})
        self.assertIn("шлях_фіду", self.р["не_поле"])


if __name__ == "__main__":
    unittest.main()

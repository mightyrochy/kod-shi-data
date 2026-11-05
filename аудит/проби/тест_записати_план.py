"""Перевіряє передачу режимів із JSON-плану до CLI приладу без запуску моделей."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import записати_план as план


class ПеревіркаПлану(unittest.TestCase):
    """Звіряє режими, сумісність реєстру й відмову до будь-яких побічних дій."""

    def запуск(self, питання):
        """Запускає справжній CLI плану й приладу в режимі друку змінних."""
        with tempfile.TemporaryDirectory() as тека:
            тека = Path(тека)
            файл = тека / "ПЛАН.json"
            файл.write_text(json.dumps({"scenes": питання}, ensure_ascii=False), encoding="utf-8")
            вихід = тека / "запис"
            результат = subprocess.run([sys.executable, str(Path(план.__file__)), str(файл),
                "збірка", "кеш", str(вихід), "--лише-змінні"], capture_output=True, text=True, encoding="utf-8")
            self.assertFalse(вихід.exists(), "перевірка змінних створила теку прогону")
            return результат

    def test_режими_питань(self):
        """Повний шлях із фото доходить до приладу замість палітри реєстру."""
        for id_, режим, фото in (("ж4_робота", "повне +фото", "1"), ("ж1_свято_тріада", "повне", "0")):
            with self.subTest(id=id_):
                результат = self.запуск({id_: [{"pr": 3040, "question": f"питання → {режим} → ДО → краще"}]})
                self.assertEqual(результат.returncode, 0, результат.stderr)
                змінні = json.loads(результат.stdout)
                self.assertEqual((змінні["OTSINKA"], змінні["FOTO"]), ("0", фото))
                self.assertNotIn("DO", змінні)

    def test_без_режиму(self):
        """Питання без поля режиму зберігає палітру реєстру."""
        результат = self.запуск({"ж4_робота": [{"pr": 1, "question": "питання без режиму"}]})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        self.assertEqual(json.loads(результат.stdout)["DO"], "palitra")

    def test_невідомий_режим_відмова_сцени(self):
        """Сцена з режимом, якого прилад не виконає, — відмова з причиною; решта плану йде."""
        результат = self.запуск({"ж4_робота": [], "ж1_свято_тріада": [{"pr": 3085, "question": "питання → невідоме → ДО"}]})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        self.assertIn("ВІДМОВА СЦЕНИ ж1_свято_тріада: PR #3085", результат.stderr)
        self.assertIn("відмов сцени: 1", результат.stderr)
        self.assertEqual(json.loads(результат.stdout)["DO"], "palitra")

    def test_змінні_режиму_з_питання(self):
        """Змінні, які стенд читає, доходять до приладу; довільна інструкція — відмова сцени."""
        результат = self.запуск({"ж4_робота": [{"pr": 1, "question": "п → повне +фото (OTSINKA=0 FOTO_RECHI=a.jpg; руки 1–2) → ДО"}]})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        змінні = json.loads(результат.stdout)
        self.assertEqual((змінні["FOTO"], змінні["OTSINKA"], змінні["FOTO_RECHI"]), ("1", "0", "a.jpg"))
        результат = self.запуск({"ж4_робота": [{"pr": 2, "question": "п → повне, після перезбору каталогу → ДО"}]})
        self.assertIn("довільна інструкція", результат.stderr)
        self.assertEqual(результат.stdout, "")

    def test_ci_рядок_збігається_з_планом(self):
        """CI-розбір рядка й план дають однакову відповідь на ті самі питання."""
        import режими_рядків_pr as ci
        for режим, вада in (("повне, OTSINKA=0, руки 1–4", False), ("повне, після перезбору", True), ("невідоме", True)):
            питання = {"pr": 1, "question": f"п → {режим} → ДО"}
            try:
                план.режим_питань("ж4_робота", [питання]); відмова = False
            except ValueError:
                відмова = True
            self.assertEqual(відмова, вада)
            self.assertEqual(bool(ci.перевірити([{"id": "ж4_робота", "question": питання["question"]}])[0][2]), вада)

    def test_одна_сцена_на_кілька_питань(self):
        """Один запис покриває палітру, повне з фото й оцінку різних PR."""
        режими = ("палітра", "повне", "повне +фото", "оцінка")
        питання = [{"pr": 1, "question": f"питання → {режим} → ДО"} for режим in режими]
        результат = self.запуск({"ж4_робота": питання})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        змінні = json.loads(результат.stdout)
        self.assertEqual(змінні["FOTO"], "1")
        self.assertNotIn("DO", змінні)
        self.assertNotIn("OTSINKA", змінні)

    def test_послідовний_запуск_і_журнал(self):
        """Запускач передає режим аргументом, завершує всі сцени й зберігає червоний код."""
        with tempfile.TemporaryDirectory() as тека:
            тека = Path(тека)
            файл = тека / "ПЛАН.json"
            файл.write_text(json.dumps({"scenes": {"ж4_робота": [
                {"pr": 3040, "question": "питання → повне +фото → ДО"}], "ж1_свято_тріада": []}}), encoding="utf-8")
            вихід = тека / "запис"
            with patch.object(sys, "argv", ["записати_план", str(файл), "збірка", "кеш", str(вихід)]), \
                    patch.object(план.subprocess, "run", side_effect=[subprocess.CompletedProcess([], 1), subprocess.CompletedProcess([], 0)]) as запуск:
                self.assertEqual(план.виконати(), 1)
            self.assertEqual(запуск.call_count, 2)
            self.assertEqual(запуск.call_args_list[0].args[0][-2:], ["--режим", "повне +фото"])
            self.assertNotIn("--режим", запуск.call_args_list[1].args[0])
            записи = [json.loads(рядок) for рядок in (вихід / "done.txt").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([запис["rc"] for запис in записи], [1, 0])


if __name__ == "__main__":
    unittest.main()

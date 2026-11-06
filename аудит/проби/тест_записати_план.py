"""Перевіряє передачу режимів із JSON-плану до CLI приладу без запуску моделей."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import записати_план as план
import записати_сцену as сцена


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

    def test_невідомий_режим_відмова_питання(self):
        """Питання з режимом, якого прилад не виконає, — відмова питання з PR і причиною; сцену пише решта її питань,
        а без них — режим реєстру (нічний 05.11: 11 таких питань забрали запис шести сцен)."""
        погане = {"pr": 3085, "question": "питання → невідоме → ДО"}
        результат = self.запуск({"ж4_робота": [погане, {"pr": 3086, "question": "п → повне → ДО"}], "ж1_свято_тріада": [погане]})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        for id_ in ("ж4_робота", "ж1_свято_тріада"):
            self.assertIn(f"ВІДМОВА ПИТАННЯ {id_}: PR #3085", результат.stderr)
        self.assertIn("відмов сцени: 0 · відмов питання: 2", результат.stderr)
        декодер, текст = json.JSONDecoder(), результат.stdout
        перша, кінець = декодер.raw_decode(текст)
        друга, _ = декодер.raw_decode(текст, кінець + 1)
        self.assertEqual((перша["SCENA"], перша["OTSINKA"]), ("ж4_робота", "0"))
        self.assertNotIn("DO", перша)
        self.assertEqual((друга["SCENA"], друга["DO"]), ("ж1_свято_тріада", "palitra"))

    def test_змінні_режиму_з_питання(self):
        """Змінні, які стенд читає, доходять до приладу; довільна інструкція — відмова сцени."""
        фото = "аудит/проби/знімки/f142_ohliad_bella_pislia.jpg"
        результат = self.запуск({"ж4_робота": [{"pr": 1, "question": f"п → повне +фото (OTSINKA=0 FOTO_RECHI={фото}; руки 1–2) → ДО"}]})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        змінні = json.loads(результат.stdout)
        self.assertEqual((змінні["FOTO"], змінні["OTSINKA"], змінні["FOTO_RECHI"]), ("1", "0", str(сцена.КОРІНЬ / фото)))
        результат = self.запуск({"ж4_робота": [{"pr": 2, "question": "п → повне, після перезбору каталогу → ДО"}]})
        self.assertIn("ВІДМОВА ПИТАННЯ ж4_робота: PR #2: Сцена ж4_робота: «після перезбору каталогу» — довільна інструкція",
                      результат.stderr)
        self.assertEqual(json.loads(результат.stdout)["DO"], "palitra")

    def test_файли_сцени(self):
        """Файл сцени — шлях від кореня репозиторію, стенду — абсолютний; ім'я без теки чи файлу нема — відмова сцени
        до старту, а не ENOENT стенда (нічний 05.11: ROZMOVA=R_*.json трьох сцен)."""
        результат = self.запуск({"ж4_робота_живіт": []})
        self.assertEqual(результат.returncode, 0, результат.stderr)
        self.assertEqual(json.loads(результат.stdout)["ROZMOVA"], str(сцена.КОРІНЬ / "аудит/перевірки/rozbir_0210/R_zhyvit.json"))
        результат = self.запуск({"ж4_робота": [{"pr": 3, "question": "п → повне, ROZMOVA=R_zhyvit.json → ДО"}]})
        self.assertIn("ВІДМОВА СЦЕНИ ж4_робота: Сцена ж4_робота: ROZMOVA=R_zhyvit.json — файлу нема", результат.stderr)
        self.assertEqual(результат.stdout, "")

    def test_реєстр_файли_є(self):
        """Кожна файлова змінна реєстру веде до файлу в репозиторії; фото її речей, яких у репозиторії нема, — відомий
        виняток (дошка 13576), а не мовчазний ENOENT."""
        нема = []
        for рядок in (сцена.КОРІНЬ / "аудит/проби/живі_сцени.txt").read_text(encoding="utf-8").splitlines():
            if рядок.startswith("#") or "|" not in рядок:
                continue
            id_ = рядок.split("|")[0]
            try:
                сцена.файли_сцени(id_, dict(о.partition("=")[::2] for о in рядок.split("|")[3].split() if "=" in о))
            except ValueError as причина:
                нема.append(id_)
        self.assertEqual(нема, ["ж1_робота_блуза_фото", "ж3_свято_др_взуття_фото"])

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


class ПеревіркаДереваСтенда(unittest.TestCase):
    """Стенд іде з живого шляху штампа сторінки: дерево новіше за штамп — живий шлях штампа з git у тимчасову теку."""

    def test_дерево_штампа(self):
        with tempfile.TemporaryDirectory() as тека:
            корінь = Path(тека) / "репо"

            def git(*а):
                return subprocess.run(["git", *а], cwd=корінь, check=True, capture_output=True, text=True).stdout.strip()

            def писати(шлях, текст):
                (корінь / шлях).parent.mkdir(parents=True, exist_ok=True)
                (корінь / шлях).write_text(текст, encoding="utf-8")

            корінь.mkdir()
            git("init", "-q", "-b", "main")
            git("config", "user.email", "проба@local"); git("config", "user.name", "проба")
            писати("джерела/код.py", "А = 1\n")
            писати("аудит/проби/рв6_стенд.js", "require('./модуль.js');\n")
            писати("аудит/проби/модуль.js", "// 1\n")
            писати("аудит/проби/жінки/ж1.json", "{}\n")
            писати("аудит/проби/архів/великий.txt", "не живий шлях\n")
            git("add", "-A"); git("commit", "-qm", "штамп")
            штамп = git("rev-parse", "HEAD")
            with patch.object(сцена, "КОРІНЬ", корінь):
                self.assertEqual(сцена.корінь_стенда(штамп, "node", Path(тека) / "с0"), (корінь, []), "дерево = штамп")
                писати("джерела/код.py", "А = 2\n")
                git("commit", "-qam", "продукт після штампа")
                писати("аудит/проби/модуль.js", "// 2, не закомічено\n")
                стенд, зміни = сцена.корінь_стенда(штамп, "node", Path(тека) / "с1")
                self.assertEqual(зміни, ["аудит/проби/модуль.js", "джерела/код.py"])
                self.assertEqual(стенд, Path(тека) / "с1")
                for шлях in ("джерела/код.py", "аудит/проби/модуль.js", "аудит/проби/рв6_стенд.js", "аудит/проби/жінки/ж1.json"):
                    self.assertEqual((стенд / шлях).read_text(encoding="utf-8"), git("show", f"{штамп}:{шлях}") + "\n", шлях)
                self.assertFalse((стенд / "аудит/проби/архів").exists(), "теки-архіви проб не викладаються")


if __name__ == "__main__":
    unittest.main()

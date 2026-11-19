import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[2]
шлях = КОРІНЬ / "аудит/проби/драйвер_хмарного_прогону.py"
спец = importlib.util.spec_from_file_location("драйвер", шлях)
драйвер = importlib.util.module_from_spec(спец)
спец.loader.exec_module(драйвер)


class Лічба(unittest.TestCase):
    def test_записані_виклики(self):
        with tempfile.TemporaryDirectory() as tmp:
            тека = Path(tmp)
            відповіді = тека / "VIDPOVIDI"
            відповіді.mkdir()
            for номер in range(4):
                (відповіді / f"seed3_{номер}_модель.txt").write_text("── ВІДПОВІДЬ (1) ──", encoding="utf-8")
            (тека / "done.txt").write_text('{}', encoding="utf-8")
            (тека / "результат.json").write_text('{}', encoding="utf-8")
            результат = драйвер.лічба_жива(тека)
            self.assertEqual(результат["викликів"], 4)
            for поле in ("usd", "вихід", "не200"):
                self.assertIsNone(результат[поле])
            self.assertIn("не лічено:", результат["причина"])

    def test_лише_відповіді(self):
        with tempfile.TemporaryDirectory() as tmp:
            тека = Path(tmp); відповіді = тека / "VIDPOVIDI"; відповіді.mkdir()
            (відповіді / "seed3_01_модель.txt").write_text("── ВІДПОВІДЬ (1) ──", encoding="utf-8")
            (відповіді / "seed3_02_ПРИМІРЯННЯ.txt").write_text("── КАДР: 1 ──", encoding="utf-8")
            (відповіді / "інше.txt").write_text("── ВІДПОВІДЬ (1) ──", encoding="utf-8")
            self.assertEqual(драйвер.лічба_жива(тека)["викликів"], 1)

    def test_сервер(self):
        with tempfile.TemporaryDirectory() as tmp:
            журнал = Path(tmp) / "журнал.jsonl"
            журнал.write_text(json.dumps({"початок_utc": "00:00:01", "usd": 0.1, "вихід": 10, "статус": 200}) + "\n", encoding="utf-8")
            self.assertEqual(драйвер.лічба_сервера(журнал, 0, 2), {"викликів": 1, "usd": 0.1, "вихід": 10, "не200": 0})


if __name__ == "__main__":
    unittest.main()

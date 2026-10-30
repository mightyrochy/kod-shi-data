"""Порівнює зібрані промпти й читання записаних допитів з базою; без викликів моделей.

Запуск із кореня: python аудит/проби/е2_оцінка_порівняння.py [SHA бази].
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def головна():
    """Міряє справжній вихід функцій і сумісність читача на всіх записаних допитах групи."""
    корінь = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(корінь / "джерела"))
    import оцінка_образу as після
    база = sys.argv[1] if len(sys.argv) > 1 else "76854e453d5e1897bfc29eeef21576e0c63d2e39"
    git = lambda *а: subprocess.run(["git", "-C", str(корінь), *а], capture_output=True, check=True).stdout
    with tempfile.TemporaryDirectory(prefix="е2-оцінка-") as тека:
        шлях = Path(тека) / "оцінка_образу.py"
        шлях.write_bytes(git("show", база + ":джерела/оцінка_образу.py"))
        спека = importlib.util.spec_from_file_location("оцінка_до", шлях)
        до = importlib.util.module_from_spec(спека)
        спека.loader.exec_module(до)
        for назва, модуль in (("ДО", до), ("ПІСЛЯ", після)):
            речі = модуль.виправити_речі([], [{"op": "add", "slot": "top", "color": "black"}])["речі"]
            суд = dict(речі=речі, образ=модуль.скласти(речі)[0], суд={"node": "верх"})
            оцінка = модуль.промпт_оцінки(суд)
            допит = модуль.промпт_допиту(суд, "What if I change the shoes?", {})
            правила = json.loads(допит)["task"]["rules"]
            print(назва, "довжини функцій:", len(оцінка), len(допит), "правил картки в допиті:",
                  sum(any('"' + к + '"' in р for к in ("verdict", "works", "change")) for р in правила))
        гілка = "origin/claude/zhyvi-1016-1"
        файли = git("ls-tree", "-r", "--name-only", гілка, "аудит/живі_1016_1").decode().splitlines()
        записи = [ф for ф in файли if "ж1_оціни_образ_6б/VIDPOVIDI/" in ф and ф.endswith("_ОЦІНКА_допит.txt")]
        for файл in записи:
            текст = git("show", гілка + ":" + файл).decode().split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
            assert до.прийняти_допит(текст) == після.прийняти_допит(текст), файл
            assert після.прийняти_допит(текст)["відповідь"], файл
        assert записи, "Записів допиту немає"
        print("Записані допити: однаково прочитано", len(записи), "із", len(записи))
        оцінки = [ф for ф in файли if "ж1_оціни_образ_6б/VIDPOVIDI/" in ф and ф.endswith("_ОЦІНКА_відповідь.txt")]
        шляхи = []
        for н, файл in enumerate(оцінки):
            запис = Path(тека) / (str(н) + ".txt")
            запис.write_bytes(git("show", гілка + ":" + файл))
            шляхи.append(str(запис))
        команда = [sys.executable, str(корінь / "аудит/проби/оцінка_replay_3321.py")]
        середовище = dict(os.environ, PYTHONPATH=str(корінь / "джерела"), PYTHONUTF8="1")
        запустити = lambda код: subprocess.run(команда + [str(код), *шляхи], capture_output=True, check=True,
                                               env=середовище, cwd=корінь).stdout.decode("utf-8")
        до_записи, після_записи = запустити(тека), запустити(корінь / "джерела")
        assert оцінки and до_записи == після_записи, "Читання записаних оцінок змінилось"
        print("Записані оцінки: незмінний результат", len(оцінки), "із", len(оцінки),
              "з них нерозібраних до/після:", після_записи.count("відповідь не розібрана"))


if __name__ == "__main__":
    головна()

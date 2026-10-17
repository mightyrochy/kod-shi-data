"""Утримує планові жнива, доки main не має безпечного журналу з #1366."""
import ast
import os
from pathlib import Path
import re

РЕЄСТР = {
    "t": None, "прав": ["5620"], "джерело": "план §3.2; обмежений бюджет #1370",
    "val": {"SHOPS": "ricamare.com.ua", "TRANSPORT": "браузер", "CEILING": "25",
            "SECONDS": "180", "PARALLEL": "1", "PAUSE": "2"},
}


def готовність(корінь):
    """Перевіряє вузькі залежності розкладу без мережі, імпорту й запуску жнив."""
    потрібні = (
        "zhnyvarka/журнал_артефакт.py", "zhnyvarka/журнал_проходу.py",
        "zhnyvarka/виконавець.py", ".github/workflows/zhnyva.yml",
    )
    бракує = [ш for ш in потрібні if not (корінь / ш).is_file()]
    if бракує:
        return False, "#1366: бракує " + ", ".join(бракує)
    виконавець = (корінь / потрібні[2]).read_text(encoding="utf-8")
    дерево = ast.parse(виконавець)
    прапорці = {в.value for в in ast.walk(дерево) if isinstance(в, ast.Constant) and isinstance(в.value, str)}
    черга = any(isinstance(в, ast.ImportFrom) and в.module == "журнал_проходу" for в in ast.walk(дерево))
    if not черга or not {"--журнал", "--без-огляду"} <= прапорці:
        return False, "#1366: виконавець ще без checkpoint/resume або вимкнення огляду"
    workflow = (корінь / потрібні[3]).read_text(encoding="utf-8")
    код = "\n".join(р for р in workflow.splitlines() if not р.lstrip().startswith("#"))
    for ключ, значення in РЕЄСТР["val"].items():
        запас = "'0.8'" if ключ == "PAUSE" else "inputs." + {
            "SHOPS": "shops", "TRANSPORT": "transport", "CEILING": "ceiling",
            "SECONDS": "seconds", "PARALLEL": "parallel",
        }[ключ]
        очікуване = "${{ github.event_name == 'schedule' && '" + значення + "' || " + запас + " }}"
        входи = re.findall(r"^\s*HARVEST_" + ключ + r":\s*(.+)$", код, re.M)
        if not входи or any(в != очікуване for в in входи):
            return False, "Розклад утратив обмежений вхід HARVEST_" + ключ
    потрібні_рядки = (
        "python3 zhnyvarka/журнал_артефакт.py", '--журнал "$JOURNAL_ROOT"', "--без-огляду",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        "always() && steps.restore.outcome == 'success'", "steps.restore.outputs.artifact",
        "${{ runner.temp }}/жнива-журнал/ідентичність.json",
        "${{ runner.temp }}/жнива-журнал/проходи/", "${{ runner.temp }}/жнива-журнал/сирі/",
        "if-no-files-found: error", "retention-days: 30", "actions: read",
        '--магазини "$HARVEST_SHOPS"', '--транспорт "$HARVEST_TRANSPORT"',
        '--стеля "$HARVEST_CEILING"', '--секунд-на-магазин "$HARVEST_SECONDS"',
        '--паралельно "$HARVEST_PARALLEL"', '--пауза "$HARVEST_PAUSE"',
    )
    if re.search(r"\bgit\s+push\b", код) or not all(р in код for р in потрібні_рядки):
        return False, "#1366: workflow ще без безпечного збереження artifact або має git push"
    return True, "Безпечний journal/checkpoint і artifact persistence присутні; це не доказ свіжості каталогу"


def main():
    """Пише рішення в outputs і summary; пропуск не видає за виконані жнива."""
    готово, причина = готовність(Path(__file__).resolve().parents[1])
    if os.environ.get("GITHUB_REF") != "refs/heads/main" or os.environ.get("GITHUB_EVENT_NAME") != "schedule":
        готово, причина = False, "Розклад дозволено лише для події schedule на main"
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as вихід:
        вихід.write("ready=" + str(готово).lower() + "\n")
    стан = "ГОТОВО ДО ОБМЕЖЕНОГО ЗАПУСКУ" if готово else "ЖНИВА ПРОПУЩЕНО"
    повідомлення = f"{стан}: {причина}. Рядок 5620 відкрито; HTTP/MODEL/GPU у перевірці готовності: 0.\n"
    print(повідомлення, end="")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as звіт:
        звіт.write(повідомлення)


if __name__ == "__main__":
    main()

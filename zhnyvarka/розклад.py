"""Дозволяє розклад лише з активним restore → harvest → upload одного журналу."""
import ast
import os
from pathlib import Path
import re
import shlex

РЕЄСТР = {
    "t": None, "прав": ["5620"], "джерело": "план §3.2; обмежений бюджет #1370",
    "val": {"SHOPS": "ricamare.com.ua", "TRANSPORT": "браузер", "CEILING": "25",
            "SECONDS": "180", "PARALLEL": "1", "PAUSE": "2"},
}


def _активний(крок):
    """Приймає обов'язковий крок без умовного обходу й приховування помилки."""
    return крок.get("if", "success()") == "success()" and крок.get("continue-on-error", "false") == "false"


def _ланцюжок(схема):
    """Зіставляє активні кроки одного job, ефективні env і спільний шлях журналу."""
    ж = схема["jobs"]["harvest"]
    кроки = ж["steps"]
    if схема.get("defaults") or ж.get("defaults") or not isinstance(кроки, list):
        return False
    дозволи = ж.get("permissions", схема.get("permissions", {}))
    if дозволи.get("contents") != "read" or дозволи.get("actions") != "read":
        return False
    if ж.get("needs") != "schedule-readiness" or ж.get("continue-on-error", "false") != "false":
        return False
    умова = "always() && (github.event_name == 'workflow_dispatch' || (github.event_name == 'schedule' && needs.schedule-readiness.outputs.ready == 'true'))"
    if ж.get("if") != умова or ж.get("timeout-minutes") != "${{ github.event_name == 'schedule' && 10 || 340 }}":
        return False
    відновлення = [і for і, к in enumerate(кроки) if к.get("id") == "restore"]
    жнива = [і for і, к in enumerate(кроки) if к.get("id") == "harvest"]
    uploads = [і for і, к in enumerate(кроки)
               if к.get("uses") == "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
               and к.get("with", {}).get("name") == "${{ steps.restore.outputs.artifact }}"]
    if len(відновлення) != 1 or len(жнива) != 1 or len(uploads) != 1:
        return False
    в, з, а = відновлення[0], жнива[0], uploads[0]
    if not в < з < а:
        return False
    restore, harvest, upload = кроки[в], кроки[з], кроки[а]
    if not _активний(restore) or not _активний(harvest):
        return False
    if restore.get("working-directory", ".") != "." or harvest.get("working-directory") != "zhnyvarka":
        return False
    if restore.get("run", "").strip() != "python3 zhnyvarka/журнал_артефакт.py":
        return False
    if restore.get("env", {}).get("GH_TOKEN") != "${{ github.token }}":
        return False
    env = dict(ж.get("env", {}), **harvest.get("env", {}))
    for ключ, значення in РЕЄСТР["val"].items():
        запас = "'0.8'" if ключ == "PAUSE" else "inputs." + {
            "SHOPS": "shops", "TRANSPORT": "transport", "CEILING": "ceiling",
            "SECONDS": "seconds", "PARALLEL": "parallel",
        }[ключ]
        if env.get("HARVEST_" + ключ) != "${{ github.event_name == 'schedule' && '" + значення + "' || " + запас + " }}":
            return False
    корінь = "${{ runner.temp }}/жнива-журнал"
    if env.get("JOURNAL_ROOT") != корінь:
        return False
    команда = ["python3", "виконавець.py", "--журнал", "$JOURNAL_ROOT", "--без-огляду", "--рецепти", "рецепти.tsv"]
    for прапорець, ключ in (("--магазини", "SHOPS"), ("--транспорт", "TRANSPORT"), ("--стеля", "CEILING"),
                            ("--секунд-на-магазин", "SECONDS"), ("--паралельно", "PARALLEL"), ("--пауза", "PAUSE")):
        команда.extend([прапорець, "$HARVEST_" + ключ])
    команда += ["2>&1", "|", "tee", "$JOURNAL_ROOT/жнива_лог.txt"]
    рядки = harvest.get("run", "").replace("\\\n", "").splitlines()
    if [shlex.split(р) for р in рядки if р.strip()] != [
            ["set", "-euo", "pipefail"], команда, ["cat", "$JOURNAL_ROOT/зведення_жнив.tsv"]]:
        return False
    if upload.get("if") != "always() && steps.restore.outcome == 'success'" or upload.get("continue-on-error", "false") != "false":
        return False
    вихід = upload.get("with", {})
    шляхи = {р.strip() for р in вихід.get("path", "").splitlines() if р.strip()}
    потрібні = {корінь + "/" + ім for ім in ("ідентичність.json", "проходи/", "сирі/", "зведення_жнив.tsv", "жнива_лог.txt")}
    return (шляхи == потрібні and вихід.get("if-no-files-found") == "error"
            and вихід.get("retention-days") == "30"
            and not any(re.search(r"\bgit\s+push\b", к.get("run", "")) for к in кроки))


def готовність(корінь):
    """Читає код і YAML без імпорту виконавця, мережі та запуску жнив."""
    потрібні = ("zhnyvarka/журнал_артефакт.py", "zhnyvarka/журнал_проходу.py",
                "zhnyvarka/виконавець.py", ".github/workflows/zhnyva.yml")
    бракує = [ш for ш in потрібні if not (корінь / ш).is_file()]
    if бракує:
        return False, "#1366: бракує " + ", ".join(бракує)
    try:
        import yaml
        дерево = ast.parse((корінь / потрібні[2]).read_text(encoding="utf-8"))
        прапорці = {в.value for в in ast.walk(дерево) if isinstance(в, ast.Constant) and isinstance(в.value, str)}
        черга = any(isinstance(в, ast.ImportFrom) and в.module == "журнал_проходу" for в in ast.walk(дерево))
        if not черга or not {"--журнал", "--без-огляду"} <= прапорці:
            return False, "#1366: виконавець ще без checkpoint/resume або вимкнення огляду"
        схема = yaml.load((корінь / потрібні[3]).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        if not _ланцюжок(схема):
            return False, "#1366: немає активного обмеженого restore → harvest → upload одного журналу"
    except (ImportError, SyntaxError, ValueError, KeyError, TypeError, AttributeError) as помилка:
        return False, "Готовність не доведена: " + type(помилка).__name__
    except yaml.YAMLError as помилка:
        return False, "Некоректний YAML: " + type(помилка).__name__
    return True, "Активний обмежений journal/checkpoint і artifact persistence присутні; це не доказ свіжості каталогу"


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

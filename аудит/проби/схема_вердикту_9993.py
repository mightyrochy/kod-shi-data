"""Повтор договору на записах dd1327c9: факти входу й довжина виходу без виклику моделі.

Це проєкція записаних рішень на поточну форму, не нова генерація. Неповний
JSON не домальовується: дозволено лише цілий список вибраних образів, уже
наявний до обриву, зокрема в дубльованому фрагменті перед </think>.
Для браузерного повтору скрипт також може видати записи.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import дріт_моделі as Д
import знання_дріт as ЗД
import збирач_промптів as ЗП
import вердикт_моделі as В
import повнота_образу as П
import протокол as ПР

ЗАПИС = "dd1327c9a809f03ffb7663089183950b623e976c"
ПРЕФІКС = "аудит/проби/автоживий-bd628bb29a90637ae18833c92eceb8230bd9b995/"


def дамп(об):
    """Канонічна довжина тієї самої форми JSON."""
    return json.dumps(об, ensure_ascii=False, separators=(",", ":"))


def git(*арг):
    """Прочитати незмінний доказ зі сховища, не торкаючись робочих гілок."""
    return subprocess.check_output(["git", *арг], cwd=КОРІНЬ).decode("utf8")


def форма(вхід, відповідь):
    """Ті самі рішення в одному списку, без повторного складу й фактів коду."""
    сирий, причина = ПР.розбір(відповідь)
    цілий_вибір = False
    if причина:
        м = re.search(r'"chosen"\s*:', відповідь)
        if not м:
            raise ValueError("немає цілого записаного вибору")
        вибір, _ = json.JSONDecoder().raw_decode(відповідь[м.end():].lstrip())
        if not isinstance(вибір, list) or len(вибір) != вхід["outfits_wanted"]:
            raise ValueError("список вибору неповний")
        if not all(isinstance(о, dict) and о.get("items") for о in вибір):
            raise ValueError("вибір не містить повних складів")
        сирий = dict(version="1", outfits=вибір)
        потрібне = re.search(r'"needed"\s*:', відповідь)
        if потрібне:
            сирий["needed"], _ = json.JSONDecoder().raw_decode(відповідь[потрібне.end():].lstrip())
        цілий_вибір = True
    if "verdict" not in вхід or "outfits" not in сирий:
        return сирий, цілий_вибір
    вибір = сирий.get("chosen", [])
    чому = {о["id"]: о.get("why") for о in вибір if isinstance(о, dict) and о.get("id")}
    схема = ЗП.скелет(В.оголошення_ремонту(вхід))
    дозволено = set(схема["outfits"][0])
    образи = []
    for о in сирий["outfits"]:
        о = {к: copy.deepcopy(з) for к, з in о.items() if к in дозволено}
        if чому.get(о.get("id")):
            о["why"] = чому[о["id"]]
        о["items"] = [р["n"] if isinstance(р, dict) else р for р in о["items"]]
        образи.append(о)
    нова = dict(version="1", outfits=образи)
    if "needed" in сирий:
        нова["needed"] = сирий["needed"]
    return нова, цілий_вибір


def повтор(тека=None):
    """Звірити всі записи вердикту двох сцен і створити вимір із явними обмеженнями."""
    файли = git("ls-tree", "-r", "--name-only", ЗАПИС, "--", ПРЕФІКС).splitlines()
    виміри = []
    for файл in файли:
        if "/відповіді/" not in файл:
            continue
        текст = git("show", ЗАПИС + ":" + файл)
        частини = re.split(r"\n\n── ВІДПОВІДЬ [^\n]*\n", текст, maxsplit=1)
        if len(частини) != 2:
            raise ValueError("непрочитаний запис " + файл)
        промпт, відповідь = частини
        if "ВЕРДИКТ_V1" in файл:
            до = json.loads(промпт[промпт.index("{"):])
            дані = ЗД.відновити(до) if до.get("knowledge_legend") else copy.deepcopy(до)
            старі = [р for о in дані["verdict"] for р in о["your_outfit"]["items"]]
            старі += дані.get("showcase", [])
            дані = Д.кандидати_вердикту(дані)
            нові = ЗД.рядки_таблиці(дані["candidates"])
            assert all(р in нові for р in старі), "втрачено факти кандидата"
            assert all(isinstance(р, str) for о in дані["verdict"] for р in о["your_outfit"]["items"])
            ремонт = "ОБРАЗИ_V1" in файл
            о = В.оголошення_ремонту(дані) if ремонт else П.ВИБІР
            після = ЗП.зібрати(о, дані)
            відновлено = ЗД.відновити(після) if після.get("knowledge_legend") else після
            assert ЗД.рядки_таблиці(відновлено["candidates"]) == нові, "змінилося знання після ущільнення"
            if до.get("format_error"):
                після["format_error"] = до["format_error"]
            нова, цілий_вибір = форма(після, відповідь) if ремонт else (ПР.розбір(відповідь)[0], False)
            вихід = дамп(нова)
            схема = "ОБРАЗИ_V1" if ремонт else "ВИБІР_V1"
            об, причина, нотатки = ПР.розбір_за_схемою(вихід, схема)
            assert причина is None and not нотатки["обрізано"]
            assert ПР.розбір(вихід)[1] is None
            помилки = ПР.перевірити(ПР.СХЕМИ[схема], об)
            # Записані незаконні полюси/дії — окрема якість рішень, не синтаксис JSON.
            виміри.append(dict(файл=файл, ремонт=ремонт, вхід_до=len(дамп(до)), вхід_після=len(дамп(після)),
                               вихід_до=len(відповідь.strip()), вихід_після=len(вихід),
                               сирий_не_json=ПР.розбір(відповідь)[1] is not None,
                               цілий_вибір_до_обриву=цілий_вибір, порушення_значень=помилки,
                               обрізано_після=False, нечитний_після=False))
            промпт, відповідь = дамп(після), вихід
            текст = "── ПРОМПТ (%d симв.) ──\n%s\n\n── ВІДПОВІДЬ (проєкція записаних рішень) ──\n%s\n" % (
                len(промпт), промпт, відповідь)
        if тека:
            шлях = тека / Path(файл).relative_to(ПРЕФІКС)
            шлях.parent.mkdir(parents=True, exist_ok=True)
            шлях.write_text(текст, encoding="utf8")
    return dict(джерело=ЗАПИС, модель_викликалась=False, записи=виміри)


if __name__ == "__main__":
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument("--вивід", type=Path)
    ап.add_argument("--записи", type=Path)
    арг = ап.parse_args()
    результат = повтор(арг.записи)
    if арг.вивід:
        арг.вивід.parent.mkdir(parents=True, exist_ok=True)
        арг.вивід.write_text(json.dumps(результат, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    for р in результат["записи"]:
        print(Path(р["файл"]).name, "вхід", р["вхід_до"], "→", р["вхід_після"],
              "вихід", р["вихід_до"], "→", р["вихід_після"], "порушень значень", len(р["порушення_значень"]))

# -*- coding: utf-8 -*-
"""Відновлюваний обхід крамниць: повторює прохід виконавця, доки черга адрес кожної крамниці не вичерпана.

Журнал (корінь `--журнал`) лежить поза репозиторієм; повторний запуск продовжує з місця, де обірвався.
Після кожного циклу пише `обхід_стан.tsv`: на крамницю — адрес, результат, лишилось, стан і причина кодами.
"""
import argparse
import collections
import csv
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
ПРОДОВЖИТИ = ("стеля", "бюджет")
ШАПКА = ("домен", "стан_код", "причина_код", "адрес", "готово", "лишилось", "цикл", "підстава")


def результати(журнал, домен):
    """Рахує результат по останньому запису кожної адреси з jsonl крамниці (картка, заслон, збій…)."""
    файл = Path(журнал) / "сирі" / (домен + ".jsonl")
    останні = {}
    if файл.is_file():
        for рядок in файл.read_text(encoding="utf-8").splitlines():
            try:
                з = json.loads(рядок)
                останні[з["url"]] = з.get("стан") or "без_стану"
            except (json.JSONDecodeError, KeyError):
                continue  # обірваний останній рядок результату не доводить
    return collections.Counter(останні.values())


def черга(журнал, домен):
    """Повертає (усього, виконано) з черги крамниці; None, якщо черги нема (json-сімейство)."""
    база = Path(журнал) / "проходи" / домен / "черга.sqlite3"
    if not база.is_file():
        return None
    з = sqlite3.connect(база)
    try:
        return з.execute("SELECT count(*), coalesce(sum(стан='DONE'),0) FROM черга").fetchone()
    finally:
        з.close()


def причина(нотатка):
    """Називає причину лише за явним слідом у нотатці виконавця; здогадок нема — інакше UNKNOWN."""
    н = нотатка.lower()
    if "заслон" in н or "403" in н or "cloudflare" in н:
        return "BOT_CHALLENGE"
    if "sitemap +0" in н:
        return "EMPTY_SOURCE"
    if "timeout" in н or "тайм" in н:
        return "TIMEOUT"
    if "збій" in н:
        return "EXCEPTION"
    return "UNKNOWN"


def стан_рядка(домен, ряд, цикл, журнал):
    """Зводить останній рядок зведення виконавця й чергу в стан крамниці (CATALOG / WAIT) з причиною."""
    нотатка, карток = ряд["нотатка"], int(ряд["карток"] or 0)
    ч = черга(журнал, домен)
    адрес = ч[0] if ч else int(ряд["адрес_знайдено"] or 0)
    готово = ч[1] if ч else int(ряд["відкрито"] or 0)
    лишилось = (ч[0] - ч[1]) if ч else (1 if any(п in нотатка for п in ПРОДОВЖИТИ) else 0)
    в_каталозі = карток > 0 or sum(результати(журнал, домен).get(к, 0) for к in ("картка", "нижче_порогу")) > 0
    return dict(домен=домен, стан_код="CATALOG" if в_каталозі else "WAIT",
                причина_код="" if в_каталозі else причина(нотатка),
                адрес=адрес, готово=готово, лишилось=лишилось, цикл=цикл, підстава=нотатка[:200])


def останні_рядки(зведення, з_рядка):
    """Читає рядки зведення, дописані після `з_рядка`; для домену береться останній."""
    ряди = list(csv.DictReader(open(зведення, encoding="utf-8"), delimiter="\t"))[з_рядка:]
    return {р["домен"]: р for р in ряди}, з_рядка + len(ряди)


def записати(журнал, стани):
    """Перезаписує обхід_стан.tsv повним станом усіх крамниць обходу."""
    with open(Path(журнал) / "обхід_стан.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.DictWriter(ф, ШАПКА, delimiter="\t")
        п.writeheader()
        п.writerows(стани[д] for д in sorted(стани))


def вбити_процес(proc):
    """Примусово завершує дерево процесів."""
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        pass
    try:
        proc.kill()
    except Exception:
        pass


def main(argv=None):
    """Крутить цикли виконавця; крамницю з 0 прогресу за цикл зупиняє зі станом WAIT і причиною."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument("--журнал", required=True)
    ап.add_argument("--магазини", default="усі")
    ап.add_argument("--транспорт", default="http,браузер")
    ап.add_argument("--циклів", type=int, default=6)
    ап.add_argument("--стеля", type=int, default=300)
    ап.add_argument("--секунд-на-магазин", type=int, default=900)
    ап.add_argument("--паралельно", type=int, default=2)
    ап.add_argument("--секунд-на-цикл", type=int, default=None)
    ап.add_argument("--заглушка", default=os.environ.get("ZHNYVARKA_ЗАГЛУШКА", None))
    а = ап.parse_args(argv)
    Path(а.журнал).mkdir(parents=True, exist_ok=True)
    зведення = Path(а.журнал) / "зведення_жнив.tsv"
    ряд0 = len(зведення.read_text(encoding="utf-8").splitlines()) - 1 if зведення.is_file() else 0

    стан_файл = Path(а.журнал) / "обхід_стан.tsv"
    стани = {}
    if стан_файл.is_file():
        for р in csv.DictReader(open(стан_файл, encoding="utf-8"), delimiter="\t"):
            стани[р["домен"]] = {
                "домен": р["домен"],
                "стан_код": р["стан_код"],
                "причина_код": р["причина_код"],
                "адрес": int(р["адрес"]),
                "готово": int(р["готово"]),
                "лишилось": int(р["лишилось"]),
                "цикл": int(р["цикл"]),
                "підстава": р["підстава"],
            }

    магазини = перелік_крамниць(а)
    if стани:
        магазини = [д for д in магазини if д not in стани or стани[д]["лишилось"] > 0]

    for цикл in range(1, а.циклів + 1):
        if not магазини:
            break
        партій = (len(магазини) + max(а.паралельно, 1) - 1) // max(а.паралельно, 1)
        таймаут_циклу = а.секунд_на_цикл if а.секунд_на_цикл is not None else (партій * а.секунд_на_магазин + 60)
        cmd = [sys.executable, str(ТЕКА / "виконавець.py"), "--журнал", а.журнал, "--без-огляду",
               "--рецепти", str(ТЕКА / "рецепти.tsv"), "--магазини", ",".join(магазини),
               "--транспорт", а.транспорт, "--стеля", str(а.стеля),
               "--секунд-на-магазин", str(а.секунд_на_магазин), "--паралельно", str(а.паралельно)]
        if а.заглушка:
            cmd += ["--заглушка", а.заглушка]

        код = 0
        таймаут_вийшов = False
        proc = subprocess.Popen(cmd, start_new_session=sys.platform != "win32")
        try:
            код = proc.wait(timeout=таймаут_циклу)
        except subprocess.TimeoutExpired:
            таймаут_вийшов = True
            вбити_процес(proc)
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            код = -1

        ряди, ряд0 = останні_рядки(зведення, ряд0) if зведення.is_file() else ({}, 0)
        наступні = []
        for д in магазини:
            if д in ряди:
                с = стан_рядка(д, ряди[д], цикл, а.журнал)
            else:
                # Крамниця без рядка у зведенні: таймаут циклу або аварійне завершення
                ч = черга(а.журнал, д)
                адрес = ч[0] if ч else (стани[д]["адрес"] if д in стани else 0)
                готово = ч[1] if ч else (стани[д]["готово"] if д in стани else 0)
                лишилось = (ч[0] - ч[1]) if ч else (стани[д]["лишилось"] if д in стани else 1)
                причина_код = "TIMEOUT" if таймаут_вийшов else "збій"
                підстава = "таймаут циклу обходу (виконавця зупинено)" if таймаут_вийшов else "виконавець не повернув рядка зведення"
                був_у_каталозі = д in стани and стани[д]["стан_код"] == "CATALOG"
                с = dict(домен=д, стан_код="CATALOG" if був_у_каталозі else "WAIT",
                         причина_код="" if був_у_каталозі else причина(причина_код),
                         адрес=адрес, готово=готово, лишилось=лишилось,
                         цикл=цикл, підстава=підстава)
            було = стани.get(д)
            стани[д] = с
            if с["стан_код"] != "WAIT" and с["лишилось"] and не_стоїть(було, с):
                наступні.append(д)
        записати(а.журнал, стани)
        print("цикл %d: код %d · крамниць %d → лишилось продовжувати %d" % (цикл, код, len(магазини), len(наступні)), flush=True)
        магазини = наступні


def перелік_крамниць(а):
    """Перелік крамниць обходу: названі або всі з рецептів."""
    if а.магазини.strip() not in ("усі", "all", ""):
        return [x.strip().lower() for x in а.магазини.split(",")]
    return [р["домен"] for р in csv.DictReader(open(ТЕКА / "рецепти.tsv", encoding="utf-8"), delimiter="\t")
            if р["транспорт"] in {x.strip() for x in а.транспорт.split(",")}]


def не_стоїть(було, є):
    """Крамниця без нових виконаних адрес за цикл не продовжується — це знак заслону, не повільності."""
    if not було:
        return є["готово"] > 0
    return є["готово"] > було["готово"]


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Відновлюваний обхід крамниць: повторює прохід виконавця, доки черга адрес кожної крамниці не вичерпана.

Журнал (корінь `--журнал`) лежить поза репозиторієм; повторний запуск продовжує з місця, де обірвався.
Після кожного циклу пише `обхід_стан.tsv`: на крамницю — адрес, результат, лишилось, стан і причина кодами.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
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


def main(argv=None):
    """Крутить цикли виконавця; крамницю з 0 прогресу за цикл зупиняє зі станом WAIT і причиною."""
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument("--журнал", required=True)
    ап.add_argument("--магазини", default="усі")
    ап.add_argument("--транспорт", default="http,браузер")
    ап.add_argument("--циклів", type=int, default=6)
    ап.add_argument("--стеля", type=int, default=300)
    ап.add_argument("--секунд-на-магазин", type=int, default=900)
    ап.add_argument("--паралельно", type=int, default=2)
    а = ап.parse_args(argv)
    Path(а.журнал).mkdir(parents=True, exist_ok=True)
    зведення = Path(а.журнал) / "зведення_жнив.tsv"
    ряд0 = len(зведення.read_text(encoding="utf-8").splitlines()) - 1 if зведення.is_file() else 0
    стани, магазини = {}, перелік_крамниць(а)
    for цикл in range(1, а.циклів + 1):
        if not магазини:
            break
        код = subprocess.call([sys.executable, str(ТЕКА / "виконавець.py"), "--журнал", а.журнал, "--без-огляду",
                               "--рецепти", str(ТЕКА / "рецепти.tsv"), "--магазини", ",".join(магазини),
                               "--транспорт", а.транспорт, "--стеля", str(а.стеля),
                               "--секунд-на-магазин", str(а.секунд_на_магазин), "--паралельно", str(а.паралельно)])
        ряди, ряд0 = останні_рядки(зведення, ряд0) if зведення.is_file() else ({}, 0)
        наступні = []
        for д in магазини:
            if д not in ряди:
                continue
            с = стан_рядка(д, ряди[д], цикл, а.журнал)
            було = стани.get(д)
            стани[д] = с
            if с["лишилось"] and (не_стоїть(було, с)):
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
    return not було or є["готово"] > було["готово"]


if __name__ == "__main__":
    main()

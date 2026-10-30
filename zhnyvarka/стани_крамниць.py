# -*- coding: utf-8 -*-
"""Кодований стан крамниці окремо від її доступу й дозволу на наступні жнива."""
import argparse
import collections
import csv
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

СТАНИ = frozenset(("CATALOG", "WAIT", "DISABLED", "RECON"))
ПРИЧИНИ = frozenset(("UNKNOWN", "HTTP", "BOT_CHALLENGE", "TIMEOUT", "TRANSPORT",
                    "UNSUPPORTED_API", "EMPTY_SOURCE", "EXCEPTION", "CEILING"))
ДОСТУП = frozenset(("UNKNOWN", "CLOUD", "HOME_ONLY", "JS_CHALLENGE", "UNAVAILABLE"))


def стан_крамниці(домен, речей, дозвіл=None, діаг=None, підстава=""):
    """Будує стан з наявного каталогу і явних кодів виробника, без здогадок із фраз.

    Дозвіл на жнива не є станом каталогу: збережені речі лишаються видимими незалежно
    від доступу й наявності на сайті. Старі діагнози без кодів мають причину UNKNOWN.
    """
    діаг = діаг or {}
    причина = діаг.get("причина_код", "UNKNOWN")
    доступ = діаг.get("доступ_код", "UNKNOWN")
    return dict(домен=домен, речей=речей, дозвіл=дозвіл or "UNKNOWN",
                стан_код="CATALOG" if речей else ("DISABLED" if дозвіл == "вимкнено" else "WAIT"),
                причина_код=причина if причина in ПРИЧИНИ else "UNKNOWN",
                доступ_код=доступ if доступ in ДОСТУП else "UNKNOWN",
                коди=діаг.get("коди", {}), підстава=підстава,
                спостереження=діаг.get("стан", ""))


def рядки_звіту(стани):
    """Показує власникові коди й дослівну підставу, включно з невідомими причинами."""
    рядки = ["", "## Стани крамниць (5658)", "",
             "Кількість — у цьому каталозі; UNKNOWN — причина або доступ не встановлені. Дозвіл на жнива не змінюється.", "",
             "| Крамниця | Речей | Стан | Причина | Доступ | HTTP/транспорт | Підстава |", "|---|---:|---|---|---|---|---|"]
    for с in стани:
        підстава = (с["підстава"] + ": " + с["спостереження"]).replace("|", "\\|").replace("\n", " ")
        рядки.append("| %s | %d | %s | %s | %s | %s | %s |" % (
            с["домен"], с["речей"], с["стан_код"], с["причина_код"], с["доступ_код"],
            json.dumps(с["коди"], ensure_ascii=False), підстава))
    return рядки


def знімок(каталог, перелік, сирі=None):
    """Зіставляє поточний каталог, реєстр і за потреби збережені діагнози без мережі."""
    лічби = collections.Counter()
    відкрити = gzip.open if str(каталог).endswith(".gz") else open
    with відкрити(каталог, "rb") as ф:
        for _, офер in ET.iterparse(ф, events=("end",)):
            if офер.tag == "offer":
                лічби[(офер.findtext("param[@name='магазин']") or "").removeprefix("www.")] += 1
                офер.clear()
    with open(перелік, encoding="utf-8") as ф:
        магазини = list(csv.DictReader((р for р in ф if not р.startswith("#")), delimiter="\t"))
    вих = []
    for м in магазини:
        домен = м["домен"].removeprefix("www.")
        діаг, підстава = {}, "каталог=%s; реєстр=%s; діагноз відсутній" % (каталог, перелік)
        if сирі:
            for суфікс in (".json.gz", ".json"):
                файл = Path(сирі) / (домен + суфікс)
                if файл.is_file():
                    читати = gzip.open if суфікс.endswith(".gz") else open
                    with читати(файл, "rt", encoding="utf-8") as ф:
                        діаг = json.load(ф).get("діаг", {})
                    підстава = str(файл)
                    break
        вих.append(стан_крамниці(домен, лічби[домен], м["стан"], діаг, підстава))
    return вих


def main():
    """Друкує власникові стан поточного каталогу; HTTP не виконує."""
    корінь = Path(__file__).resolve().parents[1]
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument("--каталог", default=str(корінь / "каталог_повний.xml.gz"))
    ап.add_argument("--перелік", default=str(корінь / "zhnyvarka/магазини.tsv"))
    ап.add_argument("--сирі")
    а = ап.parse_args()
    print("\n".join(рядки_звіту(знімок(а.каталог, а.перелік, а.сирі))))


if __name__ == "__main__":
    main()

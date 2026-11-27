#!/usr/bin/env python3
"""Перелік нових речей проходу (продовження наряду `Запис-речі-прохід-сцен`, п.2): речі, що мапа ід (`мапа_ід.py`) знайшла
в пулах усіх сцен, а записів нового виду в `дані/записи_речі.json.gz` ще нема. Порядок: ж3 (мірило (б)), ж4, далі за
ситуаціями; усередині — за ід. Вихід: `дані/перелік_нові.json` (`речі`: ід без крамниці — як у `прохід.py`, повний ід з
крамницею — для `звести.py`). Запуск з кореня: python3 -I <цей файл>"""
import gzip, json, re
from pathlib import Path
К = Path(__file__).resolve().parents[4]; Д = К / "аудит/проби/запис-речі-прохід-сцен/дані"
мапа = json.load(gzip.open(Д / "мапа_ід.json.gz", "rt", encoding="utf-8"))
є = {к.split("@")[0] for к in json.load(gzip.open(Д / "записи_речі.json.gz", "rt", encoding="utf-8"))}
порядок = lambda с: (0, 0) if с.startswith("ж3") else (1, 0) if с.startswith("ж4") else (2, int(re.match(r"с(\d+)", с)[1]))
речі = {}
for запит, рс in мапа.items():
    сц = запит.split("/")[0]
    for ід, ст, _ in рс.values():
        if not ід or ід.split("@")[0] in є: continue
        р = речі.setdefault(ід.split("@")[0], {"ід": ід.split("@")[0], "повний": ід, "ситуації": set()})
        р["ситуації"].add(сц)
вих = sorted(речі.values(), key=lambda р: (min(порядок(с) for с in р["ситуації"]), р["ід"]))
for р in вих: р["ситуації"] = sorted(р["ситуації"])
(Д / "перелік_нові.json").write_text(json.dumps({"речей": len(вих), "речі": вих}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(вих))

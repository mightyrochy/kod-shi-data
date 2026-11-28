"""Класи розбіжностей міток Sonnet і Haiku на вибірці 300 (журнали `дані/*_новий.jsonl`, перша версія підказки).
Без моделі: для кожної мітки — пари значень, що розійшлися, з частотою, і перші N випадків (ід, значення, слот).
Запуск з кореня: python3 -I аудит/звіти/запис-речі-код/скрипти/розбіжності.py [N] > аудит/звіти/запис-речі-код/дані/розбіжності.txt"""
import collections
import json
import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[4]
Д = КОРІНЬ / "аудит/проби/запис-речі-вибірка-300/дані"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20


def мітки(файл):
    вихід = {}
    for рядок in open(Д / файл, encoding="utf-8"):
        if рядок.strip():
            запис = json.loads(рядок)
            try:
                вихід[запис["ід"]] = json.loads(запис["текст"]).get("мітки", {})
            except (ValueError, AttributeError):
                pass
    return вихід


def значення(мітки_речі, поле):
    в = мітки_речі.get(поле)
    в = в.get("в") if isinstance(в, dict) else в
    if isinstance(в, list):
        в = "+".join(sorted(str(х) for х in в))
    return "∅" if в is None else str(в)


слот = {в["ід"]: в["слот"] for в in json.load(open(Д / "вибірка.json", encoding="utf-8"))}
sonnet, haiku = мітки("sonnet_новий.jsonl"), мітки("haiku_новий.jsonl")
пари = collections.defaultdict(collections.Counter)
випадки = collections.defaultdict(list)
усі = collections.Counter()
for ід in sorted(set(sonnet) & set(haiku)):
    for поле in sorted(set(sonnet[ід]) | set(haiku[ід])):
        а, б = значення(sonnet[ід], поле), значення(haiku[ід], поле)
        if а == "∅" and б == "∅":
            continue
        усі[поле] += 1
        if а != б:
            пари[поле][(а, б)] += 1
            випадки[поле].append((ід, слот.get(ід, "?"), а, б))
for поле, число in усі.most_common():
    розійшлось = sum(пари[поле].values())
    print(f"## {поле}: розійшлось {розійшлось} з {число} (Sonnet → Haiku)")
    for (а, б), к in пари[поле].most_common(25):
        print(f"  {к:3d}  {а}  →  {б}")
    for ід, с, а, б in випадки[поле][:N]:
        print(f"    {ід} [{с}] S={а} H={б}")

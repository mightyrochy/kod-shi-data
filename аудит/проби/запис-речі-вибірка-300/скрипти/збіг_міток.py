"""Збіг міток нового запису Sonnet і Haiku на вибірці 300 (перша версія підказки, журнали `дані/*_новий.jsonl`) і вибір
власника 28.11 на сторінці огляду (`дані/відповіді_власника_новий.json`, ключ — `дані/ключ_нового.json`). Без моделі.
Запуск з кореня: python3 -I аудит/проби/запис-речі-вибірка-300/скрипти/збіг_міток.py > …/дані/збіг_міток.txt"""
import collections
import json
from pathlib import Path

Д = Path(__file__).resolve().parent.parent / "дані"


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
    if поле == "колір" and isinstance(в, list) and в:
        в = max(в, key=lambda ч: ч.get("частка", 0) if isinstance(ч, dict) else 0)
        в = в.get("код") if isinstance(в, dict) else в
    return json.dumps(в, ensure_ascii=False, sort_keys=True)


sonnet, haiku = мітки("sonnet_новий.jsonl"), мітки("haiku_новий.jsonl")
усі, збіг, нс, нх = (collections.Counter() for _ in range(4))
for ід in sonnet:
    if ід not in haiku:
        continue
    for поле in set(sonnet[ід]) | set(haiku[ід]):
        а, б = значення(sonnet[ід], поле), значення(haiku[ід], поле)
        усі[поле] += 1
        збіг[поле] += а == б
        нс[поле] += а in ('"невідомо"', "null")
        нх[поле] += б in ('"невідомо"', "null")
print(f"речей з мітками обох моделей: {len(set(sonnet) & set(haiku))}")
for поле, число in усі.most_common():
    print(f"{поле}: збіг {збіг[поле]} з {число}; невідомо Sonnet {нс[поле]}, Haiku {нх[поле]}")

ключ = json.load(open(Д / "ключ_нового.json", encoding="utf-8"))
вибір = json.load(open(Д / "відповіді_власника_новий.json", encoding="utf-8"))
голоси = collections.Counter(ключ[ід][в["вибір"]].split(" (")[0] for ід, в in вибір.items())
print(f"огляд власника 28.11, речей {len(вибір)}: {dict(голоси.most_common())}")

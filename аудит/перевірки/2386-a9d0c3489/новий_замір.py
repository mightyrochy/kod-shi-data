"""Звіряє суми нового артефакту 5.1 та незмінність попередньо перевіреної реалізації."""
import collections
import json
from pathlib import Path
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf8")
корінь = Path.cwd()
попередній = "9ef27f98adc6cdc4cd1b03fdeebf6938e571e56a"
голова = "a9d0c34898ac51ec8ea349b10b69ce9666c2210f"
print("Голова:", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
for шлях in ("zhnyvarka", "джерела", "каталог_записи_v1.jsonl.gz", "каталог_повний.xml.gz",
             "аудит/жнива_5_3/повний-обхід_стан.tsv", "аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz"):
    до = subprocess.check_output(["git", "rev-parse", попередній + ":" + шлях], text=True).strip()
    після = subprocess.check_output(["git", "rev-parse", голова + ":" + шлях], text=True).strip()
    assert до == після
    print("Незмінний об'єкт:", шлях, після)
дані = json.loads((корінь / "аудит/жнива_5_3/поля_свіжі_усі.json").read_text(encoding="utf8"))
print("Крамниць у замірі:", len(дані["крамниці"]))
for стан in ("ДО", "ПІСЛЯ"):
    сума = collections.Counter()
    for крамниця in дані["крамниці"].values():
        сума.update(крамниця[стан])
    assert dict(сума) == дані["разом"][стан]
    print(стан, json.dumps(dict(сума), ensure_ascii=False))
for домен in ("gepur.com", "theoriginals.com.ua", "skripka.com.ua", "md-fashion.ua", "vsisvoi.ua",
              "intimo.com.ua", "bella-bicchi.com", "emmeliedelage.com", "alot.com.ua"):
    рядок = дані["крамниці"].get(домен)
    print("Вибірка", домен, json.dumps(рядок, ensure_ascii=False) if рядок else "НЕМАЄ")
журнал = Path.home() / ".cache/liusterko/harvest-5.3-claude"
print("Сирі джерела заміру доступні:", журнал.is_dir())
print("Новий замір рахує наявність полів; перевірок чужого тексту, відгуків, комплекту й походження кольору немає.")

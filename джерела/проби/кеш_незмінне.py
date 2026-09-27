# -*- coding: utf-8 -*-
"""К-4: що в промпті незмінне й ДЕ воно стоїть — за записами стенда (`рв6_стенд.js`, VIDPOVIDI=<тека>).
Кеш провайдера ловить лише СПІЛЬНИЙ ПОЧАТОК запиту, тож на тип виклику: спільний початок промптів
одного сіда (між викликами), спільний початок усіх сідів (між жінками), блок «task»/«завдання» (роль,
правила, межі, схема) — розмір і зсув. Токени — Gemma (GEMMA_TOKENIZER=<tokenizer.json>), інакше символи.
Запуск: python3 проби/кеш_незмінне.py <тека сіда> [<тека другого сіда> …]"""
import os, re, sys, collections
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else len(s)


def блок_завдання(п):
    """(зсув, довжина) обʼєкта «task»/«завдання» у промпті; (-1, 0) — його нема."""
    м = re.search(r'"(?:task|завдання)":\s*\{', п)
    if not м:
        return -1, 0
    маска, гл = re.sub(r'"(?:[^"\\]|\\.)*"', lambda х: " " * len(х.group()), п), 0   # рядки — геть
    for і in range(м.end() - 1, len(п)):
        гл += (маска[і] == "{") - (маска[і] == "}")
        if гл == 0:
            return м.start(), і + 1 - м.start()
    return м.start(), len(п) - м.start()

def промпти(тека):
    """{тип виклику: [промпт, …]} однієї теки стенда: заголовок і відповідь відрізані."""
    г = collections.defaultdict(list)
    for ім in sorted(os.listdir(тека)):
        т = open(os.path.join(тека, ім), encoding="utf-8").read()
        г[re.sub(r"^seed\d+_\d+_", "", ім)[:-4]].append(т.split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (")[0])
    return г

теки = [промпти(а) for а in sys.argv[1:]]
print("%-40s %4s %9s %9s %9s %9s %5s" % ("виклик", "вик", "сер", "спіл1сід", "спілУсі", "завдання", "зсув"))
for тип in sorted({т for г in теки for т in г}, key=lambda т: -sum(len(г.get(т, [])) for г in теки)):
    усі = [п for г in теки for п in г.get(тип, [])]
    сід = min((ток(os.path.commonprefix(г[тип])) for г in теки if len(г.get(тип, [])) > 1), default=ток(усі[0]))
    з, д = блок_завдання(усі[0])
    print("%-40s %4d %9d %9d %9d %9d %4d%%" % (тип[:40], len(усі), sum(map(ток, усі)) // len(усі), сід,
          ток(os.path.commonprefix(усі)), ток(усі[0][з:з + д]) if з >= 0 else 0,
          round(100.0 * з / len(усі[0])) if з >= 0 else -1))

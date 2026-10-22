# -*- coding: utf-8 -*-
"""Рядок 190 (наряд 4.4, Д.1): скільки незмінного початку дала б ПЕРЕСТАНОВКА промпта — без перестановки (вхід моделі
не міняється: це Р3, лише вимір). На тип виклику, по всіх промптах тек стенда (VIDPOVIDI=<тека>, кілька сідів):
«нині» — спільний початок, який кеш провайдера бачить сьогодні; «сталі» — члени повідомлення (верхні ключі й ключі
«task»), однакові в усіх промптах типу: стань вони першими, спільний початок був би не менший за їхню суму. Пороги
неявного кешу Gemini: 2 048 (2.5 Flash) і 4 096 (3.x Flash). Токени — GEMMA_TOKENIZER=<tokenizer.json>, інакше символи.
Запуск: python3 проби/кеш_перестановка_190.py <тека VIDPOVIDI> [<тека другого сіда> …]"""
import collections, json, os, re, sys
Т = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer; Т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"])
ток = lambda s: len(Т.encode(s, add_special_tokens=False).ids) if Т else len(s)
джс = lambda в: json.dumps(в, ensure_ascii=False, separators=(",", ":"))
г = collections.defaultdict(list)
for тека in sys.argv[1:]:
    for ім in sorted(os.listdir(тека)):
        т = open(os.path.join(тека, ім), encoding="utf-8").read().split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (")[0]
        г[re.sub(r"^seed\d+_\d+_", "", ім)[:-4]].append(т)

def члени(о):
    """[(шлях, '"ключ":значення')] — верхні ключі, а «task»/«завдання» — по його ключах."""
    return [(к + "." + кк, джс({кк: вв})[1:-1]) for к, в in о.items() if к in ("task", "завдання") and isinstance(в, dict)
            for кк, вв in в.items()] + [(к, джс({к: в})[1:-1]) for к, в in о.items() if к not in ("task", "завдання")]

print("%-40s %3s %8s %8s %8s  %s" % ("виклик", "вик", "сер", "нині", "сталі", "найбільші сталі члени (токени)"))
for тип, тексти in sorted(г.items(), key=lambda п: -max(map(len, п[1]))):
    об = []
    for т in тексти:
        try: об.append(json.loads(т))
        except ValueError: pass
    if len(об) < 2 or len(об) < len(тексти) or not all(isinstance(о, dict) for о in об): continue
    всі = [dict(члени(о)) for о in об]
    сталі = [(ш, ток(с)) for ш, с in члени(об[0]) if all(в.get(ш) == с for в in всі)]
    print("%-40s %3d %8d %8d %8d  %s" % (тип[:40], len(тексти), sum(map(ток, тексти)) // len(тексти),
          ток(os.path.commonprefix(тексти)), sum(н for _, н in сталі),
          ", ".join("%s %d" % п for п in sorted(сталі, key=lambda п: -п[1])[:4])))

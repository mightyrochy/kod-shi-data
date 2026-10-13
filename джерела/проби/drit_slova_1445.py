# -*- coding: utf-8 -*-
"""Рядок 1445: кирилиця в «case» промптів стилістки на записаних паспортах розбору 02.10 (40 сцен).
Рука 1–2 — `дріт_моделі.випадок(випадок_для_пакета(...))`, як у пакеті складання (без «day»); руки 3–4 —
`case` промпту `руки_без_коду.промпт_руки` (доти — рядок `паспорт_рядком`). Друкує літер кирилиці
поза цитатами її слів (her_words, goal_quote, intent_quote, her_other_words, event з її слів) і приклади.
Прогін: cd джерела && python3 проби/drit_slova_1445.py ../аудит/перевірки/rozbir_0210/*/вердикти.txt.gz"""
import gzip, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import пакет_моделі as ПМ, дріт_моделі as Д, паспорт_нагоди as ПН, руки_без_коду as РБК
ЇЇ = ("her_words", "goal_quote", "intent_quote", "her_other_words", "language_model_note", "event", "mood")
кир = lambda x: len(re.findall("[а-яіїєґА-ЯІЇЄҐ]", json.dumps(x, ensure_ascii=False)))
поза = lambda c: {к: v for к, v in c.items() if к not in ЇЇ} if isinstance(c, dict) else c
р12 = р34 = n = 0; прикл = {}
for ф in sys.argv[1:]:
    try: сп = json.loads(gzip.open(ф, "rt").read())["спільне"]
    except (ValueError, KeyError): continue
    п, сц = сп.get("паспорт"), (сп.get("вхід_прогону") or {}).get("сценарій") or {}
    if not isinstance(п, dict): continue
    n += 1; рядок = ПН.паспорт_рядком(п)
    c12 = Д.випадок(ПМ.випадок_для_пакета(п, рядок, сц))
    c34 = РБК.випадок_кодами(п, рядок, сц) if hasattr(РБК, "випадок_кодами") else рядок
    р12 += кир(поза(c12)); р34 += кир(поза(c34))
    for к in ("wishes", "event", "occasion"):
        if c12.get(к) and к not in прикл: прикл[к] = (os.path.basename(os.path.dirname(ф)), c12[к])
    if "34" not in прикл: прикл["34"] = (os.path.basename(os.path.dirname(ф)), c34)
print("паспортів %d · кирилиці поза її словами: case рук 1–2 %d, case рук 3–4 %d" % (n, р12, р34))
for к, v in прикл.items(): print("  %-8s %s" % (к, json.dumps(v, ensure_ascii=False)[:400]))

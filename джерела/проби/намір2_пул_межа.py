# -*- coding: utf-8 -*-
"""НАМІР-2 (рядок 1435): «case» і доза «на межі» в справжньому пакеті складання живого прогону стенда. Аргументи —
теки VIDPOVIDI прогонів або їхні `відповіді.tar.gz`; без аргументів — ДО: ж1 і ж7 «ювілей свекрухи» розбору 02.10
(тоді: intent conventional, 40 речей `branch: edge` у кожному). Друкує на кожен пакет руки 1–2: intent, intent_source,
intent_quote, goal, нота мовної моделі, edge/усього речей пулу. Мірило рядка: case.intent ≠ conventional, edge = 0.
Запуск: cd джерела && python3 проби/намір2_пул_межа.py [тека|архів …]"""
import glob, io, json, os, re, sys, tarfile
КОР = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДО = [os.path.join(КОР, "аудит/перевірки/rozbir_0210/%s_ювілей_свекрухи/відповіді.tar.gz" % ж) for ж in ("ж1", "ж7")]
def пакети(шлях):
    if шлях.endswith(".tar.gz"):
        with tarfile.open(шлях) as т:
            for ч in sorted(т.getmembers(), key=lambda ч: ч.name):
                if "ПАКЕТ_V1_ОБРАЗИ" in ч.name:
                    yield ч.name, т.extractfile(ч).read().decode("utf-8")
    else:
        for ф in sorted(glob.glob(os.path.join(шлях, "**", "*ПАКЕТ_V1_ОБРАЗИ*"), recursive=True)):
            yield ф, open(ф, encoding="utf-8").read()
def обʼєкт(текст):
    i = текст.find('{"'); т = текст[i:].split("── ВІДПОВІДЬ")[0]
    return json.JSONDecoder().raw_decode(т)[0]
for шлях in sys.argv[1:] or ДО:
    for ім, т in пакети(шлях):
        try: в = обʼєкт(т)
        except ValueError: print("%s: пакет не читається JSON" % ім); continue
        к = в.get("case") or {}; пул = json.dumps(в.get("pool") or в, ensure_ascii=False)
        межа = len(re.findall(r'"(?:branch|br)": ?"(?:edge|e)"', пул)); усього = len(re.findall(r'"n": ?"', пул))
        print("%-60s intent %-15s source %-8s goal %-8s edge %3d/%-3d %s | quote: %s | нота: %s" % (
            шлях[-45:] + ":" + os.path.basename(ім)[:14], к.get("intent", "—"), к.get("intent_source", "—"),
            к.get("goal", "—"), межа, усього, "✔" if к.get("intent") != "conventional" and not межа else "✘",
            к.get("intent_quote", "—"), str(к.get("language_model_note", "—"))[:90]))

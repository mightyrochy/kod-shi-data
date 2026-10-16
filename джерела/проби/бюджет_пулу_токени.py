# -*- coding: utf-8 -*-
"""БЮДЖЕТ-ПУЛУ (рядки 5540, 5541): пул руки 1 на шести сценах #1042 — речей усього й по слотах, промпт руки 1
(символи, токени Qwen 3.5 і оцінка `пакет_моделі.токенів`, коли вона є), промпт руки 2, час збирання запитів.
Та сама проба на `main` ДО і на гілці ПІСЛЯ: обидва дерева беруть свій типовий бюджет (аргумент — бюджет у
токенах для дерева, що його розуміє). Токени — QWEN_TOKENIZER=<tokenizer.json Qwen3.5-9B> (`pip install tokenizers`).
Запуск із `джерела`: QWEN_TOKENIZER=… python3 проби/бюджет_пулу_токени.py [бюджет_токенів]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, feed as Ф, міст_пакет as МП, пакет_моделі as ПМ
ТК = os.environ.get("QWEN_TOKENIZER") and __import__("tokenizers").Tokenizer.from_file(os.environ["QWEN_TOKENIZER"])
ток = lambda s: len(ТК.encode(s, add_special_tokens=False).ids) if ТК else 0
оц = getattr(ПМ, "токенів", lambda s: 0)
д = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))
КАТ, База = Ф.каталог_на_диску("каталог_повний.xml"), json.load(open("стенд_вх.json", encoding="utf-8"))
exec(open("проби/пул_свобода_смуги.py", encoding="utf-8").read().split("СЦЕНИ = ", 1)[1].split("\nfor назва", 1)[0].join(["СЦЕНИ = ", ""]))
ОСН = ("верх", "низ", "сукня", "комплект", "верхній_шар")
def запити(назва, сц, пасп):
    МП._КЕШ_ПАКЕТА.clear()
    вх = dict(База, каталог=КАТ, сценарій=сц, випадок=назва, паспорт=dict(пасп, **{к: сц[к] for к in ("темп_c", "місце", "година", "опади", "дрес_код") if к in сц}))
    if sys.argv[1:]: вх["бюджет_токенів"] = int(sys.argv[1])
    т0 = time.time(); r = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False))); return r, time.time() - т0
запити(*next((н, *в) for н, в in СЦЕНИ.items()))          # прогрів: імпорти й каталог, не міряється
разом = {}
for назва, (сц, пасп) in СЦЕНИ.items():
    r, сек = запити(назва, сц, пасп)
    сл = {с: len(в) for с, в in r["кандидати"].items()}; к = sum(сл.values()); пул = д(json.loads(r["B"])["pool"])
    print("%s\n  речей %d · одяг %d (сукні %d) · взуття+сумки %d · аксесуари %d · %.1f с" % (назва, к, sum(сл.get(с, 0) for с in ОСН), сл.get("сукня", 0), сл.get("взуття", 0) + сл.get("сумка", 0), к - sum(сл.get(с, 0) for с in ОСН + ("взуття", "сумка")), сек))
    print("  слоти: " + " ".join("%s %d" % (с, сл[с]) for с in МП.УСІ_СЛОТИ if с in сл))
    print("  рука 1: %d симв, %d ток Qwen (оцінка %d) · пул %d симв, %d ток Qwen (оцінка %d), %.1f ток/річ · рука 2: %d ток Qwen" % (len(r["B"]), ток(r["B"]), оц(r["B"]), len(пул), ток(пул), оц(пул), ток(пул) / max(1, к), ток(r.get("C") or "")))
    for ключ, v in (("речей", к), ("ток1", ток(r["B"])), ("сек", сек)): разом.setdefault(ключ, []).append(v)
print("\nРАЗОМ: речей %s · ток руки 1 %s · секунд %s" % tuple("%s–%s (сума %s)" % (min(v), max(v), round(sum(v), 1)) for v in разом.values()))

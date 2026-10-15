# -*- coding: utf-8 -*-
"""БЮДЖЕТ-ПУЛУ (рядок 5540): скільки речей руки 1 влазить у бюджет і скільки токенів це коштує — за записом речі.
ДО — запис як є; К2 — ті самі факти короткими ключами (`дріт_моделі.КОРОТКІ_КЛЮЧІ`, легенда в `pool_keys`), L/hem
[a,a]→a, список з одного → значення, тканина «unknown» → типове; Т — К2 таблицею (колонки + рядки). Слова речі (назва,
колір крамниці) їдуть як є (п.12). Сцени — `проби/пул_свобода_смуги.py`. Токени — Qwen3.5 (QWEN_TOKENIZER=tokenizer.json).
PIDLOHA=10 — підлога семплера на слот (типово 20). Запуск із `джерела`: QWEN_TOKENIZER=… python3 проби/бюджет_пулу_запис.py [бюджет …]"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, feed as Ф, дріт_моделі as Д, міст_пакет as МП
ТК = os.environ.get("QWEN_TOKENIZER") and __import__("tokenizers").Tokenizer.from_file(os.environ["QWEN_TOKENIZER"])
ток = lambda s: len(ТК.encode(s, add_special_tokens=False).ids) if ТК else 0
д = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))
КЛ = dict(Д.КОРОТКІ_КЛЮЧІ, name="nm", shop_color="cs")
def к2(пул):
    р = [{КЛ.get(к, к): (в[0] if к in ("L", "hem_cm") and isinstance(в, list) and len(в) == 2 and в[0] == в[1] else Д._стиснути(к, в))
          for к, в in r.items() if not (к == "fabric" and в == "unknown")} for r in пул]
    л = Д.легенда_ключів(р, короткий=True); л.update(nm="the shop's name of the item", cs="the shop's own colour word", fb="fabric; absent = unknown")
    return р, л
def т(пул):
    р, л = к2(пул); ч = collections.Counter(к for r in р for к in r); кол = [к for к, н in ч.most_common() if н >= len(р) / 4]
    л["_layout"] = "pool.cols names the columns; a row of pool.rows gives values in that order, null = absent; an object at its end holds its other keys"
    return {"cols": кол, "rows": [[r.get(к) for к in кол] + ([{к: в for к, в in r.items() if к not in кол}] if set(r) - set(кол) else []) for r in р]}, л
ВАР, стан, старий = {"ДО": None, "К2": к2, "Т": т}, {}, Д.пакет
def новий(п):
    в = старий(п)
    if стан.get("ф") and "pool" in в: в["pool"], в["pool_keys"] = стан["ф"](в["pool"])
    return в
Д.пакет = новий
if os.environ.get("PIDLOHA"): import семплер as СМ; _в = СМ.вибрати; СМ.вибрати = lambda *a, **k: _в(*a, **dict(k, підлога=int(os.environ["PIDLOHA"])))
ОСН = ("верх", "низ", "сукня", "комплект", "верхній_шар")
КАТ, База = Ф.каталог_на_диску("каталог_повний.xml"), json.load(open("стенд_вх.json", encoding="utf-8"))
exec(open("проби/пул_свобода_смуги.py", encoding="utf-8").read().split("СЦЕНИ = ", 1)[1].split("\nfor назва", 1)[0].join(["СЦЕНИ = ", ""]))
for назва, (сц, пасп) in СЦЕНИ.items():
    print("\n" + назва)
    for бюдж in [int(x) for x in sys.argv[1:]] or [120000]:
        for вар, ф in ВАР.items():
            стан["ф"] = ф; МП._КЕШ_ПАКЕТА.clear()
            r = json.loads(B.виклик("запити", json.dumps(dict(База, каталог=КАТ, сценарій=сц, бюджет_символів=бюдж, паспорт=dict(пасп, **{к: сц[к] for к in ("темп_c", "місце", "година", "опади", "дрес_код") if к in сц}), випадок=назва), ensure_ascii=False)))
            пул = д(json.loads(r["B"])["pool"]); к = r["стеля"]["K"]; сл = {с: len(в) for с, в in r["кандидати"].items()}
            print("  бюджет %d · %-2s · речей %4d · %5.1f симв/річ · промпт %d симв, %d ток Qwen · пул %d ток, %.1f ток/річ · одяг %d, сукні %d, взуття+сумки %d, аксесуари %d" % (бюдж, вар, к, len(пул) / к, len(r["B"]), ток(r["B"]), ток(пул), ток(пул) / к, sum(сл.get(с, 0) for с in ОСН), сл.get("сукня", 0), сл.get("взуття", 0) + сл.get("сумка", 0), к - sum(сл.get(с, 0) for с in ОСН + ("взуття", "сумка"))))

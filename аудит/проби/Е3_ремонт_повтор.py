# -*- coding: utf-8 -*-
"""Е3-річ-пулу-2 (рядок 11879): записані відповіді ремонту повноти — крізь міст робочої копії, без моделі.

Записи — `аудит/гг1_замір/сирі` (28 входів живих прогонів, відповіді qwen3.5-9b на промпт ремонту); бік ремонту —
`гг1_повтор_ремонту.бік`, як `ремонт2_повтор_записів.py`. Чинний код будує пул, суд складання, вітрину й промпт ремонту,
записана відповідь іде мостом ітерації 2. Пишеться все, що з картки рук 1–2 залежить від речі пулу: склади образів
складання й ремонту (id), блокери, повернуте ремонтом (`повернуто_кодом`), повнота картки, хеш промпту ремонту
й речі вітрини.
  cd <дерево>/джерела && python3 -W ignore <репо>/аудит/проби/Е3_ремонт_повтор.py <тека з сирі/> <вихід.json> [k/n]
  python3 аудит/проби/Е3_ремонт_повтор.py --порівняти <до.json…> -- <після.json…>"""
import glob, gzip, hashlib, json, os, sys

if sys.argv[1] == "--порівняти":
    і = sys.argv.index("--")
    до, піс = ({к: v for ф in sys.argv[а:б] for к, v in json.load(open(ф, encoding="utf-8")).items()}
               for а, б in ((2, і), (і + 1, len(sys.argv))))
    поля = sorted({п for р in list(до.values()) + list(піс.values()) for п in р})
    інші = {п: [к for к in sorted(set(до) & set(піс)) if до[к].get(п) != піс[к].get(п)] for п in поля}
    print("входів: ДО %d · ПІСЛЯ %d · спільних %d" % (len(до), len(піс), len(set(до) & set(піс))))
    for п in поля:
        print("  %-28s різних %d %s" % (п, len(інші[п]), інші[п][:8]))
    for к in sorted({к for п in інші.values() for к in п}):
        print("\n══ %s" % к)
        for п in поля:
            if до[к].get(п) != піс[к].get(п):
                print("  %s\n    ДО    %s\n    ПІСЛЯ %s" % (п, json.dumps(до[к].get(п), ensure_ascii=False)[:1500],
                                                     json.dumps(піс[к].get(п), ensure_ascii=False)[:1500]))
    sys.exit(0)

sys.path.insert(0, "."); sys.path.insert(0, "../аудит/проби"); os.environ["BOKY"] = "з_гг1"
import гг1_повтор_ремонту as Г
тека, вихід = sys.argv[1], sys.argv[2]
k, n = (int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "1/1").split("/"))
входи = {json.loads(л)["ключ"]: json.loads(л) for л in gzip.open(Г.ВХОДИ, "rt", encoding="utf-8")}
міст, ост = Г.міст, {}


def стежити(ім, вх):
    р = міст(ім, вх)
    if ім == "від_моделі":
        ост["р2" if вх.get("ітерація") == 2 else "р1"] = р
    return р


Г.міст = стежити
склади = lambda р: [dict(номер=о.get("номер"), ід=о.get("ід"), блокує=bool(о.get("блокує")),
                         блокери=sorted(str(b.get("суть") or b.get("код")) for b in о.get("блокери") or []))
                    for о in (р or {}).get("образи") or []]
вих = {}
for і, ф in enumerate(sorted(glob.glob(os.path.join(тека, "сирі", "*.json.gz")))):
    if і % n != k - 1:
        continue
    з = json.load(gzip.open(ф, "rt", encoding="utf-8")); х = з.get("з_гг1") or {}
    if х.get("збій") or not х.get("виклики"):
        continue
    os.environ["ЗАМІНА_ПУЛУ"] = str(х.get("заміна_пулу", 0))
    ост.clear(); т = iter([(в["статус"], в["текст"], в["обрізано"], в["с"]) for в in х["виклики"]])
    р = Г.бік(входи[з["ключ"]]["вх"], входи[з["ключ"]]["текст"], True, lambda п, о=None: next(т, (599, "", False, 0)))
    пр = р.get("промпт") or ""
    try:
        вітрина = json.loads(пр).get("showcase") if пр else None
        вітрина = {с: [x.get("n") if isinstance(x, dict) else x for x in рч] for с, рч in вітрина.items()} \
            if isinstance(вітрина, dict) else вітрина
    except Exception as е:  # вітрина — для звірки, не для розбору
        вітрина = "не прочитано: %s" % е
    р1, р2 = ост.get("р1") or {}, ост.get("р2") or {}
    вих[з["ключ"]] = dict(
        збій=р.get("збій"), складання=склади(р1), ремонт=склади(р2), промпт_ремонту=hashlib.sha1(пр.encode()).hexdigest()[:12],
        вітрина=вітрина, повернуто=[(в.get("образ"), в.get("річ"), в.get("слот"), в.get("сім_я"))
                                   for в in (р2.get("розбір_блоків") or {}).get("повернуто_кодом") or []],
        повнота=(р2.get("повнота") or {}).get("ід"))
    print(з["ключ"], len(вих[з["ключ"]]["ремонт"]), вих[з["ключ"]]["збій"], flush=True)
json.dump(вих, open(вихід, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# -*- coding: utf-8 -*-
"""Рядки 1422/1424/1425 на прогонах стенда: на кожну руку 1–2 — чи є в описі картки речення про
плечі, стегна, талію, зріст чи фігуру; крій обраного верху і чи він у ярусі кроїв тіла
(`hypergraph.крої_для_пулу`, чинний код); `мета.фігура` звіту. Друкує лічбу по руках.
Запуск: PYTHONPATH=. python3 проби/фігура_картки_1422.py <тека клітинки ж4_…> …"""
import sys, json, gzip, re, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import fit as ПС, hypergraph as ГГ, outfit as O
ЖІНКИ = pathlib.Path(__file__).resolve().parents[2] / "аудит/проби/жінки"
ТІЛО = re.compile(r"плеч|стегн|\bтал(?:ія|ію|ії|ією|і)\b|зріст|зрост|фігур|невисок|живіт|живот|\bніг\b|\bноги", re.I)
ТИ = re.compile(r"\b(ти|тебе|тобі|твій|твоя|твої|твоє|твоїх|твоїм|твоєї|твоєму|твого|твоїй|твоєю|твоїми|твою)\b", re.I)   # про НЕЇ, не про річ


def описи(x):                                             # усі `описи_н` вердикта: (назва, крій)
    if isinstance(x, dict):
        for k, v in x.items():
            yield from ((о.get("назва"), о.get("крій")) for о in v.values()) if k == "описи_н" else описи(v)
    elif isinstance(x, list):
        for v in x:
            yield from описи(v)
лічба = collections.defaultdict(lambda: [0, 0, 0, 0])      # рука → [картки, з тілом, верхів, верхів у ярусі]
for тека in map(pathlib.Path, sys.argv[1:]):
    м = json.load(open(ЖІНКИ / (тека.name.split("_")[0] + ".json"), encoding="utf-8"))["мірки"]
    я = (ГГ.крої_для_пулу(ПС.тіло(м["зріст"], {к: v for к, v in м.items() if к != "зріст"})) or {}).get("верх")
    сир = gzip.open(тека / "вердикти.txt.gz", "rt", encoding="utf-8").read()
    фіг = sorted(set(re.findall(r'"фігура":\s*("?[^,}"]*"?)', сир)))
    for v in json.loads(сир)["прогони"][0]["вердикти"]:
        р = int(v.get("рука") or 0)
        if р not in (1, 2):
            continue
        л = лічба[р]; л[0] += 1; крої = dict(описи(v))
        тіло = [s.strip() for s in re.split(r"(?<=[.!?])\s+", str(v.get("опис") or "")) if ТІЛО.search(s) and ТИ.search(s)]
        л[1] += bool(тіло)
        верх = [x for x in (v.get("речі_образу") or []) if x.get("слот") == "верх"]
        к = O.крій_речі(dict(крій=крої.get(верх[0]["назва"]))) if верх else None
        л[2] += bool(верх); л[3] += bool(верх and я and к in я["ярус"])
        print("%-34s рука %d  тіло:%s  верх: %s %s  фігура:%s" % (тека.name[:34], р, len(тіло), к,
              "у ярусі" if я and к in я["ярус"] else "—", ",".join(фіг)))
        for s in тіло[:2]:
            print("      · " + s[:200])
for р, л in sorted(лічба.items()):
    print("РУКА %d: карток з тілом %d/%d; верхів із кроєм у ярусі %d/%d" % (р, л[1], л[0], л[3], л[2]))

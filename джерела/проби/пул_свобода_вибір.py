# -*- coding: utf-8 -*-
"""ПУЛ-СВОБОДА (рядок 5511): як стилістка обирає — ремонт лишає 5 із 10 образів складання, вибір бере 1 із 5.
По моделі: скільки разів ремонт лишив рівно перші N (місце в «verdict» — лише порядок складання, де полюси коду стоять
першими), місце обраного у показі кроку `choice` (навмання: перші 5 із 10 — 1/252, кожне місце з 5 — 20 %) і полюс
(«pole») обраного образу. Файли вердиктів: `--git` — усі версії всіх гілок (потрібна повна історія), інакше — шляхи.
Запуск: python3 джерела/проби/пул_свобода_вибір.py --git"""
import collections, gzip, json, os, re, subprocess, sys
КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
git = lambda *а: subprocess.run(("git", "-C", КОРІНЬ) + а, capture_output=True).stdout
def файли():
    if sys.argv[1:] != ["--git"]: yield from (open(ф, "rb").read() for ф in sys.argv[1:]); return
    р = git("log", "--all", "--format=", "--raw", "--no-abbrev", "--diff-filter=AM", "--no-renames", "--", ":(glob)**/вердикти*", ":(glob)**/verdykty*").decode().splitlines()
    yield from (git("cat-file", "blob", б) for б in sorted({x.split()[3] for x in р if x.startswith(":")}))
def obj(т):
    try: return json.loads(re.sub(r"^```(json)?|```$", "", str(т).strip()))
    except ValueError: return {}
бачено, Л = set(), collections.defaultdict(collections.Counter)
for дані in файли():
    try: д = json.loads(gzip.decompress(дані) if дані[:2] == b"\x1f\x8b" else дані)
    except ValueError: continue
    for п in (д.get("прогони") or []) if isinstance(д, dict) else []:
        for в in п.get("вердикти") or []:
            ключ = (д.get("пристрій"), п.get("прогін"), в.get("рука"), в.get("склад"))
            if ключ in бачено or str(в.get("рука")) not in "12": continue
            бачено.add(ключ); c = Л[str(в.get("модель"))[:22]]
            вк = {к.get("крок"): к for к in ((в.get("етапи") or {}).get("виклики") or []) if isinstance(к, dict)}
            n = len((вк.get("assembly") or {}).get("образи_кроку") or []); рем = obj((вк.get("repair") or {}).get("відповідь_сира"))
            лиш = sorted({int(x) for x in re.findall(r'"id"\s*:\s*"o(\d+)"', json.dumps(рем))})   # «chosen» чи давніше одразу «outfits»
            if n > len(лиш) > 0:
                c["ремонтів"] += 1; c["перші N"] += лиш == list(range(1, len(лиш) + 1)); c["Σм"] += sum(лиш); c["ΣN"] += len(лиш)
            вб = вк.get("choice") or {}; показ = [str(x).replace("о", "o") for x in ((вб.get("запит") or {}).get("порядок") or {}).get("образи") or []]
            обр = str(obj(вб.get("відповідь_сира")).get("chosen") or "")
            if обр in показ and len(показ) == 5:
                c["виборів"] += 1; c["місце %d" % (показ.index(обр) + 1)] += 1
                оо = [о for о in (рем.get("outfits") or []) if isinstance(о, dict)]; і = int(обр[1:]) if обр[1:].isdigit() else 0
                c["полюс %s" % (оо[і - 1].get("pole") if 0 < і <= len(оо) else "?")] += 1   # вибір нумерує образи ремонту o1… за порядком
for мод, c in sorted(((м, c) for м, c in Л.items() if c["виборів"]), key=lambda x: -x[1]["виборів"]):
    print("%s: ремонтів %d · лишив рівно перші N %d · середнє місце лишеного %.1f (навмання 5.5)" % (мод, c["ремонтів"], c["перші N"], c["Σм"] / max(c["ΣN"], 1)))
    print("   виборів з 5: %d · %s" % (c["виборів"], " · ".join("%s %d" % (к, v) for к, v in sorted(c.items()) if к.startswith("місце"))))
    print("   полюс обраного: %s" % " · ".join("%s %d" % (к[6:], v) for к, v in c.most_common() if к.startswith("полюс")))

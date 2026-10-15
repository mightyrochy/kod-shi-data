# -*- coding: utf-8 -*-
"""Рядок 5215: як часто рука 2 повторює руку 1 (та сама сукня; той самий верх+низ; увесь образ), з розбивкою за поломкою
й за ярусом пари. Файли вердиктів: `--git` — усі версії з історії всіх гілок (`вердикти*`, `verdykty*`), інакше —
аргументи чи `аудит/тести`. Пара — один раз (прогін, склад рук 1 і 2). Запуск: python3 джерела/проби/рука2_повтор_сукні.py [--git|файли]"""
import collections, gzip, json, os, subprocess, sys
КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def git(*а): return subprocess.run(("git", "-C", КОРІНЬ) + а, capture_output=True).stdout
def файли():
    if sys.argv[1:] == ["--git"]:
        рядки = git("log", "--all", "--format=", "--raw", "--no-abbrev", "--diff-filter=AM", "--no-renames", "--", ":(glob)**/вердикти*", ":(glob)**/verdykty*").decode().splitlines()
        for б in sorted({р.split()[3] for р in рядки if р.startswith(":")}): yield git("cat-file", "blob", б)
        return
    шл = sys.argv[1:] or [os.path.join(КОРІНЬ, "аудит", "тести")]
    for ш in шл:
        for к, _, фф in (os.walk(ш) if os.path.isdir(ш) else [("", 0, [ш])]):
            for ф in фф:
                if "verdykty" in ф or "вердикти" in ф: yield open(os.path.join(к, ф), "rb").read()
def речі(в):
    ро = в.get("речі_образу")
    return {r["id"]: r.get("слот") for r in ро if isinstance(r, dict)} if isinstance(ро, list) and ро else None
пари = {}
for дані in файли():
    try: д = json.loads(gzip.decompress(дані) if дані[:2] == b"\x1f\x8b" else дані)
    except ValueError: continue
    for п in (д.get("прогони") or []) if isinstance(д, dict) else []:
        вв = {str(в.get("рука")): в for в in п.get("вердикти") or []}
        if "1" in вв and "2" in вв and речі(вв["1"]) and речі(вв["2"]):
            пари[(д.get("пристрій"), п.get("прогін"), вв["1"].get("склад"), вв["2"].get("склад"))] = (вв["1"], вв["2"])
гр = collections.defaultdict(lambda: collections.Counter())
for а, б in пари.values():
    ра, рб = речі(а), речі(б); сл = lambda р, с: {i for i, x in р.items() if x == с}
    для = ("сукня" in ра.values()) and ("сукня" in рб.values()); окр = "сукня" not in list(ра.values()) + list(рб.values())
    ключ = (б.get("поломка_руки") or "—") + "·" + str(б.get("правило_руки") or "") + " · " + (str(б.get("пара_руки") or "").split(" ·")[0] or "—")
    for г in (ключ, "УСЬОГО", "модель " + str(б.get("модель"))[:16] + " · " + ключ.split(" · ")[-1]):
        c = гр[г]; c["пар"] += 1; c["увесь образ"] += set(ра) == set(рб); c["≥1 спільна річ"] += bool(set(ра) & set(рб))
        c["сукня в обох"] += для; c["та сама сукня"] += для and сл(ра, "сукня") == сл(рб, "сукня")
        c["без сукні в обох"] += окр; c["той самий верх+низ"] += окр and сл(ра, "верх") == сл(рб, "верх") and сл(ра, "низ") == сл(рб, "низ")
for г, c in sorted(гр.items(), key=lambda x: -x[1]["пар"]): print("%-34s" % г, " · ".join("%s %d" % (к, v) for к, v in c.items()))

# -*- coding: utf-8 -*-
"""Скретч: діф знімків ДО → прототип по викликах: запити — id кандидатів, що зайшли/вийшли; від_моделі — знахідки (правило,
речі → id) ДО/ПІСЛЯ. Запуск: python3 перелік.py до.jsonl проєкт.jsonl"""
import sys, json, re, collections as K
Д = [json.loads(l) for l in open(sys.argv[1])][1:]; П = [json.loads(l) for l in open(sys.argv[2])][1:]
def рефи(ЗЗ):
  реф = {}
  for з in ЗЗ:
    р = з.get("результат")
    if з["ім"] != "запити" or not isinstance(р, dict): continue
    за = {(r.get("назва"), r.get("ціна")): r["id"] for xs in р["кандидати"].values() for r in xs}
    for п in ("B", "C"):
        for m in re.finditer(r'\["(#\d+·\d+)","((?:[^"\\]|\\.)*)",(\d+)', р.get(п) or ""):
            і = за.get((json.loads('"%s"' % m.group(2)), float(m.group(3))))
            if і: реф.setdefault(m.group(1), set()).add(і)
  return lambda рр: [("/".join(sorted(реф.get(r, {r})))) for r in рр]
ідД, ідП = рефи(Д), рефи(П)
for н, (а, б) in enumerate(zip(Д, П)):
    if а == б: continue
    print("#%d %s" % (н, а["ім"]))
    ра, рб = а.get("результат"), б.get("результат")
    if а["ім"] == "запити":
        for с in sorted(set(ра["кандидати"]) | set(рб["кандидати"])):
            іа = {r["id"] for r in ра["кандидати"].get(с, [])}; іб = {r["id"] for r in рб["кандидати"].get(с, [])}
            if іа != іб: print("  слот %s: вийшли %s; зайшли %s" % (с, sorted(іа - іб), sorted(іб - іа)))
        continue
    for оа, об in zip(ра["вердикт"]["образи"], рб["вердикт"]["образи"]):
        зн = lambda о, ід: K.Counter((з["правило"], tuple(ід(з.get("речі") or [])), з.get("сила")) for з in о["знахідки"])
        за, зб = зн(оа, ідД), зн(об, ідП)
        for з in sorted(за - зб): print("  образ %s ЗНЯТО  %s %s %s" % (оа["ід"], з[0], ", ".join(з[1]), з[2]))
        for з in sorted(зб - за): print("  образ %s НОВЕ   %s %s %s" % (оа["ід"], з[0], ", ".join(з[1]), з[2]))
        if за == зб and оа != об: print("  образ %s: знахідки ті самі; різні поля %s" % (оа["ід"], [к for к in оа if оа[к] != об.get(к)]))
    if ра.get("вердикт", {}).get("образи") == рб.get("вердикт", {}).get("образи"): print("  поля:", [к for к in ра if ра[к] != рб.get(к)][:8])

# -*- coding: utf-8 -*-
"""Рядок 173: шпильки на прогулянці з собаками. Корпус — тема-10 XXV, K-END-01 / K-SHO-16: вартість
каблука росте з тривалістю й поверхнею, «the cost, stated … let her choose», «a rule that silently
downranks heels is paternalism» — отже НЕ вето: пул той самий, ціна названа. ДО — модулі main
3e99595 (git show у тимчасову теку), ПІСЛЯ — чинні. Стенд_вх, паспорт «прогулянка з собаками в
парку, +15 °C, дощ, 2 год». Друкує: поверхню й дію зі слів; пар на каблуці ≥ 6 см у пулі взуття;
суть K-SHO-16 і рядок жінці на образі з туфлями ж-09123 (крамниця: каблук 5 см) і ж-10287 (10 см).
Запуск із `джерела`: PYTHONPATH=. python3 проби/shpylky_173.py"""
import json, subprocess, sys, tempfile, os, re
if len(sys.argv) == 1:
    тека = tempfile.mkdtemp()
    for ф in ("сценарій.py", "аксесуари_носіння.py", "міст_відповіді.py", "accessory.py"):
        open(os.path.join(тека, ф), "wb").write(subprocess.check_output(["git", "show", "3e99595:джерела/" + ф]))
    subprocess.run([sys.executable, __file__, тека], check=True)
    sys.argv.append("")
sys.path.insert(0, sys.argv[1] or "."); М = "ДО   " if sys.argv[1] else "ПІСЛЯ"
import bridge as B, сценарій as СЦ
дж = lambda x: json.dumps(x, ensure_ascii=False)
п = dict(подія="прогулянка з собаками в парку", нагода="прогулянка", місце="парк", формат="просто неба",
         рух="багато ходити", тривалість_год=2, темп_c=15, опади="так", година=11)
вх = json.load(open("стенд_вх.json", encoding="utf-8"))
вх = dict(вх, сценарій=dict(вх["сценарій"], нагода="прогулянка", місце="парк", темп_c=15, дрес_код=None), паспорт=п)
н = СЦ.з_показу(вх["сценарій"], п)[0]
print("%s · зі слів: поверхня %s · дія %s" % (М, н.get("поверхня"), н.get("активність")))
к = json.loads(B.виклик("запити", дж(вх)))["кандидати"]
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
пул = [кат[x["id"]] for x in к.get("взуття", [])]
print("%s · пул взуття %d, на каблуці ≥ 6 см: %s" % (М, len(пул), [(c["id"], c.get("каблук_см")) for c in пул
                                                            if (c.get("каблук_см") or 0) >= 6]))
for пара in ("ж-09123@cultboutique.com.ua", "ж-10287@giardini-shoes.com"):
    r = json.loads(B.виклик("від_моделі", дж(dict(вх, ід=[к["сукня"][0]["id"], пара, к["сумка"][0]["id"]]))))
    суть = sorted(set(re.findall(r"каблук [0-9.]+ см на [^\"\\]{0,40}", дж(r))))
    print("%s · %s: K-SHO-16 «%s»\n        рядок жінці: %s" % (М, пара, "; ".join(суть) or "—",
                                                          (r.get("носіння_жінці") or {}).get("рядок") or "—"))

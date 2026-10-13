# -*- coding: utf-8 -*-
"""ФІГ-1, рядок 305: провенанс чисел, на яких стало правило (`діагностика`: `еластан_за_чим`
K-BOD-02, `підйом_чому` K-SIL-02), доїжджає в поле `знахідки` відповіді моста — тобто в
`етапи.суд.знахідки` файла вердиктів. 6 сцен `стенд_знімок` × 4 облягаючі низи з ≥2 %
еластану зі складу + верх і взуття з пулу сцени. Друкує: скільки знахідок СУДУ несли
`діагностика` і скільки з них несе звіт; окремо — знахідки, що спирались на два поля.
Запуск із теки `джерела`: python3 проби/фіг1_провенанс_звіт.py"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, feed as Ф, фід_каталог as ФК, pipeline as PL, стенд_знімок as СЗ
СУД, _суд = [], PL.перевірити_від_моделі
def _лічба(*a, **k):
    в = _суд(*a, **k); СУД.extend(z for z in в.get("знахідки") or [] if z.get("діагностика") and not PL._питання_або_нуль(z)); return в
PL.перевірити_від_моделі = _лічба
КАТ, База = Ф.каталог_на_диску("каталог_повний.xml"), json.load(open("стенд_вх.json", encoding="utf-8"))
кат = ФК._прочитати_каталог(КАТ, ліміт_фото=0)["каталог"]
низи = [r["id"] for r in кат if r.get("слот") == "низ" and (r.get("еластан_%") or 0) >= 2
        and r.get("крій") in ("bodycon", "fitted", "skinny") and r.get("довжина_рівень")]
суд, звіт, поле = collections.Counter(), collections.Counter(), collections.Counter()
for і, (назва, сцен) in enumerate(СЗ.СЦЕНАРІЇ.items()):
    вх = dict(База, каталог=КАТ, сценарій=сцен, випадок=назва)
    пул = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["кандидати"]
    for к in range(4):
        ід = [низи[(і * 4 + к) * 5 % len(низи)]] + [(пул.get(с) or [{}])[0].get("id") for с in ("верх", "взуття")]
        СУД.clear()
        в = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=[x for x in ід if x]), ensure_ascii=False)))
        суд.update(z["правило"] for z in СУД)
        for з in в.get("знахідки") or []:
            д = з.get("діагностика") or {}
            звіт.update([з["правило"]] if д else [])
            for п in ("еластан_за_чим", "підйом_чому"):
                if п in д: поле[(з["правило"], п, str(д[п])[:50])] += 1
print("знахідок суду з `діагностика` / у звіті з нею: %d / %d" % (sum(суд.values()), sum(звіт.values())))
for п, n in sorted(суд.items()): print("  %-10s суд %3d → звіт %3d" % (п, n, звіт[п]))
for (п, ім, v), n in sorted(поле.items()): print("  %s · %s = %s × %d" % (п, ім, v, n))

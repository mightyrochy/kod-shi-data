# -*- coding: utf-8 -*-
"""Рядки 2881 і 2952: слова для людини в дроті стилістки. ДО — записані промпти розбору 02.10
(`запит.текст` викликів): значення `found_for` і `source` кольору не-виміру. ПІСЛЯ — ті самі сирі
відповіді моделі з «needed» крізь `розбір_відповідей.запити_речей_з_тексту` → `дріт_моделі.річ`
(та сама річ із `за_запитом`, що кладе `міст_пакет.додати_за_запитом`); і її річ словами кожного
кольору лексикону (`річ_з_фото.запис_каталогу`, без фото) → `color_not_measured.source`.
Прогін: cd джерела && python3 проби/drit_znaideno_2881.py ../аудит/перевірки/rozbir_0210/*/вердикти.txt.gz"""
import gzip, json, os, re, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import розбір_відповідей as РВ, дріт_моделі as Д, річ_з_фото as Р
КИР = re.compile("[а-яіїєґА-ЯІЇЄҐ]")
до, джерела, після, прикл = Counter(), Counter(), Counter(), {}
for ф in sys.argv[1:]:
    try: прогони = json.loads(gzip.open(ф, "rt").read())["прогони"]
    except (ValueError, KeyError): continue
    for в in (в for п in прогони for в in (п.get("вердикти") or [])):
        for вк in ((в.get("етапи") or {}).get("виклики") or []):
            т = str((вк.get("запит") or {}).get("текст") or "")
            for м in re.finditer(r'"found_for": ?"([^"]*)"', т):
                до["кирилицею" if КИР.search(м.group(1)) else "кодами"] += 1
            for м in re.finditer(r'"color_not_measured": ?\{"source": ?"([^"]*)"', т):
                джерела[м.group(1)] += 1
            сира = str(вк.get("відповідь_сира") or "")
            if '"needed"' not in сира: continue
            for з in РВ.запити_речей_з_тексту(сира):
                ff = Д.річ(dict(id="x", слот=з["слот"] or "верх", за_запитом=з["коди"])).get("found_for")
                після["кирилицею" if КИР.search(str(ff)) else "кодами"] += 1
                після["доти фразою кирилицею"] += bool(КИР.search(з.get("фраза") or з["опис"]))
                прикл.setdefault(ff, з.get("фраза") or з["опис"])
print("ДО · found_for у записаних промптах:", dict(до), "· source кольору не-виміру:", dict(джерела))
print("ПІСЛЯ · found_for на запит «needed» тих самих відповідей:", dict(після))
for ff, фр in list(прикл.items())[:6]: print("   %-34s ← фраза пошуку «%s»" % (ff, фр))
її = Counter()
for сл in Р.КОЛЬОРИ:
    нв = Д.річ(Р.запис_каталогу(dict(ід="1", слот="верх", колір=сл))).get("color_not_measured")
    if нв: її[нв["source"]] += 1
print("ПІСЛЯ · її річ словами (%d кольорів лексикону) → source:" % len(Р.КОЛЬОРИ), dict(її))

# -*- coding: utf-8 -*-
"""НАМІР-2 (рядок 842): чи «case» складання (`ПАКЕТ_V1.випадок` → дріт) несе типовий намір як її слово. Паспорти —
шість живих сцен ВИБ-1 (`аудит/перевірки/vyb1/*_В/вердикти.txt.gz`, ті самі, на яких вибір виправлено 12/12 → 0/12),
плюс контроль: та сама сцена з її цитатою наміру. Друкує intent, intent_source і intent_quote «case». Без моделі.
Запуск: cd джерела && python3 проби/намір2_складання.py"""
import glob, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import пакет_моделі as ПМ, дріт_моделі as Д
підс = {"мітка": 0, "без мітки": 0}
for ф in sorted(glob.glob("../аудит/перевірки/vyb1/*_В/вердикти.txt.gz")):
    сп = json.load(gzip.open(ф))["спільне"]; п = сп["паспорт"]
    for назва, пасп in ((ф.split("/")[-2], п), ("  контроль: її слова", dict(п, намір="context_optimal",
                                                                            намір_слова="щоб ніхто не причепився"))):
        в = Д.випадок(ПМ.випадок_для_пакета(пасп, сп.get("випадок_моделі") or п.get("подія") or ""))
        if назва[0] != " ": підс["мітка" if в.get("intent_source") == "default" else "без мітки"] += 1
        print("%-22s intent %-15s intent_source %-8s intent_quote %s" % (назва, в.get("intent"), в.get("intent_source", "—"),
                                                                       в.get("intent_quote", "—")))
print("РАЗОМ: типовий намір у «case» складання — %s" % " · ".join("%s %d" % кв for кв in підс.items()))

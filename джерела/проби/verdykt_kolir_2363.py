# -*- coding: utf-8 -*-
"""Рядок 2363: колір у `речі_образу` вердикту — із запису каталогу, не з сирого офера.
Запуск: cd джерела && python3 -W ignore проби/verdykt_kolir_2363.py
ФАКТ: `міст_опис.показ` (поля `колір`/`hex` речі) проти `колір_назва`/`колір_hex_фото` запису каталогу."""
import os, sys, json
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, фід_каталог as ФК, міст_опис as М
шл = feed.каталог_на_диску()
кат = {r["id"]: r for r in ФК._прочитати_каталог(шл, ліміт_фото=0)["каталог"]}
ідс = [i for i in (o["id"] for o in feed.читати_yml(шл)[0]) if i in кат]
в = json.loads(М.показ({"каталог": шл, "речі": [{"id": i} for i in ідс]}))
розб = [(к["id"], к.get("колір"), кат[к["id"]].get("колір_назва")) for к in в if (к.get("колір") or None) != (кат[к["id"]].get("колір_назва") or None)]
з_hex_кат = sum(1 for i in ідс if кат[i].get("колір_hex_фото"))
з_hex_вер = sum(1 for к in в if к.get("hex"))
hex_розб = sum(1 for к in в if (к.get("hex") or None) != (кат[к["id"]].get("колір_hex_фото") or None))
print("ФАКТ · речей у каталозі %d, карток показу %d" % (len(ідс), len(в)))
print("ФАКТ · колір вердикту ≠ колір_назва каталогу: %d (приклади %s)" % (len(розб), розб[:3]))
print("ФАКТ · hex: у записі каталогу %d, у картках вердикту %d, розбіжних %d" % (з_hex_кат, з_hex_вер, hex_розб))

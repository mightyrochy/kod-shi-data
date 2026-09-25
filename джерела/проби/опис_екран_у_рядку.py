# -*- coding: utf-8 -*-
"""Опис s13 (gemma, 25.09): у «текст» стоїть «\\» перед справжнім переносом чи пробілом — «Invalid \\escape», опис
не розбирався і після повтору, а на картці «Чому цей образ» стояв сирий ```json {"версія"…} з \\n і \\. На збережених
відповідях опису: чим падав суворий розбір, чи розбирає тепер `розбір_відповідей.опис_відповідь_з_json` (і що названо
в `нормалізовано`), і що показ (`людською` з показ.html) кладе на картку з СИРОГО тексту, коли опису нема.
Друкує факт. Запуск: cd джерела && python3 проби/опис_екран_у_рядку.py <тека VIDPOVIDI> <сід>"""
import glob, json, os, subprocess, sys
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д); os.chdir(Д)
import розбір_відповідей as Р
тека, сід = sys.argv[1], sys.argv[2]
JS = r"""const fs=require('fs'); const h=fs.readFileSync('показ.html','utf8');
const i=h.indexOf('function людською('), j=h.indexOf('\nfunction ', i+10);
const f=new Function(h.slice(i,j)+'; return людською;')();
process.stdout.write(String(f(fs.readFileSync(0,'utf8'), null)[0]));"""
for ф in sorted(glob.glob(os.path.join(тека, "seed%s_*_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1.txt" % сід))):
    т = open(ф, encoding="utf-8").read(); к = т.find("── ВІДПОВІДЬ"); в = т[т.index("\n", к) + 1:]
    сир = в.replace("```json", "").replace("```", "").strip()
    try:
        json.loads(сир, strict=False); суворо = "розбирається"
    except ValueError as e:
        суворо = "не JSON (%s)" % str(e)[:40]
    р = Р.опис_відповідь_з_json(в)
    карт = subprocess.run(["node", "-e", JS], input=в, capture_output=True, text=True).stdout
    print("ФАКТ · %s · суворий розбір: %s · тепер «текст»: %s (%d симв.) · нормалізовано: %s" % (
        os.path.basename(ф)[:9], суворо, "є" if р["текст"] else "нема", len(р["текст"] or ""),
        "; ".join(р["нормалізовано"]) or "—"))
    print("ФАКТ ·   картка з сирого тексту (коли опису нема): %d симв.%s" % (
        len(карт), (" — " + repr(карт[:40])) if карт else " — образ без опису"))

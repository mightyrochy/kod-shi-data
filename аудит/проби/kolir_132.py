# -*- coding: utf-8 -*-
"""Рядок 132: колір brenda перезнято моделлю на кадрі, який продукт ПОКАЗУЄ.
ДО — збагачення з `origin/main`, ПІСЛЯ — файл цієї гілки; каталог той самий.
Лічба — `фід_каталог._прочитати_каталог(…, 0)`, як у вимірі куратора.
Запуск: python аудит/проби/kolir_132.py (звідки завгодно)"""
import sys, os, gzip, json, pathlib, subprocess
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
os.chdir(КОРІНЬ / "джерела")
import фід_каталог as ФК, міст_опис as МО
ІД, МАГ, КАТ = "ж-01583@brenda.ua", "@brenda.ua", "каталог_повний.xml"   # розпакований і почищений, як у збірці
ШЛЯХ = "джерела/каталог_збагачення.json.gz"
до = json.loads(gzip.decompress(subprocess.check_output(
    ["git", "-C", str(КОРІНЬ), "show", "origin/main:" + ШЛЯХ])).decode("utf-8"))
після = json.loads(gzip.decompress((КОРІНЬ / ШЛЯХ).read_bytes()).decode("utf-8"))
кадр = json.loads(МО.показ({"каталог": КАТ, "речі": [ІД]}))[0].get("фото")
for мітка, зб in (("ДО   ", до), ("ПІСЛЯ", після)):
    к = ФК._прочитати_каталог(КАТ, 0, кеш="__нема__.json", збагачення=зб)["каталог"]
    б = [c for c in к if c["id"].endswith(МАГ)]
    р = next((c for c in к if c["id"] == ІД), None)
    з = зб.get(ІД) or {}
    print("%s записів каталогу %d · brenda у каталозі %d (колір з фото %d)" % (
        мітка, len(к), len(б), sum(1 for c in б if c.get("колір_джерело") == "фото")))
    print("      %s у каталозі %s · колір_назва %s · колір_джерело %s" % (
        ІД, р is not None, (р or {}).get("колір_назва"), (р or {}).get("колір_джерело")))
    print("      збагачення: %s · кадр виміру %s" % (
        з.get("помилка") or "колір %s %s, згода %s" % ((з.get("колір_основний") or {}).get("слово"),
                                                       (з.get("колір_основний") or {}).get("hex"), з.get("впевненість")),
        (з.get("фото") or "—").split("/catalog/")[-1]))
    бр = {k: v for k, v in зб.items() if k.endswith(МАГ)}
    print("      записів brenda %d · знято на показаному кадрі %d · з помилкою %d" % (
        len(бр), sum(1 for v in бр.values() if v.get("кадр") == "показаний" and "помилка" not in v),
        sum(1 for v in бр.values() if "помилка" in v)))
print("перший кадр картки (показ) %s" % (кадр or "—").split("/catalog/")[-1])

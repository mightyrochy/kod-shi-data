# -*- coding: utf-8 -*-
"""Рядок 126: жнива приносять ВЛАСНЕ фото речі, а не тайл блоку «схожі товари».
ДО — каталог і збагачення з `origin/main`; ПІСЛЯ — файли цієї гілки. По brenda:
скільки речей мають власний кадр, скільки кадрів досі є спільною картинкою
крамниці (незалежний детектор `фід_фото._спільні_фото`), скільки лишилось без
знімка й що сталося з річчю власника `ж-01583@brenda.ua`.
Запуск: python3 аудит/проби/zhnyva_halereya_126.py (звідки завгодно)"""
import sys, gzip, json, pathlib, subprocess, xml.etree.ElementTree as ET
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import фід_фото as ФФ
БАЗА, МАГ, ІД = "origin/main", "brenda.ua", "ж-01583@brenda.ua"
з_git = lambda ш: subprocess.check_output(["git", "-C", str(КОРІНЬ), "show", "%s:%s" % (БАЗА, ш)])
ФАЙЛ = lambda ш: (КОРІНЬ / ш).read_bytes()


def офери(сирі):
    """[{id, назва, магазин, фото}] крамниці `МАГ` із байтів YML-каталогу (gz або ні)."""
    к = ET.fromstring(gzip.decompress(сирі) if сирі[:2] == b"\x1f\x8b" else сирі)
    return [dict(id="%s@%s" % (o.get("id"), МАГ), назва=o.findtext("name"), магазин=МАГ,
                 фото=[p.text for p in o.findall("picture") if p.text])
            for o in к.findall(".//offer")
            if next((p.text for p in o.findall("param") if p.get("name") == "магазин"), None) == МАГ]


for мітка, чит in (("ДО   ", з_git), ("ПІСЛЯ", ФАЙЛ)):
    о = офери(чит("каталог_повний.xml.gz"))
    з = json.loads(gzip.decompress(чит("джерела/каталог_збагачення.json.gz")).decode("utf-8"))
    сп = ФФ._спільні_фото(о)[МАГ]
    своє = lambda o: [x for x in o["фото"] if not ФФ.спільна_картинка(ФФ._файл_фото(x), сп)]
    бере = lambda и: bool(з.get(и)) and "помилка" not in з[и] and not ФФ.чужий_кадр(з[и].get("фото"), сп)
    р = next(o for o in о if o["id"] == ІД)
    print("%s %s: речей %d · з ВЛАСНИМ кадром %d · усі кадри спільні %d · знімка нема зовсім %d · кадрів на річ %.2f"
          % (мітка, МАГ, len(о), sum(1 for o in о if своє(o)),
             sum(1 for o in о if o["фото"] and not своє(o)), sum(1 for o in о if not o["фото"]),
             sum(len(o["фото"]) for o in о) / len(о)))
    print("      збагачення, яке продукт ВІЗЬМЕ як істину про річ: %d з %d" % (sum(1 for o in о if бере(o["id"])), len(о)))
    print("      %s («%s»): кадрів %d, власних %d, перший %s"
          % (ІД, (р["назва"] or "")[:38], len(р["фото"]), len(своє(р)), (своє(р) or р["фото"] or ["—"])[0].split("/catalog/")[-1]))
    print("      кадр виміру: %s" % ((з.get(ІД) or {}).get("помилка") or (з.get(ІД) or {}).get("фото")))

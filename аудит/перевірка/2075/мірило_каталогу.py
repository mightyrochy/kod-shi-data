"""Прямий замір первісного мірила 2.13 та збереження справжніх рядків для показу."""
import json
import os
from pathlib import Path
import sys
тут = Path(__file__).resolve().parent
корінь = тут.parents[2]
os.chdir(корінь / "джерела")
sys.path.insert(0, str(корінь / "джерела"))
import feed as Ф
import фід_каталог as ФК
import колір_річ as К
import colorspace as Ц
import композитор_річ as Р
import outfit as О

каталог = ФК.прочитати_каталог(Ф.каталог_на_диску(), 0)["каталог"]
індекс = {р["id"]: р for р in каталог}
група = json.loads((корінь / "аудит/перевірка/2.13_тип_кольору/каталог.json").read_text("utf-8"))["група_59"]
збережені = [ід for ід in група if (індекс[ід].get("колір_вимір") or {}).get("hex")
             and (індекс[ід].get("колір_вимір") or {}).get("lab")]
спотворені, сегментів = [], 0
for р in каталог:
    if not р.get("colors") or р.get("слот") == "верхній_шар":
        continue
    for колір, елемент in zip(р["colors"], О.елементи([Р.у_річ(р, р["слот"], {})])):
        а, б = К.точка_кольору(колір), К.точка_кольору(елемент)
        if а is not None and б is not None:
            сегментів += 1
            if Ц.de00(а, б) > 1:
                спотворені.append(р["id"])
ids = {"ж-07553@brenda.ua", "ж-00378@vilni.store", "ж-01678@ricamare.com.ua",
       "ж-11786@theoriginals.com.ua", "ж-00260@25union.com.ua"}
речі = []
for ід in ids:
    р = індекс[ід]
    речі.append({к: р.get(к) for к in ("id", "слот", "назва", "ціна", "урл", "колір_тип", "колір_вимір", "колір_не_вимір")})
    речі[-1].update(фото=р["фото"][0] if р.get("фото") else None, фото_всі=р.get("фото"))
(тут / "речі-для-очей.json").write_text(json.dumps(речі, ensure_ascii=False, indent=2), "utf-8")
факт = dict(група_59=len(група), збережено_фото=len(збережені),
            збережені_id=збережені, виміряних_сегментів=сегментів, спотворень_понад_1_DE=len(спотворені))
print(json.dumps(факт, ensure_ascii=False, indent=2))
assert len(збережені) == 59 and not спотворені

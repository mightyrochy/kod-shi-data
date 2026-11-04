"""Звірити дельту з входом і фото; скласти таблицю змін та аркуші для очного огляду."""
import collections
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ТЕКА = Path(__file__).resolve().parent
sys.path.insert(0, str(ТЕКА.parents[2] / "джерела"))
import фід_кадр_колір as К


def прочитати(назва):
    """Прочитати збережений вхід чи вихід виміру."""
    with gzip.open(ТЕКА / назва, "rt", encoding="utf-8") as файл:
        return json.load(файл)


def головна():
    """Перевірити походження кожного виміру та показати найбільшу зміну в кожній галереї."""
    до = прочитати("кадри_ДО.json.gz")["записи"]
    після = прочитати("дельта.json.gz")
    підписи = json.loads((ТЕКА / "підписи.json").read_text(encoding="utf-8"))
    вибірка = {р["id"]: set(р["файли"]) for р in
               json.loads((ТЕКА / "вибірка.json").read_text(encoding="utf-8"))}
    маніфест = {}
    for м in після["маніфест"]:
        assert hashlib.sha256((ТЕКА / м["фото"]).read_bytes()).hexdigest() == м["sha256"], м
        маніфест[м["id"], м["файл"], м["url"]] = м
    рядки, плитки = [], []
    for ід, записи in після["записи"].items():
        assert {в["файл"] for в in записи} <= вибірка[ід], ід
        старі = {в["файл"]: в for в in до[ід]}
        зміни = []
        for в in записи:
            с = старі[в["файл"]]
            м = маніфест.get((ід, в["файл"], в["url"]))
            if в.get("вимір"):
                assert м is not None, в
            if в["url"] == с["url"]:
                assert в.get("клас") == с.get("клас"), в
            відстань = math.dist(с["lab"], в["lab"]) if с.get("lab") and в.get("lab") else None
            рядки.append(dict(id=ід, назва=підписи[ід]["назва"],
                колір_крамниці=підписи[ід]["колір_сирий"],
                файл=в["файл"], url=в["url"], клас=в.get("клас"),
                слово_до=с.get("слово"), hex_до=с.get("hex"),
                слово_після=в.get("слово"), hex_після=в.get("hex"),
                тип=в.get("колір_тип"), придатна=bool(К.вимір_кадру(в)),
                розкид=в.get("розкид"), delta_E76=round(відстань, 3) if відстань is not None else None,
                маска_до=с.get("маска"), маска=в.get("маска"),
                причина=в.get("чому"), фото=м["фото"] if м else None))
            if м:
                зміни.append((в, с, м, відстань))
        кандидати = [р for р in зміни if р[0].get("клас") in К.КАДР_КАРТКИ] or зміни
        if кандидати:
            в, с, м, відстань = max(кандидати, key=lambda р: р[3] if р[3] is not None else -1)
            плитки.append((ід, в, с, м, відстань))
    with (ТЕКА / "зміни.tsv").open("w", encoding="utf-8", newline="") as файл:
        писар = csv.DictWriter(файл, fieldnames=list(рядки[0]), delimiter="\t")
        писар.writeheader()
        писар.writerows(рядки)
    числа = dict(речей=len(після["записи"]), кадрів=len(рядки),
        вимірів_до=sum(bool(К.вимір_кадру(в)) for ід, зап in після["записи"].items()
                      for в in до[ід] if в["файл"] in {н["файл"] for н in зап}),
        вимірів_після=sum(р["придатна"] for р in рядки),
        невідомих=sum(not р["придатна"] for р in рядки),
        змінили_hex=sum(р["hex_до"] != р["hex_після"] for р in рядки),
        змінили_hex_придатних=sum(р["придатна"] and р["hex_до"] != р["hex_після"] for р in рядки),
        змінили_слово=sum(р["слово_до"] != р["слово_після"] for р in рядки),
        змінили_маску=sum(р["маска_до"] != р["маска"] for р in рядки),
        маски=dict(collections.Counter(р["маска"] for р in рядки)),
        збережених_кадрів=len(маніфест),
        фото_байтів=sum(ф.stat().st_size for ф in (ТЕКА / "фото").glob("*.jpg")))
    with (ТЕКА / "черга_ДО.tsv").open(encoding="utf-8") as файл:
        черга = list(csv.DictReader(файл, delimiter="\t"))
    числа["черга_речей"] = len(черга)
    числа["черга_кадрів"] = sum(int(р["кадрів"]) for р in черга)
    причини = collections.Counter()
    for р in черга:
        for частина in р["причини"].split(","):
            причина, число = частина.rsplit("=", 1)
            причини[причина] += int(число)
    числа["черга_причини"] = dict(причини)
    числа["залишилось_галерей_вибірки"] = len(set(вибірка) - set(після["записи"]))
    числа["кадрів_вибірки_без_нового_запису"] = sum(
        len(файли - {в["файл"] for в in після["записи"].get(ід, [])}) for ід, файли in вибірка.items())
    (ТЕКА / "числа.json").write_text(json.dumps(числа, ensure_ascii=False, indent=2), encoding="utf-8")
    шрифт = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    for початок in range(0, len(плитки), 10):
        аркуш = Image.new("RGB", (1500, 760), "white")
        олівець = ImageDraw.Draw(аркуш)
        for н, (ід, в, с, м, відстань) in enumerate(плитки[початок:початок + 10]):
            x, y = (н % 5) * 300, (н // 5) * 380
            фото = ImageOps.contain(Image.open(ТЕКА / м["фото"]).convert("RGB"), (290, 250))
            аркуш.paste(фото, (x + (300 - фото.width) // 2, y))
            номер_речі, крамниця = ід.split("@", 1)
            олівець.text((x + 5, y + 252), "%d. %s" % (початок + н + 1, номер_речі), fill="black", font=шрифт)
            олівець.text((x + 5, y + 270), крамниця, fill="black", font=шрифт)
            for зсув, назва, запис in ((0, "ДО", с), (145, "ПІСЛЯ", в)):
                олівець.rectangle((x + 5 + зсув, y + 290, x + 50 + зсув, y + 325),
                                  fill=запис.get("hex") or "#eeeeee", outline="black")
                олівець.text((x + 55 + зсув, y + 290), назва, fill="black", font=шрифт)
                олівець.text((x + 5 + зсув, y + 330), запис.get("слово") or "невідомо", fill="black", font=шрифт)
            поверхня = в.get("вимір") or {}
            олівець.text((x + 5, y + 350), "Δ76 %s · %s · %s" %
                         (round(відстань, 1) if відстань is not None else "—", в.get("маска"),
                          поверхня.get("візерунок") or "нема"),
                         fill="black", font=шрифт)
            край = x + 5
            for _, частка, hex, _ in поверхня.get("сегменти", []):
                праворуч = min(x + 295, край + round(частка * 290))
                if праворуч > край:
                    олівець.rectangle((край, y + 370, праворуч, y + 378), fill=hex)
                край = праворуч
        аркуш.save(ТЕКА / ("огляд_%02d.jpg" % (початок // 10 + 1)), quality=92)
    print(json.dumps(числа, ensure_ascii=False))


if __name__ == "__main__":
    головна()

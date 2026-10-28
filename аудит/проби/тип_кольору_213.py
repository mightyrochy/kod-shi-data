"""Каталог 2.13 у трьох деревах: лічба та аркуш фото, без викликів моделей.

Аргументи: JSON каталогу до #1735, JSON бази наряду, JSON голови, тека доказів [--кадри].
JSON — результат FK.прочитати_каталог(feed.каталог_на_диску(), 0).
"""
import argparse
import concurrent.futures
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
import колір_річ as КР
import colorspace as КС


def читати(шлях):
    """Прочитати знімок каталогу за id."""
    return {р["id"]: р for р in json.loads(шлях.read_text(encoding="utf-8"))["каталог"]}


def аркуші(ід, до, після, тека):
    """Завантажити кадри й намалювати фото, типи та збережений вимір поруч."""
    import urllib.request
    from PIL import Image, ImageDraw, ImageFont
    кеш = тека / "фото"
    кеш.mkdir(exist_ok=True)
    шрифт = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
    def кадр(і):
        р = після[і]
        шлях = кеш / (і.replace("@", "_") + ".jpg")
        адреса = next(iter(р.get("фото") or []), None)
        if not адреса:
            return і, None, "фото нема"
        try:
            if not шлях.exists():
                with urllib.request.urlopen(адреса, timeout=20) as запит:
                    з = Image.open(io.BytesIO(запит.read())).convert("RGB")
                з.thumbnail((230, 230))
                з.save(шлях)
            return і, Image.open(шлях).convert("RGB"), None
        except (OSError, ValueError) as п:
            return і, None, type(п).__name__
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as пул:
        кадри = {і: (з, п) for і, з, п in пул.map(кадр, ід)}
    помилки = []
    for стор in range((len(ід) + 23) // 24):
        полотно = Image.new("RGB", (1440, 1360), "white")
        перо = ImageDraw.Draw(полотно)
        for н, і in enumerate(ід[стор * 24:(стор + 1) * 24]):
            x, y = (н % 6) * 240, (н // 6) * 340
            з, п = кадри[і]
            if з:
                полотно.paste(з, (x + (240 - з.width) // 2, y))
            else:
                помилки.append(dict(id=і, помилка=п))
                перо.text((x + 4, y + 80), п or "фото нема", font=шрифт, fill="red")
            р = після[і]
            перо.text((x + 4, y + 232), і, font=шрифт, fill="black")
            перо.text((x + 4, y + 250), str(р.get("колір_назва")), font=шрифт, fill="black")
            перо.text((x + 4, y + 268), "ДО: " + КР.тип_кольору(до.get(і, {})), font=шрифт, fill="black")
            перо.text((x + 4, y + 286), "ПІСЛЯ: " + КР.тип_кольору(р), font=шрифт, fill="black")
            hex_ = (р.get("колір_вимір") or {}).get("hex")
            if hex_:
                перо.rectangle((x + 4, y + 309, x + 52, y + 333), fill=hex_)
                перо.text((x + 60, y + 312), "фото " + hex_, font=шрифт, fill="black")
        полотно.save(тека / ("кадри_%d.jpg" % (стор + 1)), quality=90)
    return помилки


def головна():
    """Порівняти походження та тип; джерело даних зберегти в короткому JSON."""
    арг = argparse.ArgumentParser(description=__doc__)
    for ім in ("давній", "до", "після", "тека"):
        арг.add_argument(ім, type=Path)
    арг.add_argument("--кадри", action="store_true")
    а = арг.parse_args()
    давній, до, після = map(читати, (а.давній, а.до, а.після))
    а.тека.mkdir(parents=True, exist_ok=True)
    група = [і for і, р in давній.items() if р.get("колір_джерело") == "фото" and до.get(і, {}).get("колір_джерело") == "назва_вікно"]
    змінені = [і for і, р in після.items() if і in до and КР.тип_кольору(до[і]) != КР.тип_кольору(р)]
    звіт = dict(дерева=[str(а.давній), str(а.до), str(а.після)], до=len(до), після=len(після),
        втрачено=len(до.keys() - після.keys()),
        типи={т: sum(КР.тип_кольору(р) == т for р in після.values()) for т in ("вимір", "інтервал", "невідомо")},
        невимір_з_lab=sum(bool(р.get("lab")) for р in після.values() if КР.тип_кольору(р) != "вимір"),
        група_59=група, збережено_фото=sum(bool(після.get(і, {}).get("колір_вимір")) for і in група),
        група_вимір=sum(КР.тип_кольору(після.get(і)) == "вимір" for і in група), змінені=змінені)
    if а.кадри:
        звіт["помилки_фото"] = аркуші(list(dict.fromkeys(група + змінені)), до, після, а.тека)
    (а.тека / "каталог.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({к: len(в) if isinstance(в, list) else в for к, в in звіт.items()}, ensure_ascii=False))


if __name__ == "__main__":
    головна()

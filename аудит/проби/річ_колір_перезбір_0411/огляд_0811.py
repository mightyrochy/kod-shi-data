"""Показати кожен новий кадр поряд зі старим кольором і новими сегментами."""
import gzip
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ТЕКА = Path(__file__).resolve().parent


def головна():
    """П’ять аркушів з ATR-кадрів у рівних кроках: вибірка, не вся дельта."""
    числа = json.loads((ТЕКА / "числа_0811.json").read_text(encoding="utf-8"))
    після = json.loads(gzip.decompress((ТЕКА / "дельта.json.gz").read_bytes()))
    до = json.loads(gzip.decompress((ТЕКА / "кадри_ДО.json.gz").read_bytes()))["записи"]
    підписи = json.loads((ТЕКА / "підписи.json").read_text(encoding="utf-8"))
    фото = {(м["id"], м["файл"]): ТЕКА / м["фото"] for м in після["маніфест"]}
    кадри = [(ід, в) for ід in числа["нові_id"] for в in після["записи"][ід] if (ід, в["файл"]) in фото and в.get("маска") == "ATR"]
    шрифт = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    for початок in (0, 20, 40, 60, 80):
        аркуш = Image.new("RGB", (1600, 900), "white")
        for н, (ід, в) in enumerate(кадри[початок:початок + 8]):
            плитка = Image.new("RGB", (400, 450), "white")
            олівець = ImageDraw.Draw(плитка)
            x, y = 0, 0
            зображення = ImageOps.contain(Image.open(фото[ід, в["файл"]]).convert("RGB"), (390, 290))
            плитка.paste(зображення, (x + (400 - зображення.width) // 2, y))
            с = next(с for с in до[ід] if с["файл"] == в["файл"])
            поверхня = в.get("вимір") or {}
            олівець.text((x + 5, y + 292), "%d. %s" % (початок + н + 1, ід), fill="black", font=шрифт)
            олівець.text((x + 5, y + 314), в["файл"][:45], fill="black", font=шрифт)
            олівець.text((x + 5, y + 336), "Крамниця: " + str(підписи.get(ід, {}).get("колір_сирий")),
                          fill="black", font=шрифт)
            for зсув, назва, запис in ((0, "ДО", с), (195, "ПІСЛЯ", в)):
                олівець.rectangle((x + 5 + зсув, y + 360, x + 45 + зсув, y + 390),
                                  fill=запис.get("hex") or "#eeeeee", outline="black")
                олівець.text((x + 50 + зсув, y + 358), назва, fill="black", font=шрифт)
                олівець.text((x + 50 + зсув, y + 378), запис.get("слово") or "невідомо",
                              fill="black", font=шрифт)
            олівець.text((x + 5, y + 398), "%s · %s · розкид %s" % (в.get("маска"),
                          поверхня.get("візерунок") or "утримано", в.get("розкид")), fill="black", font=шрифт)
            край = x + 5
            for _, частка, hex, _ in поверхня.get("сегменти", []):
                праворуч = min(x + 395, край + round(частка * 390))
                if праворуч > край:
                    олівець.rectangle((край, y + 427, праворуч, y + 444), fill=hex)
                край = праворуч
            аркуш.paste(плитка, ((н % 4) * 400, (н // 4) * 450))
        аркуш.save(ТЕКА / ("огляд_0811_%03d.jpg" % початок), quality=92)
    print("кадрів для огляду:", len(кадри))


if __name__ == "__main__":
    головна()

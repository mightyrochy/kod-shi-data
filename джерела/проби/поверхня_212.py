# -*- coding: utf-8 -*-
"""Наряд 2.12, стенд: збережені кадр, маска й мітки ATR → ПІСЛЯ (`виміряти_поверхню`) і аркуші ДО/ПІСЛЯ.

ЧИТАЄ теку `аудит/проби/поверхня_212/` (її пише `прилади/вимір_поверхні_212.py` на ноутбуці): `вимір.json`
(ДО, джерело маски, слово крамниці), `<ключ>.jpg`, `<ключ>.маска.png`, `<ключ>.atr.png`. Мережі нема.
ПИШЕ туди ж `після.json` і аркуші: `аркуш_6431_темні.jpg`, `аркуш_6432_принти.jpg`, `аркуш_6433_світлі.jpg`,
`аркуш_решта.jpg` (решта з 40), `аркуш_8073_cooshwear.jpg`. Рядок аркуша: кадр, маска на кадрі, ДО (основний і
другий кластер старого виміру), ПІСЛЯ (сегменти поверхні й візерунок або «невідомо → слово крамниці»), що бачили очі.
Суд — очима за мірилом наряду; стенд нічого не оцінює сам.

Запуск: cd джерела && python3 -W ignore проби/поверхня_212.py [--тека <тека>]
"""
import argparse, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
КОРІНЬ = os.path.dirname(ТУТ)
ВЕРДИКТИ = os.path.join(КОРІНЬ, "аудит", "проби", "темні_5661_вердикти.json")
КЛАСИ = [("6431_темні", (13, 18, 21, 22, 23, 25, 26, 27, 36, 38)), ("6432_принти", (8, 11, 14, 32, 37, 39)),
         ("6433_світлі", (4, 5, 10, 34))]
ВИСОТА = 220


def після(тека, зап):
    """ПІСЛЯ з тих самих файлів: поверхня придатна → сегменти й основний; ні → колір за словом крамниці."""
    import cv2
    from жнива_колір import виміряти_поверхню, звести_колір, стиснути_поверхню
    к = зап["ключ"]
    bgr = cv2.imread(os.path.join(тека, к + ".jpg"))
    м = cv2.imread(os.path.join(тека, к + ".маска.png"), cv2.IMREAD_GRAYSCALE)
    if bgr is None or м is None:
        return None
    ш_atr = os.path.join(тека, к + ".atr.png")
    арр = cv2.imread(ш_atr, cv2.IMREAD_GRAYSCALE) if os.path.exists(ш_atr) else None
    п = виміряти_поверхню(bgr, м, арр)
    осн = звести_колір(п["сегменти"], None, зап.get("слова_крамниці"))[0] if п["придатна"] else None
    return dict(стиснути_поверхню(п), основний=осн and [осн["слово"], осн["hex"], осн["частка"]])


def шрифт(розмір):
    from PIL import ImageFont
    for ім in ("arial.ttf", "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(ім, розмір)
        except OSError:
            pass
    return ImageFont.load_default()


def рядок(тека, зап, п, підпис, Ш):
    """Один рядок аркуша: кадр | маска | ДО | ПІСЛЯ | текст."""
    import cv2, numpy as np
    from PIL import Image, ImageDraw
    полотно = Image.new("RGB", (Ш, ВИСОТА + 10), "white")
    д = ImageDraw.Draw(полотно)
    ф, фм = шрифт(15), шрифт(13)
    x = 5
    bgr = cv2.imread(os.path.join(тека, зап["ключ"] + ".jpg"))
    if bgr is not None:
        м = cv2.imread(os.path.join(тека, зап["ключ"] + ".маска.png"), cv2.IMREAD_GRAYSCALE)
        накл = bgr.copy()
        if м is not None:
            накл[м > 127] = (0.55 * накл[м > 127] + 0.45 * np.array((255, 0, 255))).astype("uint8")
            конт, _ = cv2.findContours((м > 127).astype("uint8"), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(накл, конт, -1, (255, 0, 255), 2)
        for кадр in (bgr, накл):
            h, w = кадр.shape[:2]
            ш = int(w * ВИСОТА / h)
            полотно.paste(Image.fromarray(cv2.cvtColor(cv2.resize(кадр, (ш, ВИСОТА)), cv2.COLOR_BGR2RGB)), (x, 5))
            x += ш + 5
    x = max(x, 2 * ВИСОТА + 15)

    def латки(x, y, заголовок, пари):
        д.text((x, y), заголовок, fill="black", font=ф)
        for і, (сл, hx, ч) in enumerate(пари[:4]):
            д.rectangle((x, y + 22 + і * 34, x + 40, y + 52 + і * 34), fill=hx, outline="black")
            д.text((x + 46, y + 28 + і * 34), "%s %s %.0f%%" % (сл, hx, 100 * ч), fill="black", font=фм)
    до = зап.get("до") or {}
    латки(x, 5, "ДО: " + (до.get("основний") or ["невідомо"])[0], [(с, h, ч) for с, ч, h in до.get("кластери") or []])
    x += 230
    if п is None:
        д.text((x, 5), "ПІСЛЯ: нема маски — колір за словом крамниці", fill="black", font=ф)
    elif not п["придатна"]:
        д.text((x, 5), "ПІСЛЯ: невідомо → слово крамниці", fill="black", font=ф)
        д.multiline_text((x, 30), "\n".join(_розбити(п["чому"], 34)), fill="black", font=фм)
    else:
        латки(x, 5, "ПІСЛЯ: %s · %s" % (п["основний"][0], п["візерунок"]),
              [(с, h, ч) for с, ч, h, _ in п["сегменти"]])
    x += 260
    д.multiline_text((x, 5), "\n".join(_розбити(підпис, 44)[:12]), fill="black", font=фм)
    return полотно


def _розбити(т, n):
    вих, р = [], ""
    for сл in (т or "").split():
        if len(р) + len(сл) + 1 > n:
            вих.append(р)
            р = сл
        else:
            р = (р + " " + сл).strip()
    return вих + ([р] if р else [])


def аркуш(тека, ім, ключі, записи, пп, підписи):
    from PIL import Image
    Ш = 1500
    рядки = [рядок(тека, записи[к], пп.get(к), підписи.get(к, ""), Ш) for к in ключі if к in записи]
    if not рядки:
        return
    а = Image.new("RGB", (Ш, sum(р.size[1] for р in рядки)), "white")
    y = 0
    for р in рядки:
        а.paste(р, (0, y))
        y += р.size[1]
    а.save(os.path.join(тека, "аркуш_%s.jpg" % ім), "JPEG", quality=85)


def main():
    ап = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ап.add_argument("--тека", default=os.path.join(КОРІНЬ, "аудит", "проби", "поверхня_212"))
    тека = ап.parse_args().тека
    записи = {з["ключ"]: з for з in json.load(open(os.path.join(тека, "вимір.json"), encoding="utf-8"))["записи"]}
    пп = {к: після(тека, з) for к, з in записи.items() if not з.get("помилка")}
    with open(os.path.join(тека, "після.json"), "w", encoding="utf-8") as ф:
        json.dump(пп, ф, ensure_ascii=False, indent=1)
    вердикти = {"%02d" % в["№"]: в for в in json.load(open(ВЕРДИКТИ, encoding="utf-8"))}
    підписи = {к: "№%s %s · крамниця «%s» · маска %s · очі: %s" % (к, з["id"], ", ".join(з.get("слова_крамниці") or []),
                                                                   з.get("маска"), (вердикти.get(к) or {}).get("що_видно", ""))
               for к, з in записи.items()}
    в_класах = set()
    for ім, номери in КЛАСИ:
        ключі = ["%02d" % н for н in номери]
        в_класах.update(ключі)
        аркуш(тека, ім, ключі, записи, пп, підписи)
    аркуш(тека, "решта", sorted(к for к in записи if к in вердикти and к not in в_класах), записи, пп, підписи)
    аркуш(тека, "8073_cooshwear", sorted(к for к in записи if к.startswith("к")), записи, пп, підписи)
    for к in sorted(записи):
        з, п = записи[к], пп.get(к)
        print(к, (з.get("до") or {}).get("основний"), "→", п and (п["основний"] or "невідомо", п["візерунок"]),
              з.get("помилка") or "")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Наряд ПС-5, хмара: власні кадри речі → кадр ≤ 512, маска ATR і мітки ATR на диску для стенда кількох кадрів.

ЧИТАЄ: вибірку стенда 2.12 (`аудит/проби/поверхня_212/вимір.json`: 40 речей 5661 і 12 cooshwear — головний кадр,
його маска ATR→SAM уже збережені там і копіюються як є), повний каталог (`каталог_повний.xml`: галерея, слот, слово
крамниці), збагачення (кадр виміру — головний кадр випадкової частини), `фід_фото.кадри_речі` (власні кадри картки:
службові й чужі картинки крамниці вже відсіяно), фото крамниць по HTTP, ATR (Leffa ONNX на CPU). SAM (ComfyUI) у
хмарі нема: кадр, якого ATR не взяв, лишається з запасною маскою, а її вимір поверхні — «невідомо».
ВИПАДКОВА ЧАСТИНА: 48 речей каталогу з виміряним кольором і ≥ 2 власними кадрами, `random.Random(5)` над
упорядкованими id — щоб частка розбіжностей не трималась лише вибірки проблемних 5661.
ПИШЕ: `аудит/проби/пс5_кадри/` — `<ключ>-<n>.jpg`, `.маска.png`, `.atr.png` (n = 0 — головний кадр) і `кадри.json`
(річ: id, слот, слова крамниці, колір каталогу; кадр: адреса, джерело маски, чому). ДО/ПІСЛЯ рахує стенд
`прилади/стенд_кадрів_пс5.py` з цих файлів, офлайн.

Запуск: cd джерела && python3 -W ignore прилади/кадри_поверхні_пс5.py [--кадрів 4] [--випадкових 48]
"""
import argparse, json, os, random, shutil, sys, tempfile
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
КОРІНЬ = os.path.dirname(ТУТ)
СТЕНД_212 = os.path.join(КОРІНЬ, "аудит", "проби", "поверхня_212")
ВИХІД = os.path.join(КОРІНЬ, "аудит", "проби", "пс5_кадри")


def зберегти(ключ, шлях, м, арр):
    """Кадр ≤ 512 (JPEG 90), маска й мітки ATR того самого розміру (PNG, найближчий сусід)."""
    import cv2, numpy as np
    from surface import ДОВГА_СТОРОНА
    bgr = cv2.imread(шлях)
    h, w = bgr.shape[:2]
    к = min(1.0, ДОВГА_СТОРОНА / float(max(h, w)))
    розм = (max(1, int(round(w * к))), max(1, int(round(h * к))))
    мала = cv2.resize(bgr, розм, interpolation=cv2.INTER_AREA) if к < 1.0 else bgr
    cv2.imwrite(os.path.join(ВИХІД, ключ + ".jpg"), мала, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if м is not None:
        cv2.imwrite(os.path.join(ВИХІД, ключ + ".маска.png"),
                    cv2.resize(((м > 127) * 255).astype("uint8"), розм, interpolation=cv2.INTER_NEAREST))
    if арр is not None:
        cv2.imwrite(os.path.join(ВИХІД, ключ + ".atr.png"),
                    cv2.resize(np.asarray(арр, "uint8"), розм, interpolation=cv2.INTER_NEAREST))


def кадр(ключ, url, слот, тека):
    """Один кадр: HTTP → маска ATR (без SAM) → файли. Збій — у записі, а не виняток."""
    import жнива_фото as ЖФ
    from жнива_маски import маска_речі, _мітки_atr
    з = dict(ключ=ключ, url=url)
    try:
        im = ЖФ._відкрити(ЖФ._качати(url))
    except Exception as e:
        з["помилка"] = "кадр: %s" % str(e)[:120]
        return з
    шлях = os.path.join(тека, "kadr.jpg")      # латиницею: cv2.imread на Windows кирилиці не бачить
    im.save(шлях, "JPEG", quality=95)
    м, dom, чому, джерело = маска_речі(шлях, слот)
    try:
        арр = _мітки_atr(шлях)
    except Exception:
        арр = None
    зберегти(ключ, шлях, м, арр)
    з.update(маска=джерело, маска_чому=чому, маска_частка=round(float(dom or 0.0), 3))
    return з


def головний_212(ключ, зап_212):
    """Головний кадр речі стенда 2.12: ті самі файли (маска ATR→SAM ноутбука), без нового запиту."""
    for хв in (".jpg", ".маска.png", ".atr.png"):
        дж = os.path.join(СТЕНД_212, зап_212["ключ"] + хв)
        if os.path.exists(дж):
            shutil.copyfile(дж, os.path.join(ВИХІД, ключ + хв))
    return dict(ключ=ключ, url=зап_212["кадр"], маска=зап_212.get("маска"), маска_чому=зап_212.get("маска_чому"),
                маска_частка=зап_212.get("маска_частка"), стенд_212=зап_212["ключ"])


def main():
    ап = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ап.add_argument("--кадрів", type=int, default=4, help="власних кадрів на річ, з головним")
    ап.add_argument("--випадкових", type=int, default=48)
    а = ап.parse_args()
    import feed, фід_каталог as FK, фід_фото as ФФ, verify as V, жнива_маски as ЖМ
    from жнива_промпти import тип_речі
    ЖМ._SAM_ЖИВИЙ = False                      # у хмарі ComfyUI нема: не чекати на нього
    оф = {o["id"]: o for o in feed.читати_yml(feed.каталог_на_диску("каталог_повний.xml"))[0]}
    зб = feed.читати_збагачення()
    сп, хо = ФФ.спільні_фото(list(оф.values())), ФФ.хости_крамниць(list(оф.values()))
    К = {r["id"]: r for r in FK.прочитати_каталог(feed.каталог_на_диску(), 0)["каталог"]}

    def кадри(ід, головний):
        """Власні кадри картки, головний першим, без повтору його файла."""
        o = оф.get(ід) or {"id": ід}
        з = зб.get(ід) if isinstance(зб.get(ід), dict) else {}
        ряд = ФФ.кадри_речі(o, сп.get(o.get("магазин")) or {}, хо, з.get("фото"))
        інші = [u for u in ряд if ФФ.файл_фото(u) != ФФ.файл_фото(головний)]
        return [головний] + інші[:а.кадрів - 1]

    def головний_зб(ід):
        з = зб.get(ід) if isinstance(зб.get(ід), dict) else {}
        return (з.get("кадр_виміру") or {}).get("url") or з.get("фото")

    стенд = json.load(open(os.path.join(СТЕНД_212, "вимір.json"), encoding="utf-8"))["записи"]
    черга = [(з["ключ"], з["id"], з) for з in стенд]
    бачені = {з["id"] for з in стенд}
    пул = sorted(ід for ід, r in К.items() if ід not in бачені and r.get("колір_hex_фото") and головний_зб(ід)
                 and len(кадри(ід, головний_зб(ід))) >= 2)
    черга += [("в%02d" % і, ід, None) for і, ід in enumerate(random.Random(5).sample(пул, а.випадкових))]
    os.makedirs(ВИХІД, exist_ok=True)
    речі = []
    with tempfile.TemporaryDirectory() as тека:
        for ключ, ід, з212 in черга:
            o, r = оф.get(ід) or {"id": ід}, К.get(ід) or {}
            try:
                _, слот = тип_речі(o)
            except Exception:
                слот = None
            сл = (V.слово_крамниці(o.get("колір_назва") or "") or {}).get("ім")
            головний = з212["кадр"] if з212 else головний_зб(ід)
            річ = dict(ключ=ключ, id=ід, слот=слот, слова_крамниці=[сл] if сл else [],
                       колір_крамниці=o.get("колір_назва"), каталог=[r.get("колір_назва_фото"), r.get("колір_hex_фото")],
                       кадри=[])
            for n, url in enumerate(кадри(ід, головний) if головний else []):
                к = "%s-%d" % (ключ, n)
                річ["кадри"].append(головний_212(к, з212) if (n == 0 and з212) else кадр(к, url, слот, тека))
            речі.append(річ)
            print(ключ, ід, [(к.get("маска") or к.get("помилка", "?"))[:8] for к in річ["кадри"]], flush=True)
    with open(os.path.join(ВИХІД, "кадри.json"), "w", encoding="utf-8") as ф:
        json.dump(dict(sam=False, кадрів=а.кадрів, сід=5, речі=речі), ф, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

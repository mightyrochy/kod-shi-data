# -*- coding: utf-8 -*-
"""Наряд 2.12, ноутбук: ті самі 40 кадрів вибірки 5661 і 12 cooshwear (8073) → кадр, маска, ДО → гілка.

ЧИТАЄ: `аудит/проби/темні_5661_вердикти.json` (40 id, кадр, на який дивились очима), збагачення
(`feed.читати_збагачення`: кадр власника кадру з кроку 5.2 — `кадр_виміру.url`, інакше `фото`), повний
каталог (`каталог_повний.xml`: слот і слово крамниці), фото крамниць по HTTP (кадр речі; лише крамниці),
ATR (`open-source-stylist`, ONNX локально) і SAM (локальний ComfyUI, коли піднятий; `--без-sam` вимикає) — ті самі
маски ATR→SAM, якими міряли ДО. LM Studio й моделі зору не кличе: слово моделі в `звести_колір` — None.
ПИШЕ: `аудит/проби/поверхня_212/` — `<ключ>.jpg` (кадр ≤ 512), `<ключ>.маска.png`, `<ключ>.atr.png` (мітки ATR),
`вимір.json` (ДО старим `виміряти_колір` + `звести_колір` на повному кадрі, джерело маски, кадр), далі стенд
`проби/поверхня_212.py` дописує `після.json` і аркуші `аркуш_*.jpg`; з `--пуш` — коміт і пуш поточної гілки.
ДО рахується тут, бо старий вимір читав кадр повного розміру; ПІСЛЯ стенд рахує з тих самих збережених файлів.

Запуск (Windows, корінь репозиторію на гілці): set PYTHONUTF8=1 && python -W ignore джерела/прилади/вимір_поверхні_212.py --пуш
"""
import argparse, json, os, subprocess, sys, tempfile
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
sys.path.insert(0, os.path.join(ТУТ, "проби"))
from поверхня_212 import писати
КОРІНЬ = os.path.dirname(ТУТ)
ВЕРДИКТИ = os.path.join(КОРІНЬ, "аудит", "проби", "темні_5661_вердикти.json")
ВИХІД = os.path.join(КОРІНЬ, "аудит", "проби", "поверхня_212")
COOSH = ["ж-%05d@cooshwear.com" % н for н in
         (6961, 4745, 8864, 507, 5114, 7822, 6935, 1783, 6968, 4348, 6056, 4725)]


def кадр_запису(з, запасний):
    """Кадр речі — запис власника кадру (5.2), не назва файла; нема — кадр, на який дивились очима."""
    з = з if isinstance(з, dict) else {}
    return (з.get("кадр_виміру") or {}).get("url") or з.get("фото") or запасний


def зберегти(ключ, шлях, м, арр):
    """Кадр ≤ 512 (JPEG 95), маска й мітки ATR того самого розміру (PNG, найближчий сусід)."""
    import cv2, numpy as np
    from жнива_колір import ДОВГА_СТОРОНА
    bgr = cv2.imread(шлях)        # тимчасовий файл, ім'я латиницею (див. `одна`)
    h, w = bgr.shape[:2]
    к = min(1.0, ДОВГА_СТОРОНА / float(max(h, w)))
    розм = (max(1, int(round(w * к))), max(1, int(round(h * к))))
    мала = cv2.resize(bgr, розм, interpolation=cv2.INTER_AREA) if к < 1.0 else bgr
    писати(os.path.join(ВИХІД, ключ + ".jpg"), мала, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if м is not None:
        мм = cv2.resize(((м > 127) * 255).astype("uint8"), розм, interpolation=cv2.INTER_NEAREST)
        писати(os.path.join(ВИХІД, ключ + ".маска.png"), мм)
    if арр is not None:
        писати(os.path.join(ВИХІД, ключ + ".atr.png"),
               cv2.resize(np.asarray(арр, "uint8"), розм, interpolation=cv2.INTER_NEAREST))


def одна(ключ, ід, url, слот, слова, тека):
    """Одна річ: кадр → маска → ДО. Помилка кадру чи маски — у записі, а не виняток."""
    import жнива_фото as ЖФ
    from жнива_маски import маска_речі, _мітки_atr
    from жнива_колір import виміряти_колір, звести_колір
    зап = dict(ключ=ключ, id=ід, кадр=url, слот=слот, слова_крамниці=слова)
    if not url:
        зап["помилка"] = "кадру нема ні в записі, ні у вердикті"
        return зап
    try:
        im = ЖФ._відкрити(ЖФ._качати(url))
    except Exception as e:
        зап["помилка"] = "кадр: %s" % str(e)[:120]
        return зап
    # ІМ'Я ЛАТИНИЦЕЮ: `cv2.imread` на Windows відкриває файл ANSI-викликом і кириличного шляху не бачить
    # («к00.jpg» → None на ноутбуці), а маска й старий вимір читають файл самі — прийом `жнива_фото.взяти_фото`.
    шлях = os.path.join(тека, "kadr-%s.jpg" % ключ.replace("к", "k"))
    im.save(шлях, "JPEG", quality=95)
    м, dom, чому, джерело = маска_речі(шлях, слот)
    try:
        арр = _мітки_atr(шлях)
    except Exception:
        арр = None
    зберегти(ключ, шлях, м, арр)
    зап.update(маска=джерело, маска_чому=чому, маска_частка=round(float(dom or 0.0), 3))
    if м is None:
        зап["до"] = None
        return зап
    кл, _ = виміряти_колір(шлях, м)
    осн, друг, _ = звести_колір(кл, None, слова)
    зап["до"] = dict(основний=осн and [осн["слово"], осн["hex"], осн["частка"]],
                     другий=друг and [друг["слово"], друг["hex"], друг["частка"]],
                     кластери=[[к["слово"], к["частка"], к["hex"]] for к in кл])
    return зап


def main():
    ап = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ап.add_argument("--без-sam", dest="без_sam", action="store_true", help="не кликати локальний ComfyUI (SAM)")
    ап.add_argument("--пуш", action="store_true", help="коміт і пуш теки результату в поточну гілку")
    арг = ап.parse_args()
    import feed, жнива_маски as ЖМ
    from жнива_промпти import тип_речі
    from verify import слово_крамниці
    if арг.без_sam:
        ЖМ._SAM_ЖИВИЙ = False      # без ComfyUI: ATR не взяв річ → запасна маска (з тлом)
    зб = feed.читати_збагачення()
    оф = {o["id"]: o for o in feed.читати_yml(feed.каталог_на_диску("каталог_повний.xml"))[0]}
    вердикти = json.load(open(ВЕРДИКТИ, encoding="utf-8"))
    черга = [("%02d" % в["№"], в["id"], кадр_запису(зб.get(в["id"]), в.get("кадр_дивилась"))) for в in вердикти]
    черга += [("к%02d" % і, ід, кадр_запису(зб.get(ід), ((оф.get(ід) or {}).get("фото") or [None])[0]))
              for і, ід in enumerate(COOSH)]
    os.makedirs(ВИХІД, exist_ok=True)
    записи = []
    with tempfile.TemporaryDirectory() as тека:
        for ключ, ід, url in черга:
            o = оф.get(ід) or {"id": ід}
            try:
                _, слот = тип_речі(o)
            except Exception:
                слот = None
            сл = (слово_крамниці(o.get("колір_назва") or "") or {}).get("ім")
            зап = одна(ключ, ід, url, слот, [сл] if сл else [], тека)
            записи.append(зап)
            print(ключ, ід, зап.get("маска") or зап.get("помилка"), (зап.get("до") or {}).get("основний"))
    with open(os.path.join(ВИХІД, "вимір.json"), "w", encoding="utf-8") as ф:
        json.dump(dict(sam=not арг.без_sam and bool(ЖМ._SAM_ЖИВИЙ), записи=записи), ф, ensure_ascii=False, indent=1)
    subprocess.check_call([sys.executable, "-W", "ignore", os.path.join(ТУТ, "проби", "поверхня_212.py"),
                           "--тека", ВИХІД])
    if арг.пуш:
        гілка = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        subprocess.check_call(["git", "add", ВИХІД])
        subprocess.check_call(["git", "commit", "-m", "2.12: кадри, маски й ДО/ПІСЛЯ вибірки 5661 і 8073 (ноутбук)"])
        subprocess.check_call(["git", "push", "--no-thin", "-u", "origin", гілка])


if __name__ == "__main__":
    main()

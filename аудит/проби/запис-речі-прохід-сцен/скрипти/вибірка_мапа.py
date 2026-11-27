#!/usr/bin/env python3
"""Перевірка вибірки мапи ід (наряд, п.1): 30 рядків пулу, яким мапа дала ід, а звіт `стилістка-вибір-з-пулу` ід не мав
(зерно 20261127, з кожної сцени не більше двох), — аркуш: кадр і назва речі з каталогу поруч з ознаками самого рядка
(тип, слово кольору, зразок hex, ціна, L). Оглядач дивиться аркуш і каже для кожного: збігається / хибне.
Вихід: `дані/вибірка_мапи.json` (ключ: запит, n, ід, статус, ознаки), аркуші `/tmp/аркуш_мапи_<k>.png` (не комітяться).
Запуск з кореня: python3 -I <цей файл>"""
import csv, gzip, importlib.util, io, json, pickle, random, textwrap, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
К = Path(__file__).resolve().parents[4]; Д = К / "аудит/проби/запис-речі-прохід-сцен/дані"
сп = importlib.util.spec_from_file_location("м", К / "аудит/проби/запис-речі-прохід-сцен/скрипти/мапа_ід.py")
М = importlib.util.module_from_spec(сп); сп.loader.exec_module(М)
мапа = json.load(gzip.open(Д / "мапа_ід.json.gz", "rt", encoding="utf-8"))
відомі = {(р["запит"], р["n"]) for р in csv.DictReader(gzip.open(К / "аудит/звіти/стилістка-вибір-з-пулу/рядки.csv.gz", "rt", encoding="utf-8")) if р["ід"]}
кандидати = sorted((з, n, tuple(v)) for з, рс in мапа.items() for n, v in рс.items() if v[0] and (з, n) not in відомі)
random.Random(20261127).shuffle(кандидати)
вибір, за_сценою = [], {}
for з, n, v in кандидати:
    с = з.split("/")[0]
    if за_сценою.get(с, 0) >= 2: continue
    за_сценою[с] = за_сценою.get(с, 0) + 1; вибір.append((з, n, v))
    if len(вибір) == 30: break
рядки = {}
for сц, (пр, л), рс in М.джерела(): рядки[f"{сц}/{пр}/{л}"] = {r["n"]: r for r in рс}
М.проєкція(); кат = pickle.load((М.КЕШ / "каталог.pkl").open("rb"))
шрифт = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
ключ_, клітинки = [], []
for k, (з, n, v) in enumerate(вибір, 1):
    р = рядки[з][n]; р_ = кат[v[0]]
    ознаки = {x: р.get(x) for x in ("type", "color", "hex", "price", "L", "fabric", "cut") if р.get(x) is not None}
    ключ_.append({"№": k, "запит": з, "n": n, "ід": v[0], "статус": v[1], "ознаки_рядка": ознаки, "назва": р_["назва"], "ціна_каталогу": р_["ціна"]})
    кл = Image.new("RGB", (300, 400), "white"); d = ImageDraw.Draw(кл)
    try:
        дані_ = urllib.request.urlopen(urllib.request.Request(р_["фото"][0], headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        ф = Image.open(io.BytesIO(дані_)).convert("RGB"); ф.thumbnail((300, 270)); кл.paste(ф, (0, 0))
    except Exception as е:
        d.text((5, 100), f"кадр: {type(е).__name__}", fill="red", font=шрифт)
    hx = ознаки.get("hex")
    if hx: d.rectangle((260, 5, 295, 40), fill=hx, outline="black")
    текст = f"{k}. {р_['назва'][:60]}\nкаталог: {р_['ціна']:.0f} грн\nрядок: {ознаки.get('type')}, {ознаки.get('color')}, {ознаки.get('price')} грн, L={ознаки.get('L')} {ознаки.get('hex') or ''}"
    d.multiline_text((4, 275), "\n".join(textwrap.fill(x, 42) for x in текст.split("\n")), fill="black", font=шрифт)
    клітинки.append(кл)
for а in range(0, 30, 6):
    ар = Image.new("RGB", (900, 800), "white")
    for i, кл in enumerate(клітинки[а:а + 6]): ар.paste(кл, ((i % 3) * 300, (i // 3) * 400))
    ар.save(f"/tmp/аркуш_мапи_{а // 6 + 1}.png")
(Д / "вибірка_мапи.json").write_text(json.dumps(ключ_, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(ключ_), {с: n for с, n in за_сценою.items()})

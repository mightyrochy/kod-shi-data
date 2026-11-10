# -*- coding: utf-8 -*-
"""галереї.py — усі фото речі для сторінки огляду кольору: кадр проби й галерея варіанта з каталогу.

Запуск з кореня репозиторію (після `git fetch origin claude/Річ-колір-вимір`):
  python3 -I аудит/проби/річ_колір_огляд_людьми/галереї.py --ід sproba2 --кеш <тека> \
      --звіт аудит/проби/річ_колір_модель_бачить/спроба_2/звіт.tsv \
      --звіт аудит/проби/річ_колір_модель_бачить/спроба_2/запасні/звіт.tsv
→ `галереї_<ід>.tsv` тут (номер, порядок, файл, джерело, url, sha256, байтів, чому) і файли в `ohliad-koloru/foto/`.

Звідки фото (наряд, «Ціль»: галерея варіанта в каталозі; які кадри вже є в гілці кадрів, а які — лише посиланням
крамниці). Перше — кадр проби, який міряв код (рядок `кадр` таблиці проби). Далі — `<picture>` пропозиції речі в
`каталог_повний.xml.gz` у порядку каталогу: є в маніфесті дельти перезбору й у гілці кадрів 43dd34ad — байти звідти
(те, що бачили проба й код); нема — завантаження з крамниці байт у байт (`--кеш`, повтор без мережі), відмова чи не
зображення — посилання крамниці (сторінка показує його, а не вдалось на телефоні — кадр ховає). Наприкінці — кадри
речі з маніфесту, яких у нинішньому каталозі нема (крамниця змінила галерею після перезбору). Дублікат кадру (той
самий файл чи майже той самий образ, різниця dHash ≤ 4 з 64) — пропускається з причиною: лишається перший, тобто
кадр проби, потім гілка. Кадри не перетискаються: профіль кольору й стиснення — крамниці.
"""
import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

КОРІНЬ = Path(__file__).resolve().parents[3]
ДАНІ = "43dd34adee5bf462c70cbdc9f01719da7250719e"
ТЕКА_ДАНИХ = "аудит/проби/річ_колір_перезбір_0411/"
ПОЛЯ = ("номер", "порядок", "файл", "джерело", "url", "sha256", "байтів", "чому")
РОЗШИРЕННЯ = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif"}
ПОРІГ_DHASH = 4
ПАУЗА = [1.0]  # секунд між запитами до однієї крамниці (`--пауза`)
СТАРШИНСТВО = {"кадр проби": 0, "гілка кадрів": 1, "гілка кадрів, поза нинішнім каталогом": 2,
               "крамниця, завантажено": 3, "крамниця, посилання": 4}


def git_show(шлях):
    """Байти файлу з гілки кадрів."""
    return subprocess.run(["git", "-C", str(КОРІНЬ), "show", ДАНІ + ":" + ТЕКА_ДАНИХ + шлях],
                          capture_output=True, check=True).stdout


def файли_гілки():
    """Імена кадрів у `фото/` гілки (без лапок для не-ASCII шляхів)."""
    вих = subprocess.run(["git", "-C", str(КОРІНЬ), "-c", "core.quotepath=off", "ls-tree", "--name-only", ДАНІ,
                          ТЕКА_ДАНИХ + "фото/"], capture_output=True, text=True, check=True).stdout
    return {р.rsplit("/", 1)[-1] for р in вих.split()}


def галереї_каталогу(шлях):
    """{id пропозиції: [url <picture> у порядку каталогу]}."""
    текст = gzip.open(шлях, "rt", encoding="utf-8").read()
    return {ід: [html.unescape(u).strip() for u in re.findall(r"<picture>(.*?)</picture>", тіло)]
            for ід, тіло in re.findall(r'<offer id="([^"]+)"(.*?)</offer>', текст, re.S)}


def dhash(байти):
    """Різницевий хеш 8×8 сірого образу — для майже однакових кадрів різного розміру й стиснення."""
    з = Image.open(io.BytesIO(байти)).convert("L").resize((9, 8), Image.LANCZOS)
    п = list(з.tobytes())
    return sum(1 << і for і in range(64) if п[(і // 8) * 9 + і % 8] > п[(і // 8) * 9 + і % 8 + 1])


def завантажити(url, кеш, останній, повтор=False):
    """Байти зображення з крамниці або (None, причина); кеш — щоб повтор не ходив у мережу; 429 — ще раз за 5 с."""
    ім = hashlib.md5(url.encode()).hexdigest()
    for ф in кеш.glob(ім + ".*"):
        if ф.suffix == ".відмова":
            return None, ф.read_text(encoding="utf-8"), None
        return ф.read_bytes(), "", ф.suffix
    хост = urlparse(url).netloc
    чекати = ПАУЗА[0] - (time.monotonic() - останній.get(хост, 0))
    if чекати > 0:
        time.sleep(чекати)
    запит = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kod-shi-data; ohliad-koloru)",
                                                "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(запит, timeout=30) as в:
            тип, байти = в.headers.get_content_type(), в.read()
            причина = "" if тип in РОЗШИРЕННЯ else "крамниця віддала %s, не зображення" % тип
    except urllib.error.HTTPError as е:
        тип, байти, причина = "", b"", "HTTP %d" % е.code
        if е.code == 429 and not повтор:
            останній[хост] = time.monotonic() + 4
            return завантажити(url, кеш, останній, повтор=True)
    except Exception as е:  # мережа: тайм-аут, TLS, DNS
        тип, байти, причина = "", b"", type(е).__name__
    останній[хост] = time.monotonic()
    if причина:
        (кеш / (ім + ".відмова")).write_text(причина, encoding="utf-8")
        return None, причина, None
    (кеш / (ім + РОЗШИРЕННЯ[тип])).write_bytes(байти)
    return байти, "", РОЗШИРЕННЯ[тип]


def головна():
    п = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    п.add_argument("--звіт", action="append", required=True)
    п.add_argument("--ід", required=True)
    п.add_argument("--кеш", required=True)
    п.add_argument("--каталог", default=str(КОРІНЬ / "каталог_повний.xml.gz"))
    п.add_argument("--вихід", default=str(КОРІНЬ / "ohliad-koloru" / "foto"))
    п.add_argument("--пауза", type=float, default=1.0)
    п.add_argument("--знову", action="store_true", help="ще раз спитати крамницю, що відмовила")
    а = п.parse_args()
    ПАУЗА[0] = а.пауза
    кеш, фото = Path(а.кеш), Path(а.вихід)
    кеш.mkdir(parents=True, exist_ok=True)
    if а.знову:
        for в in кеш.glob("*.відмова"):
            в.unlink()
    фото.mkdir(parents=True, exist_ok=True)
    каталог = галереї_каталогу(а.каталог)
    у_гілці = файли_гілки()
    маніфест = {}
    for м in json.loads(gzip.decompress(git_show("дельта.json.gz")))["маніфест"]:
        маніфест.setdefault(м["id"], []).append(м)
    рядки, останній = [], {}
    for шлях in а.звіт:
        with open(шлях, encoding="utf-8", newline="") as ф:
            записи = list(csv.DictReader(ф, delimiter="\t"))
        for р in записи:
            н, річ = int(р["номер"]), р["річ"]
            за_url = {м["url"]: м for м in маніфест.get(річ, [])}
            кандидати = [(Path(р["кадр"]).name, "кадр проби", "")]
            for url in каталог[річ.split("@")[0]]:
                м = за_url.get(url)
                ім = м["фото"].rsplit("/", 1)[-1] if м else None
                кандидати.append((ім if ім in у_гілці else None, "гілка кадрів" if ім in у_гілці else "крамниця", url))
            в_каталозі = set(каталог[річ.split("@")[0]])
            for м in маніфест.get(річ, []):
                ім = м["фото"].rsplit("/", 1)[-1]
                if м["url"] not in в_каталозі and ім in у_гілці:
                    кандидати.append((ім, "гілка кадрів, поза нинішнім каталогом", м["url"]))
            зібрані = []
            for ім, джерело, url in кандидати:
                чому, байти = "", None
                if ім:
                    байти = git_show("фото/" + ім)
                else:
                    байти, чому, розш = завантажити(url, кеш, останній)
                    if байти is not None:
                        ім, джерело = hashlib.md5(url.encode()).hexdigest() + розш, "крамниця, завантажено"
                зібрані.append(dict(номер=н, порядок="", файл=ім or "", джерело=джерело if байти else "крамниця, посилання",
                                    url=url, sha256=hashlib.sha256(байти).hexdigest() if байти else "",
                                    байтів=len(байти) if байти else "", чому=чому, _байти=байти))
            # дублікати — за старшинством джерела (кадр проби, гілка, гілка поза каталогом, крамниця), а показ — у
            # порядку каталогу: лишається кадр, який бачили проба й код
            хеші, бачені, лишити = [], set(), set()
            for і in sorted(range(len(зібрані)), key=lambda і: (СТАРШИНСТВО[зібрані[і]["джерело"]], і)):
                з = зібрані[і]
                if not з["_байти"]:
                    лишити.add(і)
                    continue
                try:
                    д = dhash(з["_байти"])
                except Exception as е:  # формат, який PIL не читає: без перевірки на майже дублікат
                    д, з["чому"] = None, "dHash: %s" % type(е).__name__
                близький = next((ім for ім, х in хеші if д is not None and bin(д ^ х).count("1") <= ПОРІГ_DHASH), None)
                if з["sha256"] in бачені or близький:
                    з["чому"] = "дублікат кадру %s" % (близький or "той самий файл")
                    continue
                бачені.add(з["sha256"])
                if д is not None:
                    хеші.append((з["файл"], д))
                лишити.add(і)
            порядок = 0
            for і, з in enumerate(зібрані):
                байти = з.pop("_байти")
                if і in лишити:
                    порядок += 1
                    з["порядок"] = порядок
                    if байти:
                        (фото / з["файл"]).write_bytes(байти)
                рядки.append(з)
    вихід = Path(__file__).with_name("галереї_%s.tsv" % а.ід)
    with open(вихід, "w", encoding="utf-8", newline="") as ф:
        пис = csv.DictWriter(ф, ПОЛЯ, delimiter="\t", lineterminator="\n")
        пис.writeheader()
        пис.writerows(рядки)
    у_галереї = [р for р in рядки if р["порядок"] != ""]
    print("речей %d; у галереях %d (кадр проби %d, гілка %d, крамниця завантажено %d, лише посилання %d); "
          "дублікатів пропущено %d; байтів %.1f МБ" % (
              len({р["номер"] for р in рядки}), len(у_галереї),
              sum(р["джерело"] == "кадр проби" for р in у_галереї),
              sum(р["джерело"].startswith("гілка") for р in у_галереї),
              sum(р["джерело"] == "крамниця, завантажено" for р in у_галереї),
              sum(р["джерело"] == "крамниця, посилання" for р in у_галереї),
              len(рядки) - len(у_галереї), sum(р["байтів"] or 0 for р in у_галереї) / 1e6))


if __name__ == "__main__":
    головна()

"""Повний канал «картка»: штатний транспорт і писач/читач голови #3747.

HTML і журнал зберігаються поза продуктом; повтор читає кеш без мережі.
"""
import argparse
import collections
import concurrent.futures
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
import threading
from urllib.parse import urlsplit

ГОЛОВА = "f03db4bbc2fb5a175f98ea373be4624421492cb9"
ВІДБИТОК = "463268ea374a2d61192f6aee87b2f7513111ff37fd73614b9aa5fd555c0e28cc"
ТЕКА = Path(__file__).resolve().parent


def зараз():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def читати(шлях):
    with gzip.open(шлях, "rt", encoding="utf-8") as потік:
        return [json.loads(рядок) for рядок in потік]


def зберегти(шлях, дані):
    шлях.parent.mkdir(parents=True, exist_ok=True)
    тимчасовий = шлях.with_suffix(шлях.suffix + ".tmp")
    with gzip.open(тимчасовий, "wt", encoding="utf-8") as потік:
        json.dump(дані, потік, ensure_ascii=False)
    тимчасовий.replace(шлях)


def причини(факти, ж):
    кольори = {str(в.get("колір")).strip().lower()
               for в in факти.get("варіанти") or [] if в.get("колір")}
    свотчі = {(с.get("назва") or с.get("hex") or с.get("фото") or "").strip().lower()
              for с in факти.get("свотчі") or []}
    відповідь = []
    if len(кольори) > 1:
        відповідь.append("кілька_кольорів_JSON_LD")
    if len(свотчі) > 1:
        відповідь.append("кілька_свотчів")
    if len(set(факти.get("кольори_вибору") or [])) > 1:
        відповідь.append("кілька_значень_вибору")
    if not факти.get("є_товар"):
        відповідь.append("нема_Product")
    if not (факти.get("id_магазину") or re.search(r"(\d{3,})/?$", факти["url"])):
        відповідь.append("нема_id")
    if not ж.чисті_фото(факти.get("фото"), факти["url"], факти.get("артикул")):
        відповідь.append("нема_кадрів")
    if not факти.get("колір_ld") and not any(len(м) == 1 for м in
            (кольори, свотчі, set(факти.get("кольори_вибору") or []))):
        відповідь.append("нема_свідчення_одного_кольору")
    return відповідь


def оцінити(старий, відповідь, ж, читач):
    url = старий["адреса"]
    факти = ж.факти_з_картки(відповідь["тіло"], url, ж.рецепт_селекторів(urlsplit(url).netloc))
    факти["url"] = url
    # Той самий писач, який викликає факти_з_картки; без домислів зі старого знімка.
    власник = ж._власник_сторінки(факти, url)
    канонічний = ж.канонічний_запис(факти, {"домен": urlsplit(url).netloc}, "картка")
    запис = dict(id=старий["ід"], url=url, фото=канонічний["фото"],
                 параметри=dict(id_магазину=канонічний.get("id_магазину"), власник_кадру=власник))
    докази = [читач.доказ_варіанта(запис, кадр) for кадр in запис["фото"]]
    відомий = bool(докази) and all(докази)
    чому = причини(факти, ж)
    if not відомий and not чому:
        чому = ["читач_відхилив_доказ"]
    return dict(стан="доведено" if відомий else "невідомо",
                причина=None if відомий else чому[0], причини=[] if відомий else чому,
                джерело=докази[0]["джерело"] if відомий else None,
                запис=запис, канонічний=канонічний, факти=факти, докази=докази)


def оцінити_окремо(старий, відповідь, дерево):
    """Розбір у трьох процесах не збільшує мережеву чергу чи темп запитів."""
    sys.path[:0] = [str(дерево / "zhnyvarka"), str(дерево / "джерела")]
    import жниварка as ж
    import фід_власник_кадру as читач
    return оцінити(старий, відповідь, ж, читач)


def підсумок(записи, результати, вихід):
    поля = ["крамниця", "записів", "оброблено", "доведено:картка:один_колір",
            "доведено:ricamare:сторінка", "невідомо:кілька_кольорів_JSON_LD",
            "невідомо:кілька_свотчів", "невідомо:кілька_значень_вибору", "невідомо:нема_Product",
            "невідомо:нема_id", "невідомо:нема_кадрів", "невідомо:нема_свідчення_одного_кольору",
            "невідомо:читач_відхилив_доказ", "без_відповіді", "збій_розбору", "не_виміряно", "статуси",
            "без_відповіді_статуси"]
    числові_поля = поля[1:-2]
    лічби = collections.defaultdict(collections.Counter)
    статуси = collections.defaultdict(collections.Counter)
    відмови = collections.defaultdict(collections.Counter)
    for з in записи:
        д = urlsplit(з["адреса"]).netloc
        лічби[д]["записів"] += 1
        р = результати.get(з["ід"])
        if р is None:
            лічби[д]["не_виміряно"] += 1
            continue
        лічби[д]["оброблено"] += 1
        стан = р["стан"]
        ключ = ("доведено:" + р["джерело"] if стан == "доведено" else
                "невідомо:" + р["причина"] if стан == "невідомо" else стан)
        if ключ not in поля:
            raise ValueError("Неназвана категорія: " + ключ)
        лічби[д][ключ] += 1
        статуси[д][str(р["код"])] += 1
        if стан == "без_відповіді":
            відмови[д][str(р["код"])] += 1
    рядки = []
    разом = collections.Counter()
    разом_статуси = collections.Counter()
    разом_відмови = collections.Counter()
    for д in sorted(лічби):
        л = лічби[д]
        assert sum(л[п] for п in числові_поля[2:]) == л["записів"]
        разом.update(л)
        разом_статуси.update(статуси[д])
        разом_відмови.update(відмови[д])
        рядки.append([д] + [str(л[п]) for п in числові_поля] +
                     [json.dumps(статуси[д], ensure_ascii=False, sort_keys=True),
                      json.dumps(відмови[д], ensure_ascii=False, sort_keys=True)])
    assert разом["записів"] == 13882
    рядки.append(["РАЗОМ"] + [str(разом[п]) for п in числові_поля] +
                 [json.dumps(разом_статуси, ensure_ascii=False, sort_keys=True),
                  json.dumps(разом_відмови, ensure_ascii=False, sort_keys=True)])
    вихід.mkdir(parents=True, exist_ok=True)
    тимчасова_лічба = вихід / "лічба.tsv.tmp"
    тимчасова_лічба.write_bytes(("\n".join("\t".join(р) for р in [поля] + рядки) + "\n").encode("utf-8"))
    тимчасова_лічба.replace(вихід / "лічба.tsv")
    тимчасові_результати = вихід / "результати.jsonl.gz.tmp"
    with gzip.open(тимчасові_результати, "wt", encoding="utf-8") as потік:
        for р in sorted(результати.values(), key=lambda р: р["ід"]):
            потік.write(json.dumps(р, ensure_ascii=False) + "\n")
    тимчасові_результати.replace(вихід / "результати.jsonl.gz")
    print(json.dumps(разом, ensure_ascii=False), flush=True)


def main():
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument("--дерево", type=Path, required=True)
    парсер.add_argument("--знімок", type=Path, required=True)
    парсер.add_argument("--сховище", type=Path, required=True)
    парсер.add_argument("--вихід", type=Path, default=ТЕКА)
    парсер.add_argument("--розвідка", action="store_true", help="перший запис кожної крамниці")
    парсер.add_argument("--без-мережі", action="store_true")
    парсер.add_argument("--системні-ca", dest="системні_сертифікати", action="store_true",
                        help="додати довірені CA Windows до certifi, з перевіркою TLS")
    а = парсер.parse_args()
    голова = subprocess.check_output(["git", "-C", str(а.дерево), "rev-parse", "HEAD"], text=True).strip()
    assert голова == ГОЛОВА, голова
    assert hashlib.sha256(а.знімок.read_bytes()).hexdigest() == ВІДБИТОК
    sys.path[:0] = [str(а.дерево / "zhnyvarka"), str(а.дерево / "джерела")]
    import жниварка as ж
    import фід_власник_кадру as читач
    assert ж._curl is not None and ж.ПАРСЕР_HTML == "lxml", "Потрібні curl_cffi та lxml"
    записи = [з for з in читати(а.знімок) if
              {п[0]: п[1] for п in з.get("параметри", [])}.get("канал") == "картка"]
    assert len(записи) == len({з["ід"] for з in записи}) == 13882
    черги = collections.defaultdict(list)
    for з in записи:
        черги[urlsplit(з["адреса"]).netloc].append(з)
    а.сховище.mkdir(parents=True, exist_ok=True)
    if а.системні_сертифікати:
        import requests
        сертифікати = ssl.create_default_context().get_ca_certs(binary_form=True)
        шлях_сертифікатів = а.сховище / "довірені_CA.pem"
        шлях_сертифікатів.write_text(Path(requests.certs.where()).read_text(encoding="ascii") + "\n" +
                          "".join(ssl.DER_cert_to_PEM_cert(с) for с in сертифікати), encoding="ascii")
        os.environ["REQUESTS_CA_BUNDLE"] = str(шлях_сертифікатів.resolve())
        os.environ["CURL_CA_BUNDLE"] = str(шлях_сертифікатів.resolve())
    результати = {}
    замок = threading.Lock()
    обчислення = concurrent.futures.ProcessPoolExecutor(max_workers=3)

    def одна(старий, транспорт):
        ід = старий["ід"]
        шлях = а.сховище / "відповіді" / (ід + ".json.gz")
        if шлях.exists():
            with gzip.open(шлях, "rt", encoding="utf-8") as потік:
                збережене = json.load(потік)
            assert збережене["адреса"] == старий["адреса"]
            відповідь = збережене["відповідь"]
        elif а.без_мережі:
            return
        else:
            відповідь = транспорт.get(старий["адреса"])
            збережене = dict(ід=ід, адреса=старий["адреса"], знято=зараз(), відповідь=відповідь)
            зберегти(шлях, збережене)
        результат = dict(ід=ід, адреса=старий["адреса"], знято=збережене["знято"],
                         код=відповідь["код"], кінцева_адреса=відповідь["url"],
                         помилка=відповідь.get("помилка"), причина_код=відповідь.get("причина_код"),
                         файл=str(шлях.resolve()), голова=ГОЛОВА)
        if відповідь["код"] != 200 or not відповідь.get("тіло") or відповідь.get("заслон"):
            результат.update(стан="без_відповіді")
        else:
            try:
                результат.update(обчислення.submit(оцінити_окремо, старий, відповідь, а.дерево.resolve()).result())
            except Exception as збій:
                результат.update(стан="збій_розбору", збій=type(збій).__name__ + ": " + str(збій))
        with замок:
            результати[ід] = результат
            if len(результати) % 100 == 0 or а.розвідка:
                print(зараз(), len(результати), старий["адреса"], результат["стан"], результат["код"], flush=True)

    def магазин(пара):
        домен, черга = пара
        транспорт = ж.Транспорт()
        шлях = а.сховище / "robots" / (домен + ".json.gz")
        if шлях.exists():
            with gzip.open(шлях, "rt", encoding="utf-8") as потік:
                р = json.load(потік)
        elif а.без_мережі:
            р = dict(код=0, тіло="")
        else:
            р = транспорт.get("https://" + домен + "/robots.txt")
            зберегти(шлях, р)
        транспорт.robots[домен] = ж.розібрати_robots(р["тіло"] if р["код"] == 200 else "")
        if а.розвідка:
            черга = черга[:1]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as пул:
            # Як у жниварки: пачка з трьох, пауза 0.8 с і robots у транспорті.
            for початок in range(0, len(черга), 3):
                for завдання in [пул.submit(одна, з, транспорт) for з in черга[початок:початок + 3]]:
                    завдання.result()
        print(зараз(), "КРАМНИЦЯ", домен, len(черга), dict(транспорт.статистика[домен]), flush=True)
        with замок:
            підсумок(записи, результати, а.вихід)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as пул:
        for завдання in [пул.submit(магазин, пара) for пара in sorted(черги.items(), key=lambda п: -len(п[1]))]:
            завдання.result()
    обчислення.shutdown(wait=True)
    підсумок(записи, результати, а.вихід)
    зберегти(а.сховище / "маніфест.json.gz", dict(голова=голова, знімок_sha256=ВІДБИТОК,
             знято=зараз(), розвідка=а.розвідка, записів=len(записи), оброблено=len(результати)))


if __name__ == "__main__":
    main()

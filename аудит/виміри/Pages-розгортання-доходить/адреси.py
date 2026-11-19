# -*- coding: utf-8 -*-
"""Мірило 2 наряду «Pages-розгортання-доходить»: сайт після перемикання віддає те саме (рядки дошки 16652–16654).

python3 аудит/виміри/Pages-розгортання-доходить/адреси.py [--sha КОМІТ] [--json вихід.json] [--до адреси-до.json]

Адреси — усе, що продукт і сторінки власника беруть із сайта: кожен файл сайта за `джерела/прилади/сайт_pages.py`
на коміті, який сайт віддає (`--sha`; без нього — з `pages_vidbytok.txt` на сайті, а нема — останнє успішне
розгортання `github-pages`), і теки з `index.html` (`/`, `ohliad-koloru/`); до них — зразки адрес, яких після
перемикання не буде (теки без `index.html`, сторінки, які Jekyll робив з `.md`, решта `аудит/` і `джерела/`).
Для кожної — код відповіді й розмір живого сайта зараз і що віддасть сайт з файлів дерева (`git ls-tree -l`):
200 і розмір файла — для адреси сайта, 404 — для решти. Розбіжність живого з деревом — рядок «≠». `--до` — JSON
попереднього запуску: тоді ще й адреси, чий код відповіді змінився між запусками.
Доказ, що зникле ніхто не бере: усі абсолютні адреси сайта в дереві коміту (`git grep`, крім `.gz`) — куди ведуть;
відносні адреси сторінок сайта входять у сайт за будовою (замикання посилань у `сайт_pages.py`).
Запуск — з кореня репозиторію, з комітом `--sha` у локальній історії (`git fetch --shallow-since=…` для глибокого).
"""
import argparse
import concurrent.futures
import gzip
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "джерела", "прилади"))
import сайт_pages  # noqa: E402

САЙТ = "https://mightyrochy.github.io/kod-shi-data/"
API = "https://api.github.com/repos/mightyrochy/kod-shi-data"
ЗРАЗКИ_ЗНИКАЮТЬ = [
    "zhnyvarka/", "open-source-stylist/", "README.html", "AGENTS.html", "AGENTS.md", "аудит/СТАН.md", "аудит/СТАН.html",
    "аудит/БЕКЛОГ.md", "джерела/показ.html", "показ.html",
]


def отримати(адреса):
    url = САЙТ + urllib.parse.quote(адреса, safe="/")
    for спроба in range(3):
        try:
            з = urllib.request.Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "vymir-pages"})
            with urllib.request.urlopen(з, timeout=120) as в:
                return в.status, len(в.read())
        except urllib.error.HTTPError as п:
            if п.code < 500 or спроба == 2:
                return п.code, len(п.read())
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if спроба == 2:
                return 0, 0
        time.sleep(2)


def sha_сайта():
    try:
        with urllib.request.urlopen(САЙТ + f"pages_vidbytok.txt?t={time.time_ns()}", timeout=30) as в:
            частини = в.read().decode().split()
            if len(частини) == 2:
                return частини[1], "pages_vidbytok.txt"
    except urllib.error.URLError:
        pass
    заголовки = {"User-Agent": "vymir-pages", "Accept": "application/vnd.github+json"}
    токен = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if токен:
        заголовки["Authorization"] = f"Bearer {токен}"
    with urllib.request.urlopen(urllib.request.Request(f"{API}/deployments?environment=github-pages&per_page=30",
                                                       headers=заголовки), timeout=60) as в:
        for д in json.load(в):
            with urllib.request.urlopen(urllib.request.Request(д["statuses_url"], headers=заголовки), timeout=60) as с:
                if any(ст["state"] == "success" for ст in json.load(с)):
                    return д["sha"], "останнє успішне розгортання github-pages"
    raise SystemExit("коміт сайта не знайдено")


def посилання(sha, сайт):
    """{адреса: (скільки разів у дереві, чи вона є на сайті з файлів дерева)} для абсолютних адрес сайта."""
    вираз = r"mightyrochy\.github\.io/kod-shi-data[^][:space:]()\"'`<>|*{}]*"
    сире = subprocess.run(["git", "grep", "-I", "-h", "-o", "-E", вираз, sha, "--", ":!*.gz"], capture_output=True,
                          check=False).stdout.decode("utf-8", "replace")
    лічба = {}
    for р in сире.splitlines():
        р = р.split(":", 1)[1] if р.startswith(sha) else р
        ад = urllib.parse.unquote(р.split("kod-shi-data", 1)[1]).split("#", 1)[0].split("?", 1)[0]
        ад = re.sub(r"(\.html):\d+(:\d+)?.*$", r"\1", ад).rstrip(".,;:\\").lstrip("/")
        лічба[ад] = лічба.get(ад, 0) + 1
    вихід = {}
    for ад, н in лічба.items():
        шлях = ад + "index.html" if ад == "" or ад.endswith("/") else ад
        вихід[ад] = (н, шлях in сайт or (шлях + "/index.html") in сайт)
    return вихід


def main():
    п = argparse.ArgumentParser()
    п.add_argument("--sha")
    п.add_argument("--json")
    п.add_argument("--до")
    а = п.parse_args()
    sha, звідки = (а.sha, "--sha") if а.sha else sha_сайта()
    одн = сайт_pages.одиниці(sha)
    сире = subprocess.run(["git", "ls-tree", "-r", "-l", "-z", "--full-tree", sha], capture_output=True,
                          check=True).stdout
    розмір = {}
    for з in сире.split(b"\0"):
        if з:
            мета, шлях = з.split(b"\t", 1)
            розмір[шлях.decode()] = int(мета.split()[3]) if мета.split()[3] != b"-" else 0
    сайт = sorted(ш for ш in розмір if сайт_pages.у_сайті(ш, одн))

    def дерево_дає(адреса):
        шлях = адреса + "index.html" if адреса == "" or адреса.endswith("/") else адреса
        return (200, розмір[шлях]) if шлях in сайт else (404, None)

    адреси = [("", "сайт"), ("ohliad-koloru/", "сайт")] + [(ш, "сайт") for ш in сайт] \
        + [(з, "зразок поза сайтом") for з in ЗРАЗКИ_ЗНИКАЮТЬ]
    with concurrent.futures.ThreadPoolExecutor(16) as пул:
        живі = list(пул.map(отримати, [ад for ад, _ in адреси]))
    рядки = []
    for (ад, вид), (код, байтів) in zip(адреси, живі):
        к2, б2 = дерево_дає(ад)
        рядки.append({"адреса": ад, "вид": вид, "живий_код": код, "живий_байтів": байтів, "дерево_код": к2,
                      "дерево_байтів": б2, "збіг": код == к2 and (б2 is None or байтів == б2)})
    звіт = {"сайт": САЙТ, "sha": sha, "звідки_sha": звідки, "виміряно": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "одиниці": одн, "адрес": len(рядки), "рядки": рядки}
    print(f"коміт {sha} ({звідки}); адрес {len(рядки)}: файлів сайта {len(сайт)} у {len(одн)} одиницях, "
          f"{sum(розмір[ш] for ш in сайт) / 1e6:.1f} МБ")
    лічба = {}
    for р in рядки:
        лічба[(р["вид"], р["живий_код"], р["дерево_код"])] = лічба.get((р["вид"], р["живий_код"], р["дерево_код"]), 0) + 1
    for (вид, к1, к2), н in sorted(лічба.items()):
        print(f"  {вид}: живий {к1} / дерево {к2} — {н}")
    for р in рядки:
        if not р["збіг"]:
            print(f"  ≠ {р['адреса'] or '/'}: живий {р['живий_код']} {р['живий_байтів']} Б, дерево {р['дерево_код']} "
                  f"{р['дерево_байтів']} Б ({р['вид']})")
    пос = посилання(sha, set(сайт))
    звіт["посилання_в_дереві"] = {ад: {"разів": н, "на_сайті_після": є} for ад, (н, є) in пос.items()}
    print(f"абсолютні адреси сайта в дереві {sha[:8]}: {len(пос)} різних, {sum(н for н, _ in пос.values())} разів")
    for ад, (н, є) in sorted(пос.items(), key=lambda х: -х[1][0]):
        print(f"  {'є' if є else 'НЕМА'} після перемикання: /{ад} — {н} разів")
    if а.до:
        with (gzip.open if а.до.endswith(".gz") else open)(а.до, "rt", encoding="utf-8") as ф:
            до = {р["адреса"]: р for р in json.load(ф)["рядки"]}
        змінені = [(р["адреса"], до[р["адреса"]]["живий_код"], р["живий_код"]) for р in рядки
                   if р["адреса"] in до and до[р["адреса"]]["живий_код"] != р["живий_код"]]
        print(f"код відповіді змінився проти {а.до}: {len(змінені)}")
        for ад, к1, к2 in змінені:
            print(f"  {ад or '/'}: {к1} → {к2}")
    if а.json:
        with open(а.json, "w", encoding="utf-8") as ф:
            json.dump(звіт, ф, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

"""HTTP-статуси всіх адрес `запис.фото` ПІСЛЯ у крамницях переліку (16118): збережені коди `кадри.tsv` (#3954), решта — запит
заголовків (HEAD, за 405 — GET без тіла) до самої крамниці; читання відкритих сторінок каталогу, не платний API.
Вихід: `статуси_404.tsv` (адреса, крамниця, код, джерело коду) і підсумок у stdout. Незміряне (мережева помилка) — не 404 й не 200.
"""
import argparse
import collections
import concurrent.futures
import csv
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from порівняти import КРАМНИЦІ_ПЕРЕЛІКУ, ПРОБИ, крамниця, читати  # noqa: E402

os.environ.pop("SSLKEYLOGFILE", None)
ЗАМОК = {к: threading.Semaphore(6) for к in КРАМНИЦІ_ПЕРЕЛІКУ}


def запит(адреса, к, контекст):
    for метод in ("HEAD", "GET"):
        з = urllib.request.Request(адреса, method=метод, headers={"User-Agent": "Mozilla/5.0 (kodshi-probe)", "Range": "bytes=0-0"} if метод == "GET" else {"User-Agent": "Mozilla/5.0 (kodshi-probe)"})
        for спроба in range(3):
            try:
                with ЗАМОК[к], urllib.request.urlopen(з, timeout=30, context=контекст) as в:
                    return в.status, ""
            except urllib.error.HTTPError as п:
                if п.code in (405, 403, 501) and метод == "HEAD":
                    break
                if п.code >= 500 and спроба < 2:
                    time.sleep(2); continue
                return п.code, ""
            except Exception as п:  # мережа: повтор, потім «незміряно»
                if спроба == 2:
                    if метод == "GET":
                        return 0, type(п).__name__
                    break
                time.sleep(2)
    return 0, "нема"


def main():
    п = argparse.ArgumentParser(description=__doc__)
    п.add_argument("--після", type=Path, required=True)
    п.add_argument("--вихід", type=Path, required=True)
    п.add_argument("--cafile")
    а = п.parse_args()
    після = читати(а.після)
    збережені = {}
    for р in csv.DictReader((ПРОБИ / "кадр_варіант_кв1_очима_1511/кадри.tsv").open(encoding="utf-8"), delimiter="\t"):
        збережені[р["адреса_кадру"]] = р["http_код"]
    адреси = {}
    усього = 0
    for х in після.values():
        к = крамниця(х)
        if к not in КРАМНИЦІ_ПЕРЕЛІКУ or х["стан"] == "без_відповіді" or "запис" not in х:
            continue
        for ад in х["запис"]["фото"]:
            усього += 1; адреси[ад] = к
    контекст = ssl.create_default_context(cafile=а.cafile)
    результат = {ад: (збережені[ад], "кадри.tsv") for ад in адреси if ад in збережені}
    решта = [ад for ад in адреси if ад not in результат]
    print(f"адрес у записах {усього}, унікальних {len(адреси)}, зі збереженим кодом {len(результат)}, до запиту {len(решта)}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(24) as пул:
        майбутні = {пул.submit(запит, ад, адреси[ад], контекст): ад for ад in решта}
        for н, м in enumerate(concurrent.futures.as_completed(майбутні), 1):
            код, прим = м.result()
            результат[майбутні[м]] = (str(код), "запит заголовків" + (f" ({прим})" if прим else ""))
            if н % 500 == 0:
                print(н, flush=True)
    з = collections.Counter(к for к, _ in результат.values())
    по_крамницях = collections.defaultdict(collections.Counter)
    for ад, (код, _) in результат.items():
        по_крамницях[адреси[ад]][код] += 1
    with (а.вихід / "статуси_404.tsv").open("w", encoding="utf-8", newline="") as ф:
        ф.write("адреса\tкрамниця\tкод\tджерело\n")
        for ад in sorted(результат):
            ф.write(f"{ад}\t{адреси[ад]}\t{результат[ад][0]}\t{результат[ад][1]}\n")
    print(json.dumps(dict(адрес_у_записах=усього, унікальних=len(адреси), коди=з, по_крамницях=по_крамницях), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

"""Рахує поточні записи Alot і явний брак HTML для рядка 6977; мережі немає."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

КОРІНЬ = Path(__file__).resolve().parents[2]


def main():
    """Друкує факти записів і рецепта без вигаданого покриття DOM."""
    файл = КОРІНЬ / "каталог_записи_v1.jsonl.gz"
    with gzip.open(файл, "rt", encoding="utf-8") as вхід:
        записи = [з for рядок in вхід if (з := json.loads(рядок)).get("схема") == "v1"
                  and urlparse(з.get("адреса", "")).hostname == "alot.com.ua"]
    with (КОРІНЬ / "zhnyvarka/рецепти.tsv").open(encoding="utf-8") as вхід:
        рецепт = next(р for р in csv.DictReader(вхід, delimiter="\t") if р["домен"] == "alot.com.ua")
    print("записи SHA256:", hashlib.sha256(файл.read_bytes()).hexdigest())
    print("Alot записів:", len(записи), "з описом:", sum(bool(з.get("опис")) for з in записи))
    print("селектор_опису:", repr(рецепт["селектор_опису"]))
    print("HTML у цій пробі: 0; DOM покриття: НЕ ВИМІРЯНО; історичні 341→278 не відтворено")
    for з in записи[:2]:
        print("потрібен HTML URL/date/SHA256:", з["ід"], з["адреса"])


if __name__ == "__main__":
    main()

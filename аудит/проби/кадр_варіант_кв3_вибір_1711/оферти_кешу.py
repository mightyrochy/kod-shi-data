"""Лічить поля всіх шаблонів оферт bella-bicchi на тому самому кеші HTML."""
import argparse
import collections
import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup


def main():
    """Читає всі 340 сторінок каналу, не обмежуючись вибіркою очима."""
    п = argparse.ArgumentParser(description=__doc__)
    п.add_argument("--результати", type=Path, required=True)
    п.add_argument("--сховище", type=Path, required=True)
    а = п.parse_args()
    з = [json.loads(р) for р in gzip.open(а.результати, "rt", encoding="utf-8")]
    з = [р for р in з if urlsplit(р["адреса"]).netloc == "bella-bicchi.com"]
    поля, оферт = collections.Counter(), 0
    for р in з:
        відповідь = json.load(gzip.open(а.сховище / "відповіді" / (р["ід"] + ".json.gz"), "rt", encoding="utf-8"))
        for шаблон in BeautifulSoup(відповідь["відповідь"]["тіло"], "lxml").select("template.offers-template-json"):
            for оферта in json.loads(шаблон.string or шаблон.get_text()):
                оферт += 1
                поля.update(оферта.keys())
    print(json.dumps(dict(сторінок=len(з), оферт=оферт, поля=dict(поля)), ensure_ascii=False))


if __name__ == "__main__":
    main()

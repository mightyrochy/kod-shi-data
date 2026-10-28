"""Власний вимір перевірки #2069: справжні жнива, керований HTTP, тимчасові журнали.

Запуск: python <цей файл> <дерево коду>. Не використовує вимір виконавця.
"""
import asyncio
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

КОРІНЬ = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(КОРІНЬ / "zhnyvarka"))
import виконавець as в
import обхід as о
import json_прохід as п
from журнал_карток import прочитати


def річ(номер):
    return dict(id=номер, handle=f"p{номер}", permalink=f"https://check.test/p{номер}",
                name=f"Чорна сукня {номер}", title=f"Чорна сукня {номер}",
                images=[dict(src=f"https://check.test/{номер}.jpg")],
                variants=[dict(option1="M", available=True)],
                attributes=[dict(name="Розмір", terms=[dict(name="M")])])


class Стенд:
    def __init__(self, журнал, сімейство):
        self.дім = Path(журнал)
        self.сім = сімейство
        self.рецепт = dict(домен="check.test", сімейство=сімейство, транспорт="http",
                            старт="https://check.test", пошук=("/products.json?page={n}" if
                            сімейство == "shopify" else "/wp-json/wc/store/products?page={n}"))
        self.файл = self.дім / "сирі/check.test.jsonl"
        self.стан = self.дім / "проходи/check.test/json_стан.json"

    def прогін(self, сторінки, стеля=300, через_обхід=False, обрив=False):
        запити = []
        async def get(контекст, url, **kwargs):
            n = int(parse_qs(urlparse(url).query)["page"][0])
            запити.append(n)
            if n not in сторінки:
                raise RuntimeError(f"Зайвий HTTP сторінки {n}")
            дані = сторінки[n]
            return 200, json.dumps({"products": дані} if self.сім == "shopify" else дані)
        а = SimpleNamespace(журнал=str(self.дім), стеля=стеля, секунд_на_магазин=30,
                            без_огляду=True, оновити_перелік=False, пауза=0)
        збирач = в.Виконавець(а)
        оригінал = збирач._пиши
        лічба = 0
        def пиши(*args):
            nonlocal лічба
            оригінал(*args)
            лічба += 1
            if обрив and лічба == 1:
                raise RuntimeError("Проба: обрив після першого збереженого запису")
        def запуск(*args):
            with patch.object(збирач, "_get", get), patch.object(збирач, "_пиши", пиши):
                asyncio.run(збирач._магазин(AsyncMock(), self.рецепт, asyncio.Semaphore(1)))
            return {"check.test": (0, False)}
        if через_обхід:
            with patch.object(о, "запустити_крамниці", запуск):
                о.main(["--журнал", str(self.дім), "--магазини", "check.test", "--циклів", "1"])
        else:
            запуск()
        return запити

    def факти(self):
        записи, битий = прочитати(self.файл)
        стан = json.loads(self.стан.read_bytes())
        дані = self.файл.read_bytes() if self.файл.exists() else b""
        return dict(адреси=sorted({з["url"] for з in записи}), записів=len(записи),
                    пошкоджено=битий, кінець=стан["завершено"],
                    сума_збігається=стан.get("журнал_sha256") == hashlib.sha256(дані).hexdigest())


def main():
    провали = []
    лічба = 0
    for сім in ("woo", "shopify"):
        for випадок in ("новий товар", "очищено", "обрізано цілим рядком", "пошкоджено середній рядок",
                        "журналу нема", "старий кінець без суми", "товар зник", "два обходи",
                        "обрив усередині сторінки", "позиція другої сторінки і втрата журналу"):
            with tempfile.TemporaryDirectory(prefix="review-2069-") as дім:
                с = Стенд(дім, сім)
                початок = {1: [річ(1), річ(2)], 2: [річ(3)], 3: []}
                if випадок.startswith("позиція"):
                    початок = {1: [річ(1)], 2: [річ(2), річ(3)], 3: []}
                с.прогін(початок, стеля=2 if випадок.startswith("позиція") else 300,
                         обрив=випадок.startswith("обрив"))
                if випадок == "очищено" or випадок.startswith("позиція"):
                    с.файл.write_bytes(b"")
                elif випадок == "обрізано цілим рядком":
                    с.файл.write_bytes(с.файл.read_bytes().splitlines(keepends=True)[0])
                elif випадок == "пошкоджено середній рядок":
                    рядки = с.файл.read_bytes().splitlines(keepends=True)
                    рядки[1] = рядки[1][:len(рядки[1]) // 2] + b"\n"
                    с.файл.write_bytes(b"".join(рядки))
                elif випадок == "журналу нема":
                    с.файл.unlink()
                elif випадок == "старий кінець без суми":
                    стан = json.loads(с.стан.read_bytes())
                    стан.pop("журнал_sha256", None)
                    с.стан.write_text(json.dumps(стан), encoding="utf-8")
                    for ф in с.стан.parent.joinpath("json_сторінки").glob("*.json"):
                        ф.unlink()
                сторінки = початок
                if випадок == "новий товар":
                    сторінки = {1: [річ(1), річ(2)], 2: [річ(3), річ(4)], 3: []}
                elif випадок == "товар зник":
                    сторінки = {1: [річ(1)], 2: []}
                запити = с.прогін(сторінки, через_обхід=випадок == "два обходи")
                факти = с.факти()
                очікувано = 4 if випадок == "новий товар" else 3
                добре = len(факти["адреси"]) == очікувано and факти["кінець"] and факти["сума_збігається"]
                if випадок == "новий товар":
                    добре &= запити == [1, 2, 3]
                elif випадок == "старий кінець без суми":
                    добре &= запити == [1, 2, 3]
                elif випадок == "товар зник":
                    добре &= запити == [1, 2] and факти["записів"] == 3
                elif випадок.startswith("позиція"):
                    добре &= запити == [3]
                elif випадок.startswith("обрив"):
                    добре &= запити == [2, 3]
                else:
                    добре &= запити == []
                if випадок == "два обходи":
                    повтор = с.прогін({}, через_обхід=True)
                    добре &= повтор == []
                    факти["HTTP_другого"] = повтор
                лічба += 1
                if not добре:
                    провали.append(f"{сім}/{випадок}")
                print(json.dumps(dict(сімейство=сім, випадок=випадок, HTTP=запити,
                                      **факти, мірило=bool(добре)), ensure_ascii=False), flush=True)
    print(json.dumps(dict(випадків=лічба, пройдено=лічба-len(провали), провали=провали), ensure_ascii=False))
    return int(bool(провали))


if __name__ == "__main__":
    raise SystemExit(main())

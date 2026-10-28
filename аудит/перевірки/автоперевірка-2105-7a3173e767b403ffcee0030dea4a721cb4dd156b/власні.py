"""Власна проба меж читання зведення та відновлення JSONL, без зовнішньої мережі."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "zhnyvarka"))
import обхід
import виконавець
from журнал_карток import прочитати


def зведення():
    """Перевіряє обох споживачів того самого обірваного UTF-8 без підміни читача."""
    збоїв = 0
    with tempfile.TemporaryDirectory(prefix="review-2105-summary-") as тека:
        файл = Path(тека) / "зведення_жнив.tsv"
        файл.write_bytes(("\t".join(обхід.ШАПКА_ЗВЕДЕННЯ) + "\n2026-10-28\tbroken.test\tСукня").encode()[:-1])
        for спроба in (1, 2):
            with patch.object(обхід, "запустити_крамниці") as запуск:
                try:
                    обхід.main(["--журнал", тека, "--магазини", "broken.test,healthy.test", "--циклів", "1"])
                except UnicodeDecodeError as помилка:
                    assert запуск.call_count == 0
                    збоїв += 1
                    print(f"main/{спроба}: {type(помилка).__name__}, запусків={запуск.call_count}")
                else:
                    raise AssertionError("Відтворення відомої вади змінилося")
        try:
            обхід.останні_рядки(файл, 0)
        except UnicodeDecodeError as помилка:
            збоїв += 1
            print(f"останні_рядки: {type(помилка).__name__}")
        else:
            raise AssertionError("Другий читач більше не відтворює ваду")
    print(f"Зведення: {збоїв}/3 підтверджених збоїв, один механізм рядка 10661")


def json_відновлення(сімейство):
    """Зіставляє нові жнива, обрізання посеред UTF-8 та повторне продовження без HTTP."""
    with tempfile.TemporaryDirectory(prefix="review-2105-json-") as тека:
        рецепт = dict(домен="own.test", старт="https://own.test", транспорт="http", сімейство=сімейство,
                      пошук="/products.json?page={n}" if сімейство == "shopify" else "/wp-json/wc/store/products?page={n}")
        файл = Path(тека) / "сирі/own.test.jsonl"
        стан_файл = Path(тека) / "проходи/own.test/json_стан.json"
        def прогін(кількість, через_обхід=False):
            """Виконує справжні магазин, парсер, запис і checkpoint; підміняє лише транспорт."""
            запити = []
            збирач = виконавець.Виконавець(SimpleNamespace(журнал=тека, стеля=300, секунд_на_магазин=10,
                                                        без_огляду=True, оновити_перелік=False))
            async def get(контекст, адреса, **kw):
                """Повертає керовану сторінку API та рахує фактичні HTTP-виклики."""
                номер = int(parse_qs(urlparse(адреса).query)["page"][0])
                запити.append(номер)
                речі = [dict(id=i, handle=f"p{i}", permalink=f"https://own.test/p{i}", name=f"Чорна сукня {i}",
                              title=f"Чорна сукня {i}", images=[dict(src="https://own.test/image.jpg")],
                              variants=[dict(option1="M", available=True)], attributes=[dict(name="Розмір", terms=[dict(name="M")])])
                        for i in range(1, кількість + 1)] if номер == 1 else []
                return 200, json.dumps(dict(products=речі) if сімейство == "shopify" else речі)
            def запуск(*args):
                """Виконує справжній магазин замість створення дочірнього процесу."""
                with patch.object(збирач, "_get", get):
                    asyncio.run(збирач._магазин(AsyncMock(), рецепт, asyncio.Semaphore(1)))
                return {"own.test": (0, False)}
            if через_обхід:
                with patch.object(обхід, "запустити_крамниці", запуск):
                    обхід.main(["--журнал", тека, "--магазини", "own.test", "--циклів", "1"])
            else:
                запуск()
            return запити
        assert прогін(2) == [1, 2]
        assert прогін(3) == [1, 2]
        рядки = файл.read_bytes().splitlines(keepends=True)
        місце = рядки[-1].index("сукня".encode()) + 1
        файл.write_bytes(b"".join(рядки[:-1]) + рядки[-1][:місце])
        assert прогін(3, True) == []
        записи, пошкоджено = прочитати(файл)
        шлях = "products/" if сімейство == "shopify" else ""
        assert {з["url"] for з in записи} == {f"https://own.test/{шлях}p{i}" for i in (1, 2, 3)}
        стан = json.loads(стан_файл.read_bytes())
        assert стан["завершено"] and стан["журнал_sha256"] == hashlib.sha256(файл.read_bytes()).hexdigest()
        assert прогін(3, True) == []
        print(f"{сімейство}: новий товар 2→3, обірваний UTF-8 відновлено 3/3, пошкодження={пошкоджено}, HTTP відбудови/повтору=[]/[]")


if __name__ == "__main__":
    зведення()
    for сімейство in ("woo", "shopify"):
        json_відновлення(сімейство)
    print("Власні проби: очікувані результати підтверджено; P1 залишається")

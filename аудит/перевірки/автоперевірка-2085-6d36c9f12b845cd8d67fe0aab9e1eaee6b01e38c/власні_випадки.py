"""Власні випадки: обриви на межах стійких записів і втрата JSONL посередині."""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "zhnyvarka"))
import виконавець
import json_прохід
import обхід
from журнал_карток import прочитати


class Обрив(BaseException):
    """Імітує зупинку поза обробниками помилок крамниці."""


def магазин(журнал, сім, точка="", через_обхід=False):
    """Виконує справжній магазин, замінюючи HTTP і необов'язково межу одного запису."""
    рецепт = dict(домен="review.test", сімейство=сім, транспорт="http", старт="https://review.test",
                  пошук="/products.json?page={n}" if сім == "shopify" else "/wp-json/wc/store/products?page={n}")
    збирач = виконавець.Виконавець(SimpleNamespace(журнал=журнал, стеля=300,
                   секунд_на_магазин=30, без_огляду=True))
    запити = []
    async def http(_контекст, url, **_параметри):
        """Віддає шість речей трьома сторінками; четверта порожня."""
        n = int(url.rsplit("=", 1)[1])
        запити.append(n)
        речі = [dict(id=i, handle=f"p{i}", permalink=f"https://review.test/p{i}", name="Чорна сукня",
                     title="Чорна сукня", images=[dict(src="https://review.test/photo.jpg")],
                     variants=[dict(option1="M", available=True)],
                     attributes=[dict(name="Розмір", terms=[dict(name="M")])])
                for i in range((n - 1) * 2 + 1, min(n * 2 + 1, 7))]
        return 200, json.dumps({"products": речі} if сім == "shopify" else речі)

    записати = json_прохід.записати
    пиши = збирач._пиши
    def запис(файл, дані):
        """Зупиняє виконання до або після заданого атомарного запису."""
        назва = "кеш" if файл.name == "1.json" else ""
        if файл.name == "json_стан.json":
            if дані["завершено"]:
                назва = "кінець"
            elif дані["сторінка"] == 2:
                назва = "позиція"
        if назва and точка == назва + "-до":
            raise Обрив()
        записати(файл, дані)
        if назва and точка == назва + "-після":
            raise Обрив()

    def картка(шлях, дані):
        """Зупиняє після fsync першої картки, до оновлення позиції."""
        пиши(шлях, дані)
        if точка == "картка-після":
            raise Обрив()

    def запустити(*_аргументи):
        """Зберігає справжній шлях до зведення й стану, замінюючи запуск підпроцесу."""
        asyncio.run(збирач._магазин(AsyncMock(), рецепт, asyncio.Semaphore(1)))
        return {"review.test": (0, False)}

    with patch.object(збирач, "_get", side_effect=http), patch.object(збирач, "_пиши", side_effect=картка), \
            patch.object(json_прохід, "записати", side_effect=запис):
        if через_обхід:
            with patch.object(обхід, "запустити_крамниці", side_effect=запустити):
                обхід.main(["--журнал", журнал, "--магазини", "review.test", "--циклів", "1"])
        else:
            запустити()
    return запити


def main():
    """Друкує відновлені адреси, зайвий HTTP та підтвердження кінця для кожного випадку."""
    успішних = 0
    for сім in ("woo", "shopify"):
        for точка in ("кеш-до", "кеш-після", "картка-після", "позиція-до", "позиція-після", "кінець-до", "кінець-після",
                      "втрачено-перший", "втрачено-середній", "UTF8-середина", "UTF8-хвіст", "старий-без-суми"):
            with tempfile.TemporaryDirectory(prefix="review-2085-edge-") as ж:
                if точка.startswith(("втрачено-", "UTF8-", "старий-")):
                    магазин(ж, сім)
                    файл = Path(ж) / "сирі/review.test.jsonl"
                    рядки = файл.read_bytes().splitlines(keepends=True)
                    if точка == "втрачено-перший":
                        del рядки[0]
                    elif точка == "втрачено-середній":
                        del рядки[2]
                    elif точка == "UTF8-середина":
                        рядки[2] = b'\xd0\n'
                    elif точка == "UTF8-хвіст":
                        рядки.append(b'\xd0')
                    else:
                        стан = json_прохід.прочитати_стан(ж, "review.test")
                        del стан["журнал_sha256"]
                        json_прохід.записати(Path(ж) / "проходи/review.test/json_стан.json", стан)
                    файл.write_bytes(b"".join(рядки))
                    оч = []
                else:
                    try:
                        магазин(ж, сім, точка)
                    except Обрив:
                        pass
                    else:
                        raise AssertionError("Обрив не відбувся: " + точка)
                    оч = [1, 2, 3, 4] if точка == "кеш-до" else [2, 3, 4] if точка in (
                        "кеш-після", "картка-після", "позиція-до", "позиція-після") else []
                запити = магазин(ж, сім, через_обхід=True)
                записи, пошкоджено = прочитати(Path(ж) / "сирі/review.test.jsonl")
                адреси = {з["url"] for з in записи}
                стан = обхід.прочитати_стан(ж)["review.test"]
                добре = (запити == оч and len(адреси) == 6 and стан["готово"] == 6 and стан["лишилось"] == 0
                          and стан["стан_код"] == "CATALOG" and json_прохід.завершено(ж, "review.test"))
                if пошкоджено:
                    добре &= стан["причина_код"] == "JOURNAL_CORRUPT"
                print(f"{сім}/{точка}: HTTP={запити}/{оч}, адрес={len(адреси)}/6, готово={стан['готово']}, "
                      f"залишок={стан['лишилось']}, причина={стан['причина_код']}, добре={добре}", flush=True)
                assert добре
                успішних += 1
    print(f"Власні випадки: {успішних}/24", flush=True)


if __name__ == "__main__":
    main()

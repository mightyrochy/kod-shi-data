"""Прямий запуск JSON-жнив із керованим HTTP; необов'язковий аргумент — дерево коду ДО."""
import asyncio, hashlib, json, sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str((Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]) / "zhnyvarka"))
import виконавець
from json_прохід import прочитати_стан
from журнал_карток import прочитати


def жнива(журнал, сім, кількість, стеля=300, пачка=None):
    """Виконує магазин із незмінним рецептом; API віддає всі речі на першій сторінці."""
    рецепт = dict(домен="json.test", сімейство=сім, транспорт="http", старт="https://json.test",
                  пошук="/products.json?page={n}" if сім == "shopify" else "/wp-json/wc/store/products?page={n}")
    а = SimpleNamespace(журнал=журнал, стеля=стеля, секунд_на_магазин=30, без_огляду=True)
    збирач = виконавець.Виконавець(а)
    async def відповідь(контекст, адреса, **параметри):
        """Формує справжню структуру API та фіксує номери HTTP-запитів."""
        n = int(адреса.rsplit("=", 1)[1]); запити.append(n)
        речі = [dict(id=i, handle=f"p{i}", permalink=f"https://json.test/p{i}", name="Чорна сукня",
                     title="Чорна сукня", images=[dict(src="https://json.test/photo.jpg")],
                     variants=[dict(option1="M", available=True)],
                     attributes=[dict(name="Розмір", terms=[dict(name="M")])])
                for i in range(1, кількість + 1)]
        розмір = пачка or кількість or 1
        речі = речі[(n - 1) * розмір:n * розмір]
        return 200, json.dumps({"products": речі} if сім == "shopify" else речі)
    запити = []
    with patch.object(збирач, "_get", side_effect=відповідь):
        asyncio.run(збирач._магазин(AsyncMock(), рецепт, asyncio.Semaphore(1)))
    файл = Path(журнал) / "сирі/json.test.jsonl"
    стан = прочитати_стан(журнал, "json.test")
    return запити, len({з["url"] for з in прочитати(файл)[0]}), стан.get("журнал_sha256") == hashlib.sha256(файл.read_bytes()).hexdigest()

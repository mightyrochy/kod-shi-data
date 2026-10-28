"""Заглушка HTTP для справжніх жнив JSON-сімейства та повтору обходу без мережі."""
import asyncio, csv, json, sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід, виконавець

def прогін(журнал, сімейство, відповіді, стеля=300):
    """Виконує справжній шлях магазин → JSON → зведення → стан, замінюючи лише процес і HTTP."""
    рецепт = dict(домен="json.test", сімейство=сімейство, транспорт="http", старт="https://json.test",
                  пошук="/products.json?page={n}" if сімейство == "shopify" else "/wp-json/wc/store/products?page={n}")
    а = SimpleNamespace(журнал=журнал, стеля=стеля, секунд_на_магазин=30, без_огляду=True)
    збирач = виконавець.Виконавець(а)
    запити = AsyncMock(side_effect=відповіді)
    браузер = AsyncMock()
    def запустити(*арг):
        """Заміщує межу процесу, залишаючи справжні жнива й журнал."""
        with patch.object(збирач, "_get", запити):
            asyncio.run(збирач._магазин(браузер, рецепт, asyncio.Semaphore(1)))
        return {"json.test": (0, False)}
    with patch.object(обхід, "запустити_крамниці", запустити):
        обхід.main(["--журнал", журнал, "--магазини", "json.test", "--циклів", "1"])
    with open(Path(журнал) / "обхід_стан.tsv", encoding="utf-8") as ф:
        стан = next(csv.DictReader(ф, delimiter="\t"))
    return стан, запити.await_count

def порція(сімейство, речі):
    """Кодує очікувану структуру сторінки кожного API."""
    return 200, json.dumps({"products": речі} if сімейство == "shopify" else речі)

РІЧ = dict(id=1, handle="suknia", permalink="https://json.test/suknia", name="Сукня", title="Сукня")

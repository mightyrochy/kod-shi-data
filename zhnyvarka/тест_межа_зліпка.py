import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

import виконавець


class ПередаванняМежі(unittest.TestCase):
    def test_селектор_рецепта_надходить_до_зліпка(self):
        сторінка = Mock()
        сторінка.goto = AsyncMock(return_value=Mock(status=200))
        сторінка.wait_for_load_state = AsyncMock()
        сторінка.content = AsyncMock(return_value="x" * 1500)
        сторінка.evaluate = AsyncMock(side_effect=ValueError("зупинка після зліпка"))
        вик = object.__new__(виконавець.Виконавець)
        вик.проходи = {}
        вик._пиши = Mock()
        журнал = {"відкрито": 0, "збій": 0}
        asyncio.run(вик._картка(сторінка, {"домен": "shop", "селектор_блоку": ".product"}, журнал, "", "https://shop/product"))
        сторінка.evaluate.assert_awaited_once_with(виконавець.ЗЛІПОК_DOM, ".product")


if __name__ == "__main__":
    unittest.main()

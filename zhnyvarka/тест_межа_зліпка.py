import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

import виконавець
import жниварка
from playwright.sync_api import sync_playwright


class ПередаванняМежі(unittest.TestCase):
    def test_h1_не_читається_без_межі_товару(self):
        html = '<html><body><h1>Чужа назва товару</h1><div class="product">Інша річ</div></body></html>'
        факти = жниварка.факти_з_картки(html, 'https://shop.test/product/1', {'блок': '.product'})
        self.assertFalse(факти['назва'])
        self.assertIsNone(факти['сирий']['h1'])

    def test_body_і_html_не_є_межею(self):
        суп = жниварка.BeautifulSoup('<html><body><h1>Назва</h1></body></html>', 'html.parser')
        for селектор in ('body', 'html'):
            with self.subTest(селектор=селектор):
                блок, _ = жниварка.вузол_товару(суп, суп.h1, {'блок': селектор})
                self.assertIsNone(блок)

    def test_зліпок_читає_лише_блок_рецепта(self):
        with sync_playwright() as p:
            браузер = p.chromium.launch(headless=True)
            сторінка = браузер.new_page()
            сторінка.set_content('''<div class="product"><h1>Своя назва</h1>
                <p>Матеріал: льон</p></div><div><p>Чужий опис</p></div>''')
            dom = сторінка.evaluate(виконавець.ЗЛІПОК_DOM, '.product')
            без_межі = сторінка.evaluate(виконавець.ЗЛІПОК_DOM, '.missing')
            браузер.close()
        self.assertEqual(dom['h1'], 'Своя назва')
        self.assertIn('Матеріал: льон', dom['text'])
        self.assertNotIn('Чужий опис', dom['text'])
        self.assertIn(['Матеріал', 'льон'], dom['rows'])
        self.assertEqual(без_межі['text'], '')
        self.assertEqual(без_межі['h1'], '')
        self.assertEqual(без_межі['rows'], [])

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

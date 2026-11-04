import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

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
        сторінка.evaluate.assert_awaited_once_with(виконавець.ЗЛІПОК_DOM, {"блок": ".product"})

    def test_метадані_не_підміняють_текст_товару(self):
        """Звіряє обидва збирачі на суперечливих полях DOM і метаданих."""
        html = '''<title>Чужа вкладка</title><meta property="og:title" content="Чуже оголошення">
            <meta property="og:description" content="Чужий метаопис">
            <script type="application/ld+json">{"@type":"Product","name":"Чужий JSON",
              "description":"Чужий опис JSON", "brand":{"name":"Чужий бренд"},
              "sku":123, "material":"Чужа тканина", "offers":{"price":2500,"priceCurrency":"UAH"}}</script>
            <div class="product" itemscope itemtype="https://schema.org/Product">
              <h1>Своя назва</h1><div itemprop="description">Свій опис</div>
              <span class="sku">СВ-1</span><span itemprop="brand">Свій бренд</span></div>
            <div><h1>Сусідня назва</h1><div itemprop="description">Сусідній опис</div></div>'''
        факти = жниварка.факти_з_картки(html, 'https://shop.test/product/1', {})
        картка = виконавець.картка_з_dom('https://shop.test/product/1', html, {})
        for запис in (факти, картка):
            self.assertEqual(запис['назва'], 'Своя назва')
            self.assertEqual(запис['опис'], 'Свій опис')
            self.assertEqual(запис['бренд'], 'Свій бренд')
            self.assertEqual(запис['артикул'], 'СВ-1')
        self.assertEqual(факти['ціна'], 2500)
        self.assertNotIn('склад', факти['характеристики'])
        без_опису = html.replace('<div itemprop="description">Свій опис</div>', '')
        self.assertIsNone(жниварка.факти_з_картки(без_опису, 'https://shop.test/product/1', {})['опис'])
        self.assertEqual(виконавець.картка_з_dom('https://shop.test/product/1', без_опису, {})['опис'], '')

    def test_назва_не_h1_і_портальний_опис(self):
        """Перевіряє рецепт із заголовком у h4 і описом у сусідньому порталі."""
        html = '''<h1>Рубрика</h1><div class="wrapper">
            <section id="product"><h4 class="name">Своя річ</h4><p>Матеріал: льон</p></section>
            <section id="description"><p>Свій опис у порталі</p></section>
            <section class="other"><p>Чужий опис</p><p>Матеріал: чужий</p></section></div>'''
        рецепт = {'блок': '.wrapper', 'назва': 'h4.name', 'опис': '#description',
                  'виключити': ':scope > :not(#product):not(#description)'}
        with patch.object(жниварка, 'рецепт_селекторів', return_value=рецепт):
            факти = жниварка.факти_з_картки(html, 'https://shop.test/product/1')
            картка = виконавець.картка_з_dom('https://shop.test/product/1', html, {})
        self.assertEqual(факти['назва'], 'Своя річ')
        self.assertEqual(картка['опис'], 'Свій опис у порталі')
        with sync_playwright() as p:
            браузер = p.chromium.launch(headless=True)
            сторінка = браузер.new_page()
            сторінка.set_content(html)
            dom = сторінка.evaluate(виконавець.ЗЛІПОК_DOM, рецепт)
            браузер.close()
        self.assertEqual(dom['h1'], 'Своя річ')
        self.assertIn('Свій опис у порталі', dom['text'])
        self.assertNotIn('Чужий', dom['text'])
        self.assertNotIn(['Матеріал', 'чужий'], dom['rows'])

    def test_заголовок_рубрики_не_заважає_товару(self):
        """Читає власний h1 товару після окремого заголовка рубрики."""
        html = '<h1>Каталог</h1><article class="product"><h1>Своя річ</h1></article>'
        факти = жниварка.факти_з_картки(html, 'https://shop.test/product/1', {'блок': '.product'})
        self.assertEqual(факти['назва'], 'Своя річ')

    def test_неоднозначний_селектор_не_обирає_сусіда(self):
        """Лишає поле порожнім, коли рецепт назвав два різні товари."""
        html = '<article class="product"><h1>Перша</h1></article><article class="product"><h1>Друга</h1></article>'
        факти = жниварка.факти_з_картки(html, 'https://shop.test/product/1', {'блок': '.product'})
        self.assertIsNone(факти['назва'])
        self.assertEqual(факти['межа_блоку'], 'неоднозначна_межа_блоку')

    def test_вкладені_межі_та_рекомендації_браузера(self):
        """Обирає вужчу вкладену межу й вилучає рекомендації до читання тексту."""
        html = '''<h1>Каталог</h1><article class="product"><p>Зовнішній текст</p>
            <section class="product"><header><h1>Своя річ</h1></header><p>Свій опис</p>
            <aside class="related"><p>Матеріал: чужий</p></aside></section></article>'''
        with sync_playwright() as p:
            браузер = p.chromium.launch(headless=True)
            сторінка = браузер.new_page()
            сторінка.set_content(html)
            dom = сторінка.evaluate(виконавець.ЗЛІПОК_DOM, '.product')
            браузер.close()
        self.assertEqual(dom['h1'], 'Своя річ')
        self.assertIn('Свій опис', dom['text'])
        self.assertNotIn('Зовнішній текст', dom['text'])
        self.assertNotIn('чужий', dom['text'])

    def test_сирий_текст_зліпка_не_дає_складу_й_ціни(self):
        """Бере склад і ціну з фактів власного блоку, попри чужий сирий текст."""
        html = '''<div itemscope itemtype="https://schema.org/Product">
            <p>Чужа пропозиція: 500 грн, 80% поліестер</p>
            <section class="own"><h1>Своя річ</h1><p><strong>Склад:</strong> 100% льон</p>
            <span itemprop="price" content="2500">2500 грн</span></section></div>'''
        with patch.object(жниварка, 'рецепт_селекторів', return_value={'блок': '.own'}):
            картка = виконавець.картка_з_dom('https://shop.test/product/1', html,
                                          {'text': 'Чужа пропозиція: 500 грн, 80% поліестер'})
        self.assertEqual(картка['склад'], ['100% льон'])
        self.assertEqual(картка['ціна'], '2500.0 UAH')


if __name__ == "__main__":
    unittest.main()

"""Перевіряє походження на штучному дереві й поточних жнивах; запуск із будь-якої теки."""
import ast
from contextlib import contextmanager
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from корінь_річ_запис_речі import BeautifulSoup, Прогін, підсумувати, звичайні, ЧАСТИНА, ШМАТОК
from річ_запис_походження import HTML, Спостерігач, Позначки, походження

КОРІНЬ = Path(__file__).resolve().parents[2]
ШТУЧНЕ_ДЕРЕВО = Path(__file__).resolve().parent / 'річ_запис_дані/стенд_жнив'

СТОРІНКА = '''<html><head><title>Заголовок вкладки</title></head><body>
<article id="товар"><h1>Лляна сорочка</h1><p>Власний опис</p></article>
<footer>Сторонній опис</footer></body></html>'''


def виконати(код, тіло=СТОРІНКА):
    """Виконує довільний синтетичний читач з тією самою механікою позначок."""
    сп = Спостерігач(lambda с: с.select_one('#товар'))
    простір = dict(__походження__=сп, BeautifulSoup=BeautifulSoup, HTML=HTML, re=re, json=json, тіло=HTML(тіло))
    дерево = Позначки('синтетичний.py').visit(ast.parse(код))
    exec(compile(ast.fix_missing_locations(дерево), 'синтетичний.py', 'exec'), простір)
    return підсумувати(простір['запис'], сп.читання), простір['запис']


@contextmanager
def жнива(корінь=ШТУЧНЕ_ДЕРЕВО):
    """Виконує одне дерево й прибирає його модулі до завантаження наступного."""
    прогін = Прогін(корінь)
    try:
        yield прогін
    finally:
        прогін.закрити()


class Походження(unittest.TestCase):
    """Розрізняє джерела однакових значень, корені та відкинуті читання."""

    def test_власний_блок(self):
        """Текст товару не є місцем навіть при читанні через псевдонім документа."""
        (поля, _), запис = виконати('''документ = BeautifulSoup(тіло, 'html.parser')
інший = документ
запис = {'талія': інший.select_one('#товар p').get_text()}''')
        self.assertFalse(поля)
        self.assertEqual(звичайні(запис), {'талія': 'Власний опис'})

    def test_три_корені(self):
        """Документ, body й html не звужують до товару; поле може мати довільний ключ."""
        for вираз in ('документ', 'документ.body', 'документ.html'):
            with self.subTest(вираз=вираз):
                (поля, _), _ = виконати(f'''документ = BeautifulSoup(тіло, 'html.parser')
запис = {{'талія': {вираз}.get_text(' ', strip=True)}}''')
                self.assertEqual(len(поля), 1)

    def test_поза_блоком(self):
        """Пряме читання підвалу — місце незалежно від імені змінної."""
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
запис = {'довільне': суп.footer.get_text()}''')
        self.assertEqual(len(поля), 1)
        self.assertEqual(next(iter(поля.values())), {'довільне'})

    def test_сире_не_доходить(self):
        """Читання всього body, використане лише для довжини, не стає місцем."""
        (поля, журнал), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
сире = суп.body.get_text()
довжина = len(сире)
запис = {'опис': суп.select_one('#товар p').get_text()}''')
        self.assertFalse(поля)
        self.assertTrue(any(р['порушення'] and not р['поля'] for р in журнал))

    def test_однакові_слова_різні_джерела(self):
        """Збіг значень не заражає власний текст міткою стороннього читання."""
        тіло = СТОРІНКА.replace('Сторонній опис', 'Власний опис')
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
відкинуте = суп.footer.get_text()
запис = {'опис': суп.select_one('#товар p').get_text()}''', тіло)
        self.assertFalse(поля)

    def test_зріз_не_заражає_сусіда(self):
        """Після конкатенації й зрізу відкинутий сторонній шматок не лічиться."""
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
свій = суп.select_one('#товар p').get_text()
чужий = суп.footer.get_text()
запис = {'опис': (свій + чужий)[:len(свій)]}''')
        self.assertFalse(поля)

    def test_regex_з_кореня(self):
        """Regex по сирому HTML має адресу виконаного добування."""
        (поля, _), _ = виконати('''м = re.search(r'<footer>(.*?)</footer>', тіло)
запис = {'опис': м.group(1)}''')
        self.assertEqual({(д.файл, д.рядок) for д in поля}, {('синтетичний.py', 1)})

    def test_regex_вибрана_група(self):
        """Група regex не переносить мітку відкинутого сусіднього фрагмента."""
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
свій = суп.select_one('#товар p').get_text()
чужий = суп.footer.get_text()
м = re.search(r'(Власний опис)(.*)', свій + чужий)
запис = {'опис': м.group(1)}''')
        self.assertFalse(поля)

    def test_невідоме_вкладене_поле(self):
        """Лічба полів не залежить від наперед відомих ключів чи кількості ключів."""
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
запис = {'атрибути': {'ніколи_не_бачене': суп.footer.get_text()}}''')
        self.assertEqual(next(iter(поля.values())), {'атрибути.ніколи_не_бачене'})

    def test_видалений_текст(self):
        """Вилучений regex чи replace сторонній фрагмент у поле не доходить."""
        for вираз in ("re.sub('Сторонній опис', '', свій + чужий)", "(свій + чужий).replace('Сторонній опис', '')"):
            with self.subTest(вираз=вираз):
                (поля, _), _ = виконати(f'''суп = BeautifulSoup(тіло, 'html.parser')
свій = суп.select_one('#товар p').get_text()
чужий = суп.footer.get_text()
запис = {{'опис': {вираз}}}''')
                self.assertFalse(поля)

    def test_крихти(self):
        """Крихти поза блоком — виняток класу, а не сторонній опис."""
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
запис = {'розділ': суп.select_one('.breadcrumb').get_text()}''', СТОРІНКА.replace('<footer>', '<nav class="breadcrumb">Одяг / Сорочки</nav><footer>'))
        self.assertFalse(поля)

    def test_коди_стандарту_і_крихти_json(self):
        """JSON-LD-коди, числова сума й BreadcrumbList не є словами стороннього поля."""
        тіло = '<script>{"@type":["BreadcrumbList"],"name":"Сорочки","price":"1000","priceCurrency":"UAH"}</script>'
        (поля, _), _ = виконати('''д = json.loads(re.search(r'<script>(.*?)</script>', тіло).group(1))
запис = dict(розділ=д['name'], стандарт=д['@type'], ціна=д['price'], валюта=д['priceCurrency'])''', тіло)
        self.assertFalse(поля)

    def test_перезапис_не_доходить(self):
        """Перезаписане поле не зберігає походження старого значення."""
        (поля, _), _ = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
запис = {'опис': суп.footer.get_text()}
запис['опис'] = суп.select_one('#товар p').get_text()''')
        self.assertFalse(поля)

    def test_числа_й_адреси_json(self):
        """Саме числа, schema-коди й адреси фото не є словами крамниці."""
        (поля, _), _ = виконати('''д = json.loads(re.search(r'<script>(.*?)</script>', тіло).group(1))
запис = dict(стандарт=д['@type'], ціна=д['price'], валюта=д['priceCurrency'], фото=д['image'])''',
            '<script>{"@type":"Product","price":"1000","priceCurrency":"UAH","image":"/pic.jpg"}</script>')
        self.assertFalse(поля)

    def test_лічба_без_журналу(self):
        """Полегшений запуск CI дає ті самі місця, що й повний протокол."""
        (поля, _), запис = виконати('''суп = BeautifulSoup(тіло, 'html.parser')
запис = {'опис': суп.body.get_text()}''')
        без, журнал = підсумувати(запис, [], журнал=False)
        self.assertEqual(без, поля)
        self.assertFalse(журнал)


class ШляхЖнив(unittest.TestCase):
    """Фіксує походження на штучному дереві й окремо виконує незмінені поточні збирачі."""

    def test_жнива_json_ld_та_власний_h1(self):
        """JSON-LD із head доходить у назву XML; власний h1 не створює місця."""
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        тіло = СТОРІНКА.replace('<head>', '<head><script type="application/ld+json">{"@type":"Product","name":"Лляна сорочка","description":"Текст із JSON-LD"}</script>')
        with жнива() as прогін:
            запис, читання = прогін.сторінка(рядок, тіло)
        поля, _ = підсумувати(запис, читання)
        self.assertTrue(any(д.файл == 'zhnyvarka/жниварка.py' and any('name:' in п for п in імена) for д, імена in поля.items()))
        self.assertFalse(any('/article[1]/h1[1]' in д.вузол for д in поля))
        self.assertEqual(звичайні(запис['html']['name:']), ['Лляна сорочка'])
        self.assertEqual(звичайні(запис['html']['param:заголовок']), ['Лляна сорочка'])

    def test_js_body_до_опису(self):
        """JS штучного дерева переносить джерело body до поля опису офера."""
        опис = 'Лляна сорочка з довгими рукавами та м’яким коміром. ' * 8
        тіло = СТОРІНКА.replace('Власний опис', 'Опис ' + опис + ' Характеристики').replace('</body>', '<div class="product">Короткий кандидат</div></body>')
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        with жнива() as прогін:
            запис, читання = прогін.сторінка(рядок, тіло)
        поля, журнал = підсумувати(запис, читання)
        self.assertTrue(any(д.файл == 'zhnyvarka/виконавець.py' and 'браузер.опис' in імена for д, імена in поля.items()))
        self.assertTrue(any('@textContent' in д.вузол and 'body' in д.вузол for д in поля))
        self.assertTrue(any('@textContent' in р['вузол'] and not р['поля'] for р in журнал))
        self.assertEqual(str(запис['браузер']['опис']), опис)

    def test_штатна_відмова_офера(self):
        """Числовий sku ламає штучний офер, але не ховає читання HTML-шляху."""
        тіло = СТОРІНКА.replace('<head>', '<head><script type="application/ld+json">{"@type":"Product","name":"Лляна сорочка","sku":123}</script>')
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        with жнива() as прогін:
            запис, читання = прогін.сторінка(рядок, тіло)
        self.assertNotIn('браузер', запис)
        self.assertTrue(підсумувати(запис, читання)[0])
        self.assertTrue(any('TypeError' in в for в in прогін.відмови))

    def test_поточні_жнива_читають_власний_блок(self):
        """Поточні HTML і JS відкидають сторонню назву JSON-LD й беруть власний h1."""
        тіло = СТОРІНКА.replace('<article id="товар">',
            '<article id="товар" itemscope itemtype="https://schema.org/Product">').replace('<head>',
            '<head><script type="application/ld+json">{"@type":"Product","name":"Стороння назва"}</script>')
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        with жнива(КОРІНЬ) as прогін:
            запис, читання = прогін.сторінка(рядок, тіло)
        self.assertEqual(str(запис['браузер']['назва']), 'Лляна сорочка')
        self.assertIn('Лляна сорочка', звичайні(запис['html']['name:']))
        self.assertFalse(підсумувати(запис, читання)[0])

    def test_вхід_node_рядками(self):
        """Текст і атрибут понад ЧАСТИНА: кожен рядок входу node ≤ ЧАСТИНА, а значення доходять до JS цілими."""
        довге = 'Лляна сорочка з довгими рукавами. ' * (ЧАСТИНА // 20)
        атрибут = ', '.join(f'https://приклад.test/{і}.jpg 1x' for і in range(ЧАСТИНА // 20))
        self.assertGreater(len(довге), 2 * ШМАТОК)
        тіло = СТОРІНКА.replace('Власний опис', довге).replace('<h1>', f'<img srcset="{атрибут}"><h1>').replace(
            '<article id="товар">', '<article id="товар" itemscope itemtype="https://schema.org/Product">')
        with жнива(КОРІНЬ) as прогін:
            dom, _ = прогін.dom(тіло, 'https://приклад.test/product/сорочка', {})
            найбільший, усього, рядків = прогін.входи_node[-1]
        self.assertLessEqual(найбільший, ЧАСТИНА)
        self.assertGreater(усього, 2 * ЧАСТИНА)
        self.assertGreater(рядків, 2)
        self.assertEqual(str(dom['text']), re.sub(r'\s+', ' ', 'Лляна сорочка' + довге).strip()[:30000])
        self.assertEqual(str(dom['h1']), 'Лляна сорочка')
        self.assertEqual(len(dom['imgs']), ЧАСТИНА // 20)

    def test_помилка_спостерігача_не_стає_відмовою_продукту(self):
        """Розбіжність між справжнім і позначеним викликом червонить прилад."""
        def помилка():
            """Імітує збій самого спостерігача."""
            raise ValueError('збій спостереження')
        with жнива() as прогін, self.assertRaises(AssertionError):
            прогін.парний_виклик('проба', lambda: 'значення', помилка)


if __name__ == '__main__':
    unittest.main()

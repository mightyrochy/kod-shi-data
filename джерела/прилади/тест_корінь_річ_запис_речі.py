"""Перевіряє походження на штучних сторінках і реальному шляху жнив."""
import ast
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from корінь_річ_запис_речі import BeautifulSoup, Прогін, підсумувати, звичайні
from річ_запис_походження import HTML, Спостерігач, Позначки, походження

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
    """Запускає незмінені збирачі, а не копії їхніх правил видобування."""

    @classmethod
    def setUpClass(cls):
        """Один раз завантажує модулі й JS для синтетичних сторінок."""
        cls.прогін = Прогін(Path.cwd())

    @classmethod
    def tearDownClass(cls):
        """Прибирає перехоплення імпортів після тестів."""
        cls.прогін.закрити()

    def test_жнива_json_ld_та_власний_h1(self):
        """JSON-LD із head доходить у назву XML; власний h1 не створює місця."""
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        тіло = СТОРІНКА.replace('<head>', '<head><script type="application/ld+json">{"@type":"Product","name":"Лляна сорочка","description":"Текст із JSON-LD"}</script>')
        запис, читання = self.прогін.сторінка(рядок, тіло)
        поля, _ = підсумувати(запис, читання)
        self.assertTrue(any(д.файл == 'zhnyvarka/жниварка.py' and any('name:' in п for п in імена) for д, імена in поля.items()))
        self.assertFalse(any('/article[1]/h1[1]' in д.вузол for д in поля))

    def test_js_body_до_опису(self):
        """Справжній JS body-зліпок переносить джерело до поля опису офера жнив."""
        опис = 'Лляна сорочка з довгими рукавами та м’яким коміром. ' * 8
        тіло = СТОРІНКА.replace('Власний опис', 'Опис ' + опис + ' Характеристики').replace('</body>', '<div class="product">Короткий кандидат</div></body>')
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        запис, читання = self.прогін.сторінка(рядок, тіло)
        поля, журнал = підсумувати(запис, читання)
        self.assertTrue(any(д.файл == 'zhnyvarka/виконавець.py' and 'браузер.опис' in імена for д, імена in поля.items()))
        self.assertTrue(any('@textContent' in д.вузол and 'body' in д.вузол for д in поля))
        self.assertTrue(any('@textContent' in р['вузол'] and not р['поля'] for р in журнал))

    def test_штатна_відмова_офера(self):
        """Числовий sku ламає старий офер, але не ховає читання чинного HTML-шляху."""
        тіло = СТОРІНКА.replace('<head>', '<head><script type="application/ld+json">{"@type":"Product","name":"Лляна сорочка","sku":123}</script>')
        рядок = dict(id='проба', крамниця='приклад.test', url='https://приклад.test/product/сорочка')
        запис, читання = self.прогін.сторінка(рядок, тіло)
        self.assertNotIn('браузер', запис)
        self.assertTrue(підсумувати(запис, читання)[0])
        self.assertTrue(any('TypeError' in в for в in self.прогін.відмови))

    def test_помилка_спостерігача_не_стає_відмовою_продукту(self):
        """Розбіжність між справжнім і позначеним викликом червонить прилад."""
        def помилка():
            """Імітує збій самого спостерігача."""
            raise ValueError('збій спостереження')
        with self.assertRaises(AssertionError):
            self.прогін.парний_виклик('проба', lambda: 'значення', помилка)


if __name__ == '__main__':
    unittest.main()

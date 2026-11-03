# -*- coding: utf-8 -*-
"""Лічить джерела пропозицій заміни за паспортом Е3-заміна-з-перевіркою.

Обсяг: рекурсивно Python, JS, MJS і HTML у джерела/, крім тестів, проб,
приладів, стендів, лабораторії та даних аудиту. Продукт не імпортується.
Нерозбірний Python або непрочитаний файл — код 1 через обсяг_приладу.

Одиниця — виробник значення, не згадка слова: група ремонт/ремонт_заяви/
що_зняло_б/запит_у_каталог однієї знахідки; окремий текст настанови моделі;
об'єкт нової речі; підстановка речі в показі. Копії полів, журналювання,
коментарі й докстрінги не створюють нового виробника. Імена, f-рядки,
форматування, локальні присвоєння та імпортовані константи розгортаються.

Класифікація значення: дія заміни/додавання/вилучення з предметом одягу
або кольором; у полях ремонту — також опис альтернативи без дієслова.
Запит даних, пояснення, зміна способу носіння самі по собі — не місця.
Коди ремонт_заяви аналізуються разом із текстом тієї самої знахідки.

Умова (а): текст ремонту/вікно пошуку без кандидата й вердикта на образ
із ним — місце, хоч суд вихідного образу стоїть поруч. Для об'єктів прилад
шукає виконувані перевірки в охопній функції та її викликах: суд зміненого
складу, відмову за непройденим вердиктом, межі й захист явного вибору.
Самого виклику суду, зменшення суми або множини кодів правил недостатньо.
Розпізнаваний безпечний контракт: суд(новий_образ) → вердикт, далі
`if not вердикт['пройдено']: return None`, аналогічні негативні відмови
`у_межах(кандидат, межі)` й `зберігає_вибір(кандидат, явний_вибір)` до
емісії. Англійські еквіваленти також підтримуються. Контроль має домінувати
над емісією, а не бути в сусідній гілці. Нові форми контракту потребують
звірки людиною: це статичний прилад, не доказ довільної семантики програми.

`--докладно` показує й відкинутих кандидатів; `--json` дає повний інвентар
із причинами, шляхами до суду/пулу та обсягом для відтворюваної вибірки.
Останній рядок звичайного stdout — `місць: N`, успішне читання — код 0.
"""
import argparse
import ast
from collections import Counter
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import warnings

import обсяг_приладу as ОБСЯГ

warnings.simplefilter('ignore', SyntaxWarning)

ВИКЛЮЧЕНІ_ТЕКИ = {'проби', 'прилади', 'лабораторія', 'аудит', 'траса',
                  'дані_корпусу', 'node_modules', '__pycache__'}
ВИКЛЮЧЕНІ_ІМЕНА = ('тест', 'test_', 'стенд', 'проба', 'гейт', 'gate_', 'audit_', 'жнива_')
ПОЛЯ_РЕМОНТУ = {'ремонт', 'ремонти', 'ремонт_заяви', 'що_зняло_б', 'запит_у_каталог',
                'repair', 'fix', 'fixes', 'suggestion', 'порада'}
ПОЛЯ_ТЕКСТУ = {'суть', 'чому', 'повідомлення', 'для_неї', 'text', 'message', 'answer'}
ПРЕДМЕТ = re.compile(
    r'річ|реч[іе]|одяг|образ|кол[іьо]р|хром|світлот|тон|нейтрал|принт|мотив|'
    r'взут|пар[аиу]|шар[фуаи]|прикрас|аксесуар|верх|низ|штани|спідниц|сукн|'
    r'светр|гольф|косух|жакет|кардиган|пальт|комір|горловин|пояс|колгот|'
    r'шапк|рукавиц|сумк|сереж|кольє|ланцюг|оправ|болванк|розмір|крій|крою|'
    r'тканин|каблук|халяв|колодк|протектор|біло|метал|капюшон|силует|слот|'
    r'гардероб|накидк|квадрат|устілк|insole|item|outfit|cloth|colou?r|pair|belt|'
    r'frame|scarf|necklace|motif|hat|tights|bottom|size|cut|metal|white|fabric|'
    r'garment|shoe|bag|layer|accessor|dress|skirt|trouser|top\b|chroma|lightness', re.I)
ДІЯ = re.compile(
    r'замін(?:ити|и|юй|ювати)|замість|додати|додай|докупити|прибрати|прибери|зняти|'
    r'зніми|узяти|взяти|візьми|перевести|перенести|приглушити|звести|зрівняй|'
    r'повторити колір|розвести.*(?:світлот|хром)|'
    r'\b(?:replac\w*|swap\w*|remove\w*|add(?:ed|ing)?|substitut\w*|take|choose)\b', re.I)
АЛЬТЕРНАТИВА = re.compile(
    r'інш[аийоуі]|той самий.*(?:тон|кольор|крій|тканин)|та сама.*(?:верс|сім|річ)|'
    r'коротш|довш|нижч|вищ|ширш|вужч|глибш|темніш|світліш|тихіш|гучніш|важч|легш|більш|менш|'
    r'нейтрал|колгот|шарф|трет[яю]|прикрас|матов|принт|протектор|літня форма|зимова форма|'
    r'хромою|відтінок|(?:greater|lower|other|different|same|warmer|cooler|nude|matching|contrast|heavier|lighter)', re.I)
ВХІД = re.compile(
    r'^(?:подати|передати|запитати|виміряти|уточнити|дістати тип|дивитись|звірити|'
    r'розмітити|зйомка|фото речі|висота каблука зі|два питання|одне питання|'
    r'картка не несе|міряти|приміряти|брати номер|узяти з картки|узяти трійку)', re.I)
ЗАБОРОНА = re.compile(r'\b(?:do not|never|must not|cannot|does not)\s+(?:judge or )?'
                         r'(?:replac\w*|swap\w*|remove\w*|add\w*)|'
                         r'\badd (?:no|nothing)\b|'
                         r'не (?:замінюй|замінювати|замінити|додавай|додавати|прибирай)', re.I)
СУД = re.compile(r'(?:^|[._])(?:суд|суддя|judge|перевірити_склад|ваги_образу|evaluate)', re.I)
МЕЖІ = re.compile(r'у_межах|в_межах|within_bounds|within_request|межі_заміни')
ВИБІР = re.compile(r'зберігає_вибір|не_суперечить_вибору|respects_choice|preserves_choice')
НОВИЙ_СКЛАД = re.compile(r'нов[іиаий_]|після|замі|new|after|replac|swap')


@dataclass
class Кандидат:
    """Виробник пропозиції та відтворюваний доказ його класифікації."""
    файл: str
    рядок: int
    вид: str
    текст: str
    функція: str = ''
    умови: str = ''
    причина: str = ''
    шлях: str = ''


def коротко(текст, межа=240):
    """Стискає лише показ тексту; аналіз завжди бере повне значення."""
    return re.sub(r'\s+', ' ', текст).strip()[:межа]


def пропозиція(текст, ремонт=False):
    """Відрізняє заміну речі/кольору від запиту входу, пояснення та носіння."""
    if not ремонт and re.fullmatch(r'[a-z][a-z0-9_]*', текст.strip()):
        return False, 'машинний код, не текст пропозиції'
    текст = re.sub(r'`[\w.]+`', '', текст).lower().replace('_', ' ')
    if not текст.strip():
        return False, 'порожнє значення або копія поля; нового рішення немає'
    # Відкидаємо лише заборонену дію, а не все речення: після неї буває альтернатива.
    чистий = ЗАБОРОНА.sub('', текст)
    if ремонт:
        if re.search(r'(?:взяти|узяти) тип|take from the day.s band.*types', чистий):
            return True, 'ремонт пропонує інший тип речі в смузі дня'
        if re.search(r'\b(?:replace|swap|remove|add)\b', чистий):
            return True, 'код/текст ремонту змінює склад або замінює річ'
        if re.search(r'\b(?:move|mute|match|keep|echo|tie|cover|take|shift|bring|put)\b', чистий) and ПРЕДМЕТ.search(чистий):
            if not re.search(r'gesture|wear asymmetrically|allowed state|raise collar|knot placement|her choice|from card|походження|запитати|виміряти', чистий):
                return True, 'ремонт змінює носія кольору, річ або склад образу'
    if not ремонт:
        # Згадка заміни, опис уже зробленого, вибір палітри/образу — не нова порада.
        чистий = re.sub(r'замість|\b(?:take|choose|replaced|removed|swapped|added|adding|replacement)\b', '', чистий)
        if re.search(r'choos\w* a replacement|item to replace|for replacing', текст):
            чистий += ' replace item'
        if re.search(r'choose exactly one different item', текст):
            чистий += ' replace item'
        if re.search(r'\b(?:do not|never|no suggestions|no .*for).*\b(?:swap|add|replace)', текст):
            return False, 'заборона пропонувати заміну або додаткову річ'
    if ремонт and re.search(r'\b(?:зняти|прибрати|додати|remove|add)\b', чистий):
        return True, 'ремонт додає або прибирає предмет, названий носієм/кодом заяви'
    if ДІЯ.search(чистий) and ПРЕДМЕТ.search(чистий):
        if not ВХІД.match(чистий) or re.search(r'або.*(?:інша|річ|пара|матова)|заміни|replace', чистий):
            return True, 'дія змінює склад образу або колір речі'
    if ремонт and ПРЕДМЕТ.search(чистий) and АЛЬТЕРНАТИВА.search(чистий) and not ВХІД.match(чистий):
        return True, 'ремонт називає альтернативну річ або колір без дієслова заміни'
    return False, 'запит даних, пояснення, носіння чи опис поля без пропозиції іншої речі/кольору'


def поля(вузол):
    """Повертає поля літерала словника або виклику з іменованими аргументами."""
    вих = {}
    if isinstance(вузол, ast.IfExp):
        return dict(поля(вузол.body), **поля(вузол.orelse))
    if isinstance(вузол, ast.Dict):
        for к, з in zip(вузол.keys, вузол.values):
            if к is None:
                вих.update(поля(з))
            elif isinstance(к, ast.Constant) and isinstance(к.value, str):
                вих[к.value] = з
    if isinstance(вузол, ast.Call):
        if isinstance(вузол.func, ast.Name) and вузол.func.id == 'dict':
            for а in вузол.args:
                вих.update(поля(а))
        for к in вузол.keywords:
            if к.arg:
                вих[к.arg] = к.value
            else:
                вих.update(поля(к.value))
    return вих


class Модуль:
    """AST, зв'язки батьків, визначення та імпорти одного Python-файлу."""

    def __init__(self, шлях, текст):
        """Розбирає весь файл, реєструючи збій як непрочитаний обсяг."""
        self.шлях, self.текст = шлях, текст
        self.дерево = ОБСЯГ.розібрати(текст, шлях)
        self.батьки, self.присвоєння, self.імпорти, self.функції = {}, {}, {}, {}
        if self.дерево is None:
            return
        for в in ast.walk(self.дерево):
            for д in ast.iter_child_nodes(в):
                self.батьки[д] = в
        for в in ast.walk(self.дерево):
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.функції[в.name] = в
            if isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None:
                for ц in в.targets if isinstance(в, ast.Assign) else [в.target]:
                    if isinstance(ц, ast.Name):
                        self.присвоєння.setdefault((self.охопна(в), ц.id), []).append(в.value)
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                if в.func.attr in {'append', 'extend'}:
                    self.присвоєння.setdefault((self.охопна(в), в.func.value.id), []).extend(в.args)
            if isinstance(в, ast.ImportFrom) and в.module:
                for а in в.names:
                    self.імпорти[а.asname or а.name] = (в.module, а.name)
            elif isinstance(в, ast.Import):
                for а in в.names:
                    self.імпорти[а.asname or а.name] = (а.name, '')

    def охопна(self, вузол):
        """Знаходить найближчу функцію, не приписуючи сусідній гілці її перевірок."""
        вузол = self.батьки.get(вузол)
        while вузол is not None:
            if isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return вузол
            вузол = self.батьки.get(вузол)
        return None

    def докстрінг(self, вузол):
        """Відрізняє документацію від виконуваного значення рядка."""
        п = self.батьки.get(вузол)
        if not isinstance(п, ast.Expr):
            return False
        д = self.батьки.get(п)
        return isinstance(д, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and д.body[0] is п


class Аналіз:
    """Розгортає значення і простежує виклики без запуску коду продукту."""

    def __init__(self, модулі):
        """Індексує також вкладені модулі; неоднозначний імпорт не обирає навмання."""
        self.модулі = модулі
        self.за_імям = {}
        self.кодові_тексти = {}
        for м in модулі:
            ім = м.шлях.removeprefix('джерела/').removesuffix('.py').replace('/', '.')
            self.за_імям[ім] = м
            if 'заява' in м.функції and м.дерево is not None:
                for в in ast.walk(м.дерево):
                    if isinstance(в, ast.Dict):
                        for к, з in zip(в.keys, в.values):
                            if (isinstance(к, ast.Constant) and isinstance(к.value, str)
                                    and re.fullmatch(r'[a-z][a-z0-9_]+', к.value)
                                    and isinstance(з, ast.Constant) and isinstance(з.value, str)):
                                self.кодові_тексти[к.value] = з.value

    def розкрити_коди(self, текст):
        """Додає зміст коду лише в місці емісії ремонту, не в словнику перекладу."""
        return re.sub(r'\b[a-z][a-z0-9_]+\b',
                      lambda з: з.group() + ' ' + self.кодові_тексти.get(з.group(), ''), текст)

    def визначення(self, м, вузол):
        """Дає модуль та ім'я локального чи імпортованого посилання."""
        if isinstance(вузол, ast.Name):
            if вузол.id in м.імпорти:
                ім, назва = м.імпорти[вузол.id]
                return self.за_імям.get(ім), назва
            return м, вузол.id
        if isinstance(вузол, ast.Attribute) and isinstance(вузол.value, ast.Name):
            ім, _ = м.імпорти.get(вузол.value.id, ('', ''))
            return self.за_імям.get(ім), вузол.attr
        return None, ''

    def значення(self, м, вузол, бачені=None):
        """Збирає текст значення через присвоєння, імпорти й повернення обгорток."""
        if вузол is None:
            return ''
        бачені = set() if бачені is None else бачені
        ключ = (м.шлях, id(вузол))
        if ключ in бачені:
            return ''
        бачені.add(ключ)
        if isinstance(вузол, ast.Constant):
            return вузол.value if isinstance(вузол.value, str) else ''
        if isinstance(вузол, ast.JoinedStr):
            return ''.join(ч.value if isinstance(ч, ast.Constant) and isinstance(ч.value, str) else '{}'
                           for ч in вузол.values)
        if isinstance(вузол, ast.BinOp) and isinstance(вузол.op, ast.Mod):
            return self.значення(м, вузол.left, бачені)
        if isinstance(вузол, (ast.Name, ast.Attribute)):
            інший, ім = self.визначення(м, вузол)
            if інший:
                призначення = (м.охопна(вузол) if інший is м else None, ім)
                значення = інший.присвоєння.get(призначення) or інший.присвоєння.get((None, ім), [])
                return ' '.join(self.значення(інший, з, бачені) for з in значення)
            return ''
        if isinstance(вузол, ast.Call):
            if isinstance(вузол.func, ast.Attribute) and вузол.func.attr == 'заява':
                return ' '.join(self.значення(м, з, бачені) for з in вузол.args)
            інший, ім = self.визначення(м, вузол.func)
            if інший and ім in інший.функції:
                ф = інший.функції[ім]
                return ' '.join(self.значення(інший, з.value, бачені)
                                for з in ast.walk(ф) if isinstance(з, ast.Return))
            # .get() є копією, не новим текстом ремонту.
            if isinstance(вузол.func, ast.Attribute) and вузол.func.attr in {'get', 'pop'}:
                return ''
        return ' '.join(self.значення(м, д, бачені) for д in ast.iter_child_nodes(вузол)
                        if not isinstance(д, ast.expr_context))

    def виклики(self, м, функція, бачені=None):
        """Дає виконувані виклики разом із місцями та їхнім походженням."""
        бачені = set() if бачені is None else бачені
        if функція is None or (м.шлях, функція.name) in бачені:
            return []
        бачені.add((м.шлях, функція.name))
        вих = []
        for в in ast.walk(функція):
            if not isinstance(в, ast.Call):
                continue
            ім = ast.unparse(в.func)
            вих.append((ім, в, м))
            інший, ім = self.визначення(м, в.func)
            if інший and ім in інший.функції:
                вих.extend(self.виклики(інший, інший.функції[ім], бачені))
        return вих

    def контракт(self, м, вузол):
        """Перевіряє домінуючі відмови; згадка перевірки в тексті не є контролем."""
        ф = м.охопна(вузол)
        річ = поля(вузол).get('річ')
        річ_вираз = ast.unparse(річ) if річ is not None else None
        виконано, докази = set(), []
        if ф is None:
            return виконано, докази
        # Лише попередні if на прямому шляху до емісії; вкладений сусідній if не домінує.
        блок = вузол
        while блок in м.батьки:
            п = м.батьки[блок]
            if hasattr(п, 'body') and isinstance(п.body, list) and блок in п.body:
                for ум in п.body[:п.body.index(блок)]:
                    if not isinstance(ум, ast.If) or not isinstance(ум.test, ast.UnaryOp) or not isinstance(ум.test.op, ast.Not):
                        continue
                    if not ум.body or not isinstance(ум.body[-1], (ast.Return, ast.Raise)):
                        continue
                    if isinstance(ум.body[-1], ast.Return) and ум.body[-1].value is not None:
                        if not (isinstance(ум.body[-1].value, ast.Constant) and ум.body[-1].value.value is None):
                            continue
                    тест = ум.test.operand
                    вирази = [тест]
                    if isinstance(тест, ast.Subscript) and isinstance(тест.slice, ast.Constant):
                        if тест.slice.value in {'пройдено', 'passed', 'ok'} and isinstance(тест.value, ast.Name):
                            вирази = [з for з in м.присвоєння.get((ф, тест.value.id), []) if з.lineno < ум.lineno][-1:]
                    for вираз in вирази:
                        for виклик in ast.walk(вираз):
                            if not isinstance(виклик, ast.Call):
                                continue
                            імя = ast.unparse(виклик.func)
                            if СУД.search(імя) and виклик.args and НОВИЙ_СКЛАД.search(ast.unparse(виклик.args[0])):
                                виконано.add('а')
                            та_сама = виклик.args and ast.unparse(виклик.args[0]) == річ_вираз
                            if МЕЖІ.search(імя) and len(виклик.args) >= 2 and та_сама:
                                виконано.add('б')
                            if ВИБІР.search(імя) and len(виклик.args) >= 2 and та_сама:
                                виконано.add('в')
            блок = п
            if блок is ф:
                break
        for ім, виклик, інший in self.виклики(м, ф):
            if СУД.search(ім) or re.search(r'кандидат|пул|крамниц|запасн|catalog|pool', ім):
                докази.append(f'{інший.шлях}:{виклик.lineno} {ім}')
        return виконано, list(dict.fromkeys(докази))[:10]


def python_кандидати(аналіз, м):
    """Знаходить виробників ремонтів, настанов і структурованих замін."""
    if м.дерево is None:
        return []
    вих, зайняті = [], set()
    for в in ast.walk(м.дерево):
        набір = поля(в)
        ремонтні = ПОЛЯ_РЕМОНТУ & набір.keys()
        if в in зайняті:
            continue
        if not ремонтні:
            continue
        # Bool «ремонти=False» керує серіалізацією, не пропонує річ.
        if all(isinstance(набір[к], ast.Constant) and not isinstance(набір[к].value, str) for к in ремонтні):
            continue
        головне = next((к for к in ('ремонт', 'ремонти', 'що_зняло_б', 'запит_у_каталог', 'ремонт_заяви')
                        if к in ремонтні), sorted(ремонтні)[0])
        вузол = набір[головне]
        текст = ' '.join(аналіз.значення(м, набір[к]) for к in sorted(ремонтні))
        текст = аналіз.розкрити_коди(текст)
        зайняті.update(ast.walk(в))
        так, причина = пропозиція(текст, ремонт=True)
        if 'запит_у_каталог' in ремонтні and поля(набір['запит_у_каталог']):
            так, причина = True, 'задане вікно/тип кандидата передається як спосіб ремонту'
        ф = м.охопна(в)
        вих.append(Кандидат(м.шлях, вузол.lineno, 'ремонт', коротко(текст),
                           ф.name if ф else '', 'а' if так else '',
                           'немає кандидата з вердиктом на образ із ним; ' + причина if так else причина,
                           'знахідка → вердикт_моделі.ремонт_рядком / дріт_моделі._знахідка → модель або мовний шар'))
    for в in ast.walk(м.дерево):
        if в in зайняті or м.докстрінг(в):
            continue
        if isinstance(в, (ast.Constant, ast.JoinedStr)) and (isinstance(в, ast.JoinedStr) or isinstance(в.value, str)):
            if isinstance(м.батьки.get(в), (ast.JoinedStr, ast.FormattedValue)):
                continue
            текст = аналіз.значення(м, в)
            так, причина = пропозиція(текст)
            if not так and not ЗАБОРОНА.search(текст):
                continue
            # Літерал має бути на шляху тексту моделі/відповіді, а не у словнику лексики.
            п, контекст, словникове = в, [], False
            while п in м.батьки:
                п = м.батьки[п]
                if isinstance(п, ast.Call):
                    контекст.append(ast.unparse(п.func))
                elif isinstance(п, ast.keyword):
                    контекст.append(п.arg or '')
                elif isinstance(п, ast.Dict):
                    for к, з in zip(п.keys, п.values):
                        if isinstance(к, ast.Constant) and з is в:
                            контекст.append(str(к.value))
                            словникове = к.value not in ПОЛЯ_ТЕКСТУ | ПОЛЯ_РЕМОНТУ
                if {'t', 'val'} <= поля(п).keys():
                    словникове = True
                elif isinstance(п, (ast.Assign, ast.AnnAssign)):
                    контекст.extend(ast.unparse(ц) for ц in (п.targets if isinstance(п, ast.Assign) else [п.target]))
                elif isinstance(п, ast.Return):
                    контекст.append('return')
                if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    контекст.append(п.name)
                    break
            конт = ' '.join(контекст)
            явний_вихід = any(ч in ПОЛЯ_ТЕКСТУ | {'правила', 'роль', 'як', 'return'} for ч in контекст)
            промпт = bool(re.search(r'Оголошення|Поле|порад|промпт|ПРАВИЛ|РОЛЬ|РЯДОК|prompt', конт, re.I))
            if not (явний_вихід or промпт):
                continue
            if словникове:
                так, причина = False, 'реєстр/словник: значення набуває ролі ремонту лише в місці його емісії'
            if any(к in контекст for к in ('ламається', 'джерело', 'сила_нп_джерело', 'source')):
                так, причина = False, 'пояснення механізму або джерела; не порада заміни'
            if re.search(r'\b(?:add|adding)\s+(?:one )?(?:object|photo)|дода[йти]+ (?:фото|його в профілі)', текст, re.I):
                так, причина = False, 'операція з описом/фото, не заміна речі образу'
            if re.search(r'(?:she (?:called|calls|named)|she added herself|she corrects|her new message|реченням українською|називай її)', текст, re.I):
                так, причина = False, 'передає вибір жінки або перекладає дані, самостійного добору немає'
            if re.search(r'новий текст|українськ|Ukrainian noun|what that text advises|рядки видів|список речей|позначити', текст, re.I):
                так, причина = False, 'мовний або показовий шар відтворює готові дані, нового рішення немає'
            if re.search(r'взяти нема|інший каталог|у пулі нема|кодів|field.*meanings', текст, re.I):
                так, причина = False, 'пояснення браку даних/кандидатів або опис формату'
            if re.search(r'changes the code has verified|suggest replacements only from|only with.*swap_spares', текст, re.I):
                так, причина = False, 'опис/вибір готових змін; виробник кандидатів обліковується окремо'
            ф = м.охопна(в)
            вих.append(Кандидат(м.шлях, в.lineno, 'текст', коротко(текст), ф.name if ф else '',
                               'а' if так else '',
                               'настанова заміни до суду конкретного зміненого образу' if так else причина,
                               'текст → ' + коротко(конт, 160)))
        набір = поля(в)
        структурна = (('річ' in набір and 'готово' in набір)
                      or {'ціль', 'нова'} <= набір.keys()
                      or {'на', 'стан'} <= набір.keys())
        батько = м.батьки.get(в)
        if isinstance(батько, ast.Call) and isinstance(батько.func, ast.Attribute) and батько.func.attr == 'append':
            ціль = батько.func.value
            if isinstance(ціль, ast.Subscript) and isinstance(ціль.slice, ast.Constant):
                структурна |= ціль.slice.value in {'запасні', 'replacements', 'spares'} and 'id' in набір
        if not структурна:
            continue
        # Відмова/збереження старої речі не є пропозицією.
        стан = набір.get('стан')
        if isinstance(стан, ast.Constant) and стан.value in {'refused', 'kept'}:
            continue
        виконано, докази = аналіз.контракт(м, в)
        відсутні = ''.join(к for к in 'абв' if к not in виконано)
        ф = м.охопна(в)
        вих.append(Кандидат(м.шлях, в.lineno, 'об’єкт заміни', коротко(ast.unparse(в)), ф.name if ф else '',
                           відсутні, 'не доведено домінуючі перевірки: ' + ', '.join(відсутні)
                           if відсутні else 'суд нового образу, межі й явний вибір перевірені до емісії',
                           '; '.join(докази) or 'виробник → повернення нової речі; суд нового образу не знайдений'))
    return вих


def js_лексеми(текст, шлях='<JS>'):
    """Читає рядки JS і прибирає коментарі, зберігаючи позиції та переноси.

    Шаблонні рядки беруться цілком: текст для моделі часто має ${дані}.
    Регулярки залишаються кодом і не створюють текстової пропозиції.
    """
    код, рядки = list(текст), []

    def стерти(початок, кінець):
        """Прибирає токен із коду без зміни його координат."""
        for і in range(початок, кінець):
            if код[і] != '\n':
                код[і] = ' '

    def рядок(початок):
        """Читає лапки та шаблон з рекурсивними ${виразами} і вкладеними шаблонами."""
        лапка, і, частини, край = текст[початок], початок + 1, [], початок + 1
        while і < len(текст):
            if текст[і] == '\\':
                і += 2
            elif текст[і] == лапка:
                частини.append(текст[край:і])
                стерти(початок, і + 1)
                рядки.append((початок, ''.join(частини)))
                return і + 1
            elif лапка == '`' and текст.startswith('${', і):
                частини.extend((текст[край:і], '{}'))
                і = читати(і + 2, вкладено=True)
                край = і
            else:
                і += 1
        ОБСЯГ.непрочитано(шлях, f'незакритий рядок JS на {текст.count(chr(10), 0, початок) + 1}')
        return len(текст)

    def читати(початок, вкладено=False):
        """Лексує код; коментарі, regex та лапки не міняють баланс ${…}."""
        і, глибина, попередній = початок, 0, ''
        while і < len(текст):
            ч = текст[і]
            if текст.startswith('//', і):
                кінець = текст.find('\n', і)
                кінець = len(текст) if кінець < 0 else кінець
                стерти(і, кінець)
                і = кінець
                continue
            if текст.startswith('/*', і):
                кінець = текст.find('*/', і + 2)
                if кінець < 0:
                    ОБСЯГ.непрочитано(шлях, 'незакритий коментар JS')
                    return len(текст)
                стерти(і, кінець + 2)
                і = кінець + 2
                continue
            if ч in "'\"`":
                і = рядок(і)
                попередній = 'значення'
                continue
            if ч == '/' and (not попередній or попередній in '=(:,[!&|?;{' or попередній in {'return', 'case', '=>'}):
                кінець, клас = і + 1, False
                while кінець < len(текст):
                    з = текст[кінець]
                    if з == '\\':
                        кінець += 2
                        continue
                    if з == '[':
                        клас = True
                    elif з == ']':
                        клас = False
                    elif з == '/' and not клас:
                        кінець += 1
                        while кінець < len(текст) and текст[кінець].isalpha():
                            кінець += 1
                        break
                    elif з == '\n':
                        break
                    кінець += 1
                стерти(і, кінець)
                і, попередній = кінець, 'значення'
                continue
            if ч == '{':
                глибина += 1
            elif ч == '}':
                if вкладено and глибина == 0:
                    return і + 1
                глибина -= 1
            if ч.isalpha() or ч in '_$':
                кінець = і + 1
                while кінець < len(текст) and (текст[кінець].isalnum() or текст[кінець] in '_$'):
                    кінець += 1
                попередній, і = текст[і:кінець], кінець
                continue
            if not ч.isspace():
                попередній = ч
            і += 1
        return і

    читати(0)
    return ''.join(код), sorted(рядки)


def веб_кандидати(шлях, текст, зсув=0):
    """Знаходить видимі/модельні тексти JS та виконувані підстановки речей."""
    вих = []
    код, рядки = js_лексеми(текст, шлях)
    for позиція, значення in рядки:
        так, причина = пропозиція(значення)
        кнопка = bool(re.fullmatch(r'замінити(?: цю)?|replace', значення.strip(), re.I))
        if not так and not кнопка and not ЗАБОРОНА.search(значення):
            continue
        if re.search(r'позначити|вердикт.*записано|замінено|замінила річ після|додай (?:фото|його)', значення, re.I):
            так = False
        if re.search(r'[_a-z]+\s*=|\b(?:ABOUT|schema|code_added|photo_swap|remove_not_done)\b', значення):
            так = False
        if '<html' in значення.lower() or '<!doctype' in значення.lower() or значення.startswith('Заміни не знайдено'):
            так = False
        вих.append(Кандидат(шлях, зсув + текст.count('\n', 0, позиція) + 1, 'текст JS', коротко(значення),
                           умови='а' if так else '', причина='пропозиція без вердикта нового образу' if так else
                           'елемент вибору жінки/заборона; сам текст не обирає нову річ', шлях='JS → показ або модель'))
    for збіг in re.finditer(r'(?:[\w.]+\.)?(?:речі|items|outfit)\s*\[[^\]\n]+\]\s*=(?!=)[^;\n]+', код):
        рядок = зсув + текст.count('\n', 0, збіг.start()) + 1
        вих.append(Кандидат(шлях, рядок, 'підстановка JS', коротко(збіг.group()), умови='абв',
                           причина='зміна складу в показі; контракт суду, меж і явного вибору не прикріплений до нової речі',
                           шлях='міст → нова річ → підстановка в речі картки'))
    return вих


class HTMLТексти(HTMLParser):
    """Розбирає HTML; inline JS і видимі тексти мають окремі шляхи аналізу."""

    def __init__(self, шлях):
        """Готує накопичувач кандидатів без залежності від браузера."""
        super().__init__(convert_charrefs=True)
        self.шлях, self.вих, self.стек = шлях, [], []

    def handle_starttag(self, tag, attrs):
        """Запам'ятовує контекст тегу та тексти видимих атрибутів."""
        self.стек.append(tag)
        for ключ, текст in attrs:
            if ключ in {'title', 'aria-label', 'placeholder', 'value'} and текст:
                self.додати(текст)

    def handle_endtag(self, tag):
        """Прибирає закритий контекст, зокрема script/style."""
        if tag in self.стек:
            self.стек = self.стек[:len(self.стек) - 1 - self.стек[::-1].index(tag)]

    def handle_data(self, data):
        """Аналізує вміст JS окремо від видимого тексту HTML."""
        if self.стек and self.стек[-1] == 'script':
            self.вих.extend(веб_кандидати(self.шлях, data, self.getpos()[0] - 1))
        elif 'style' not in self.стек:
            self.додати(data)

    def додати(self, текст):
        """Реєструє лише текст заміни або кнопку, не розмітку чи коментар."""
        так, причина = пропозиція(текст)
        if re.search(r'додати фото|додай фото|add photo', текст, re.I):
            так = False
        if так or текст.strip().lower() in {'замінити', 'замінити цю', 'replace'}:
            self.вих.append(Кандидат(self.шлях, self.getpos()[0], 'текст HTML', коротко(текст),
                                   умови='а' if так else '', причина='текст заміни без суду нового образу' if так else
                                   'кнопка лише починає вибір жінки', шлях='HTML → жінка'))


def сканувати(корінь):
    """Читає весь визначений обсяг і повертає інвентар та лічби файлів."""
    дж = Path(корінь) / 'джерела'
    if not дж.is_dir():
        ОБСЯГ.непрочитано(дж, 'немає теки джерел')
        return [], {}
    модулі, веб, обсяг = [], [], Counter()
    for файл in sorted(дж.rglob('*')):
        if not файл.is_file() or файл.suffix not in {'.py', '.js', '.mjs', '.html'}:
            continue
        if any(ч in ВИКЛЮЧЕНІ_ТЕКИ for ч in файл.relative_to(дж).parts[:-1]) or файл.name.startswith(ВИКЛЮЧЕНІ_ІМЕНА):
            обсяг['виключено'] += 1
            continue
        шлях = файл.relative_to(корінь).as_posix()
        try:
            текст = файл.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as помилка:
            ОБСЯГ.непрочитано(шлях, помилка)
            continue
        обсяг[файл.suffix] += 1
        if файл.suffix == '.py':
            модулі.append(Модуль(шлях, текст))
        else:
            веб.append((шлях, текст))
    аналіз = Аналіз(модулі)
    вих = [к for м in модулі for к in python_кандидати(аналіз, м)]
    for шлях, текст in веб:
        if шлях.endswith('.html'):
            парсер = HTMLТексти(шлях)
            парсер.feed(текст)
            парсер.close()
            вих.extend(парсер.вих)
        else:
            вих.extend(веб_кандидати(шлях, текст))
    # Різні поля того самого рядка не збільшують число місць.
    різні = {}
    for к in вих:
        ключ = к.файл, к.рядок
        if ключ not in різні or (к.умови and not різні[ключ].умови):
            різні[ключ] = к
    return sorted(різні.values(), key=lambda к: (к.файл, к.рядок)), dict(обсяг)


def головна():
    """Друкує місця або повний машинний інвентар, не змінюючи продукту."""
    розбір = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    розбір.add_argument('--корінь', default='.')
    розбір.add_argument('--докладно', action='store_true')
    розбір.add_argument('--json', action='store_true')
    а = розбір.parse_args()
    кандидати, обсяг = сканувати(Path(а.корінь).resolve())
    місця = [к for к in кандидати if к.умови]
    if а.json:
        print(json.dumps({'обсяг': обсяг, 'місць': len(місця), 'кандидати': [asdict(к) for к in кандидати]},
                         ensure_ascii=False, indent=2))
    else:
        for к in кандидати:
            if к.умови or а.докладно:
                print(f'{к.файл}:{к.рядок} · {к.умови or "не місце"} · {к.причина} · {к.текст}')
        print('обсяг: ' + ', '.join(f'{к}={з}' for к, з in sorted(обсяг.items())))
        print(f'місць: {len(місця)}')


if __name__ == '__main__':
    головна()

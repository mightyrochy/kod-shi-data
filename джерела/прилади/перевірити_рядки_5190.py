"""Перевіряє offline протокол пілота 5190; жодного HTTP або моделі.

Підробна відповідь доводить тільки форму, cache/provenance та облік часу.
Не є перевіркою якості MamayLM, кольорових кодів, вікон або фото.
"""
import gzip
import io
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as XML
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

import рядки_кольору_5190 as П


def рядок(сирий):
    """Будує точний вхід для статичної протокольної фікстури."""
    return {'row_id': П.відбиток(сирий.encode('utf-8')), 'raw': сирий}


def відоме(вхід):
    """Дає фіксовану відповідь; не тлумачить слів фікстури."""
    return {'row_id': вхід['row_id'], 'status': 'known', 'relation': 'single',
            'variants': [{'quote': вхід['raw'], 'colors': [{'code': 'blue', 'quote': вхід['raw']}]}],
            'unknown_reason': 'none'}


def невідоме(вхід):
    """Дає синтетичний unknown без мовного рішення."""
    return {'row_id': вхід['row_id'], 'status': 'unknown', 'relation': 'unknown',
            'variants': [], 'unknown_reason': 'insufficient_context'}


def відповідь(рядки):
    """Загортає синтетичні дані у відповідь місцевого HTTP-протоколу."""
    return {'model': П.МОДЕЛЬ, 'choices': [{'finish_reason': 'stop',
            'message': {'content': json.dumps({'rows': рядки}, ensure_ascii=False)}}]}


class Протокол(unittest.TestCase):
    """Перевіряє протокол на вузьких негативних та інтеграційних фікстурах."""

    def setUp(self):
        """Створює чисту тимчасову теку та малий контрольний рядок."""
        self.тимчасова = tempfile.TemporaryDirectory()
        self.addCleanup(self.тимчасова.cleanup)
        self.тека = Path(self.тимчасова.name)
        self.журнал = self.тека / 'once'
        self.реальна_історія = П.попередні_спроби
        для_журналу = patch.object(П.Ж, 'тека_журналу', return_value=self.журнал)
        для_історії = patch.object(П, 'попередні_спроби', return_value=[])
        для_журналу.start(); для_історії.start()
        self.addCleanup(для_журналу.stop); self.addCleanup(для_історії.stop)
        self.вхід = рядок('«Синій»')
        self.коди = П.контракт()[3]

    def перевірити(self, розбір):
        """Перевіряє один рядок фікстури тим самим валідатором."""
        return П.перевірити_відповідь({'rows': [розбір]}, [self.вхід], self.коди)

    def test_цитата_байти_та_семантична_межа(self):
        """Приймає точний фрагмент, але не оголошує код семантично істинним."""
        розбір = відоме(self.вхід)
        розбір['variants'][0]['colors'][0]['quote'] = 'Синій'
        вихід = self.перевірити(розбір)[self.вхід['row_id']]
        self.assertEqual(вихід['quote_utf8_spans'], [[[2, 12]]])
        розбір['variants'][0]['colors'][0]['code'] = 'red'
        self.перевірити(розбір)  # Наявність цитати не є судом про значення.
        for цитата in ('синій', 'Синій ', '', 'вигадана'):
            with self.subTest(цитата=цитата), self.assertRaises(ValueError):
                розбір['variants'][0]['colors'][0]['quote'] = цитата
                self.перевірити(розбір)

    def test_форма_коди_повнота(self):
        """Відхиляє чужі/повторні id, коди й неоднозначний JSON."""
        for поле, значення in [('row_id', 'чужий-id'), ('status', 'довільно'),
                              ('relation', 'alternatives'), ('unknown_reason', 'ambiguous')]:
            розбір = відоме(self.вхід)
            розбір[поле] = значення
            with self.subTest(поле=поле), self.assertRaises(ValueError):
                self.перевірити(розбір)
        розбір = відоме(self.вхід)
        розбір['variants'][0]['colors'][0]['code'] = 'вигаданий-код'
        with self.assertRaises(ValueError):
            self.перевірити(розбір)
        for записи in ([], [відоме(self.вхід)] * 2):
            with self.assertRaises(ValueError):
                П.перевірити_відповідь({'rows': записи}, [self.вхід], self.коди)
        for текст in ('{"rows":[],"rows":[]}', '{"rows":NaN}', '```json\n{}\n```'):
            with self.assertRaises(ValueError):
                П.читати_json(текст)
        self.перевірити(невідоме(self.вхід))

    def test_групи_варіантів(self):
        """Зберігає задані моделлю групи; код не ділить slash чи кому."""
        вхід = рядок('Кава/молочний, рубін/молочний,')
        розбір = {'row_id': вхід['row_id'], 'status': 'known', 'relation': 'alternatives',
            'unknown_reason': 'none', 'variants': [
                {'quote': 'Кава/молочний', 'colors': [{'code': 'brown', 'quote': 'Кава'}, {'code': 'milky', 'quote': 'молочний'}]},
                {'quote': 'рубін/молочний', 'colors': [{'code': 'red', 'quote': 'рубін'}, {'code': 'milky', 'quote': 'молочний'}]}]}
        результат = П.перевірити_відповідь({'rows': [розбір]}, [вхід], self.коди)[вхід['row_id']]
        self.assertGreater(результат['quote_utf8_spans'][1][1][0], результат['quote_utf8_spans'][0][1][0])
        розбір['variants'][0]['colors'][0]['quote'] = 'рубін'
        with self.assertRaises(ValueError):
            П.перевірити_відповідь({'rows': [розбір]}, [вхід], self.коди)

    def test_спільний_рядок_різні_джерела(self):
        """Один переклад не поширює довіру між двома входженнями."""
        вхід = self.вхід
        входження = {'occurrence_id': 'id-1#0', 'offer_id': 'id-1', **вхід,
                    'admission': 'unknown', 'reason': 'missing_structural_provenance', 'evidence_ref': None}
        структура = {'object_id': 'property-1', 'subject_id': 'id-1', 'kind': 'product_attribute',
                     'value': вхід['raw'], 'variant_id': None}
        перше = П.допустити(входження, структура, 'synthetic:product')
        друге = П.допустити(dict(входження, occurrence_id='id-1#1'), dict(структура, kind='review'), 'synthetic:review')
        розбір = self.перевірити(відоме(вхід))
        наслідки = П.приєднати({'occurrences': [перше, друге]}, розбір)
        self.assertEqual([н['state'] for н in наслідки], ['candidate', 'unknown'])
        self.assertEqual(наслідки[1]['variants'], [])
        with self.assertRaises(ValueError):
            П.допустити(входження, dict(структура, subject_id='id-2'), 'synthetic:other')
        with self.assertRaises(ValueError):
            П.допустити(входження, dict(структура, kind='variant_attribute'), 'synthetic:no-id')

    def test_походження_відбиток_артефакту(self):
        """Вимагає перевірений артефакт, його hash та точний object→offer."""
        вхід = {'occurrence_id': 'id-1#0', 'offer_id': 'id-1', 'product_url': 'https://example.test/p1', **self.вхід}
        маніфест = {'source': {'raw_sha256': 'synthetic'}, 'occurrences': [вхід]}
        артефакт = {'version': '5190-source-objects-v1', 'source_ref': вхід['product_url'],
            'capture': {'product': {'@type': 'Product', '@id': 'property-1', 'url': вхід['product_url'], 'color': self.вхід['raw']}},
            'records': [{'object_id': 'property-1', 'subject_id': 'id-1', 'kind': 'product_attribute',
                         'value': self.вхід['raw'], 'variant_id': None, 'capture_pointer': '/product'}]}
        П.зберегти(self.тека / 'source.json', артефакт)
        доказ = {'version': '5190-provenance-v1', 'raw_sha256': 'synthetic', 'entries': [
            {'occurrence_id': 'id-1#0', 'row_id': self.вхід['row_id'], 'artifact': 'source.json',
             'artifact_sha256': П.відбиток(П.байти_json(артефакт)), 'object_id': 'property-1', 'review_ref': 'synthetic:qa'}]}
        П.зберегти(self.тека / 'proof.json', доказ)
        self.assertEqual(П.походження(маніфест, self.тека / 'proof.json')['occurrences'][0]['admission'], 'admitted')
        артефакт['capture']['product']['@type'] = 'Review'
        П.зберегти(self.тека / 'source.json', артефакт)
        with self.assertRaises(ValueError):
            П.походження(маніфест, self.тека / 'proof.json')
        доказ['entries'][0]['artifact_sha256'] = П.відбиток(П.байти_json(артефакт))
        П.зберегти(self.тека / 'proof.json', доказ)
        with self.assertRaises(ValueError):
            П.походження(маніфест, self.тека / 'proof.json')  # Навіть із новим hash kind=product не переважує Review.

    def test_справжні_негативні_4750(self):
        """Звіряє два bare ~Розмір із raw; цитата відгуку не дає ознаки речі."""
        фікстура = json.loads((П.ДАНІ / 'негативні_4750.json').read_text(encoding='utf-8'))
        сирі = (П.КОРІНЬ / 'каталог_повний.xml.gz').read_bytes()
        self.assertEqual(П.відбиток(сирі), фікстура['raw_sha256'])
        за_ід = {р.get('id') + '@' + next((''.join(п.itertext()) for п in р.findall('param') if п.get('name') == 'магазин'), ''): р
                 for р in XML.fromstring(gzip.decompress(сирі)).iter('offer') if р.get('id') in ('ж-00363', 'ж-02350')}
        for приклад in фікстура['cases']:
            параметри = list(за_ід[приклад['offer_id']].findall('param'))
            for префікс in ('', 'trace_'):
                параметр = параметри[приклад[префікс + 'param_index']]
                поле = приклад['field'] if not префікс else приклад['trace_param_name']
                значення = приклад['raw'] if not префікс else приклад['trace_param_value']
                self.assertEqual((параметр.get('name'), ''.join(параметр.itertext())), (поле, значення))
            вхід = dict(приклад, **рядок(приклад['raw']), occurrence_id=приклад['offer_id'] + '#' + str(приклад['param_index']))
            структура = {'object_id': str(приклад['trace_param_index']), 'subject_id': приклад['offer_id'],
                         'kind': 'review', 'value': приклад['raw'], 'variant_id': None}
            перевірене = П.допустити(вхід, структура, приклад['review_ref'])
            self.assertEqual(перевірене['admission'], 'unknown')

    def test_повний_пілот_лише_підробний_транспорт(self):
        """Проводить 97 рядків/119 входжень через фікстуру, потім кеш без викликів."""
        маніфест = П.підготувати()
        self.assertEqual((len(маніфест['rows']), len(маніфест['occurrences'])), (97, 119))
        self.assertEqual(len(маніфест['source']['frozen40']), 40)
        self.assertTrue(all(в['admission'] == 'unknown' for в in маніфест['occurrences']))
        бачені = []
        def заглушка(тіло):
            """Повертає unknown для кожного id, не викликаючи мережі."""
            рядки = json.loads(тіло['messages'][1]['content'])['rows']
            бачені.extend(р['row_id'] for р in рядки)
            return відповідь([невідоме(р) for р in рядки])
        with self.assertRaises(ValueError):
            П.виконати(маніфест, self.тека, транспорт=заглушка)
        self.assertEqual(бачені, [])
        звіт = П.виконати(маніфест, self.тека, транспорт=заглушка, лише_переклад=True)
        self.assertEqual((len(бачені), len(set(бачені)), звіт['requests_this_run']), (97, 97, 49))
        self.assertEqual((звіт['admitted_occurrences'], звіт['unknown_provenance']), (0, 119))
        повтор = П.виконати(маніфест, self.тека, транспорт=заглушка, лише_переклад=True)
        self.assertEqual((повтор['cache_hits'], повтор['requests_this_run'], len(бачені)), (97, 0, 97))
        self.assertFalse((self.тека / '.5190.lock').exists())
        self.assertTrue(all(р['state'] == 'unknown' for р in json.loads((self.тека / 'входження.json').read_text(encoding='utf-8'))))
        шлях = next((self.тека / 'cache').glob('*.json'))
        кеш = json.loads(шлях.read_text(encoding='utf-8'))
        кеш['identity']['prompt_sha256'] = 'stale'
        П.зберегти(шлях, кеш)
        with self.assertRaises(ValueError):
            П.виконати(маніфест, self.тека, транспорт=заглушка, лише_переклад=True)
        self.assertEqual(len(бачені), 97)

    def test_час_пакета_збій_та_версії(self):
        """Облік часу чесний; невдала спроба не стає кешем і не повторюється."""
        вхід = self.вхід
        маніфест = {'source': {}, 'rows': [вхід, рядок('Інший рядок')], 'occurrences': []}
        def заглушка(тіло):
            """Дає синтетичний пакет з однозначною формою."""
            return відповідь([невідоме(р) for р in json.loads(тіло['messages'][1]['content'])['rows']])
        with patch.object(П.time, 'monotonic', side_effect=[10.0, 18.0]):
            П.виконати(маніфест, self.тека, транспорт=заглушка)
        результати = json.loads((self.тека / 'переклади.json').read_text(encoding='utf-8'))
        self.assertEqual([(р['batch_elapsed_s'], р['amortized_s']) for р in результати], [(8.0, 4.0)] * 2)
        версія = П.контракт()[2]
        for поле in ('model', 'schema_sha256', 'prompt_sha256', 'protocol'):
            self.assertNotEqual(П.ключ_кешу(вхід, версія), П.ключ_кешу(вхід, dict(версія, **{поле: 'stale'})))
        збійна = self.тека / 'збій'
        невипробувані = dict(маніфест, rows=[рядок('Окремий вхід 1'), рядок('Окремий вхід 2')])
        def обірвана(тіло):
            """Імітує обрізання відповіді за лімітом виходу."""
            дані = заглушка(тіло)
            дані['choices'][0]['finish_reason'] = 'length'
            return дані
        for транспорт, пакет in ((обірвана, 2), (заглушка, 1)):
            with self.assertRaises(ValueError):
                П.виконати(невипробувані, збійна, пакет=пакет, транспорт=транспорт)
        self.assertFalse((збійна / 'cache').exists())
        self.assertFalse((збійна / '.5190.lock').exists())

    def test_справжній_транспорт_і_проксі_без_повтору(self):
        """Передає фактичний Request runner до справжнього proxy у VM без сокетів."""
        тіло = П.запит([self.вхід], *П.контракт()[:2])
        бачені = []
        class Клієнт:
            """Заміщує лише HTTP I/O, зберігає фактичні метод, URL, headers і body."""
            def open(цей, запит, timeout):
                бачені.append(запит)
                дані = {'protocol': П.ПРОТОКОЛ_ПРОКСІ, 'post_retries': 0} if запит.get_method() == 'GET' else відповідь([невідоме(self.вхід)])
                return io.BytesIO(П.байти_json(дані))
        with patch.object(П.urllib.request, 'build_opener', return_value=Клієнт()):
            П.надіслати(тіло)
        self.assertEqual([р.get_method() for р in бачені], ['GET', 'POST'])
        self.assertEqual(бачені[0].full_url, 'http://127.0.0.1:1235/.well-known/lyusterko-5190')
        р = бачені[1]
        П.зберегти(self.тека / 'caller.json', {'method': р.get_method(), 'path': urlsplit(р.full_url).path,
            'headers': {к.lower(): з for к, з in р.header_items()}, 'body': р.data.decode('utf-8')})
        вихід = subprocess.check_output(['node', str(П.КОРІНЬ / 'аудит/ноутбук_стенд_2/тест_проксі_5190.js'),
                                        str(self.тека / 'caller.json')], text=True)
        self.assertEqual(json.loads(вихід), {'capability_posts': 0, 'once_posts': 1, 'ordinary_posts': 3})
        with patch.object(П.urllib.request, 'build_opener') as збудувати:
            збудувати.return_value.open.return_value = io.BytesIO(b'{"post_retries":2}')
            with self.assertRaises(ValueError):
                П.надіслати(тіло)
            self.assertEqual(збудувати.return_value.open.call_count, 1)  # До POST старого proxy не дійшло.

    def test_один_raw_між_теками_версіями_та_після_збою(self):
        """Новий output і prompt/model/schema не дають повтору вже посланого raw."""
        маніфест = {'source': {}, 'rows': [self.вхід], 'occurrences': []}
        def заглушка(тіло):
            """Імітує один успішний результат."""
            return відповідь([невідоме(self.вхід)])
        with patch.object(П, 'контракт', wraps=П.контракт) as контракт:
            первісний = П.контракт()
            self.assertEqual(П.виконати(маніфест, self.тека / 'а', транспорт=заглушка)['requests_this_run'], 1)
            with patch('builtins.print'):
                повтор = П.виконати(маніфест, self.тека / 'б', транспорт=lambda _: self.fail('Повтор POST'))
            self.assertEqual((повтор['cache_hits'], повтор['requests_this_run']), (1, 0))
            for поле in ('prompt_sha256', 'schema_sha256', 'model', 'protocol'):
                нова = dict(первісний[2], **{поле: 'changed'})
                контракт.return_value = (первісний[0], первісний[1] + '\n', нова, первісний[3])
                for вихід in ('а', 'новий-' + поле):
                    with self.subTest(поле=поле, вихід=вихід), self.assertRaises(ValueError):
                        П.виконати(маніфест, self.тека / вихід, транспорт=lambda _: self.fail('Неявний повтор'))
        інший = {'source': {}, 'rows': [рядок('Невизначена спроба')], 'occurrences': []}
        with self.assertRaises(OSError):
            П.виконати(інший, self.тека / 'обрив', транспорт=lambda _: (_ for _ in ()).throw(OSError('after accepted')))
        with self.assertRaises(ValueError):
            П.виконати(інший, self.тека / 'інша', транспорт=lambda _: self.fail('Повтор після обриву'))
        with П.Ж.відкрити([]):
            with self.assertRaises(FileExistsError):
                П.виконати(маніфест, self.тека / 'паралельний', транспорт=lambda _: self.fail('Конкурентний POST'))

    def test_явний_дозвіл_точній_історії_лише_раз(self):
        """Дозвіл із decision/reason/identity/prior attempts діє рівно один раз."""
        маніфест = {'source': {}, 'rows': [self.вхід], 'occurrences': []}
        попередня = {'row_id': self.вхід['row_id'], 'raw': self.вхід['raw'], 'attempts': [
            {'request_sha256': 'old-request', 'identity': {'protocol': 'old'}}]}
        with П.Ж.відкрити([попередня]):
            pass
        дозвіл = {'version': '5190-repeat-v1', 'authorization_id': 'fixture-decision',
            'decision_ref': 'fixture:explicit-decision', 'reason': 'Синтетичне рішення після збою',
            'target_identity_sha256': П.Ж.відбиток(П.контракт()[2]), 'rows': {self.вхід['row_id']: ['old-request']}}
        for хибний in (None, dict(дозвіл, rows={}), dict(дозвіл, target_identity_sha256='stale')):
            with self.assertRaises(ValueError):
                П.виконати(маніфест, self.тека / 'а', лише_переклад=True, дозвіл=хибний,
                           транспорт=lambda _: self.fail('Неповний дозвіл'))
        зіпсоване = dict(відоме(self.вхід), variants=[])
        звіт = П.виконати(маніфест, self.тека / 'а', лише_переклад=True, дозвіл=дозвіл,
                         транспорт=lambda _: відповідь([зіпсоване]))
        self.assertEqual((звіт['state'], звіт['rejected_rows'], звіт['requests_this_run']), ('partial', 1, 1))
        with self.assertRaises(ValueError):
            П.виконати(маніфест, self.тека / 'інша', лише_переклад=True, дозвіл=дозвіл,
                       транспорт=lambda _: self.fail('Повтор використаного дозволу'))

    def test_часткова_відповідь_кешує_сусіда_без_ремонту(self):
        """Некоректний рядок не втрачає валідний сусід і не стає unknown-відповіддю."""
        інший = рядок('Рядок із хибною формою')
        маніфест = {'source': {}, 'rows': [self.вхід, інший], 'occurrences': []}
        хибний = dict(відоме(інший), relation='alternatives')
        звіт = П.виконати(маніфест, self.тека / 'а', транспорт=lambda _: відповідь([відоме(self.вхід), хибний]))
        self.assertEqual((звіт['validated_rows'], звіт['rejected_rows'], звіт['model_unknown_rows']), (1, 1, 0))
        повтор = П.виконати(маніфест, self.тека / 'б', транспорт=lambda _: self.fail('Повтор часткового пакета'))
        self.assertEqual((повтор['cache_hits'], повтор['rejected_rows'], повтор['requests_this_run']), (1, 1, 0))
        for записи in ([відоме(self.вхід), хибний, хибний], [відоме(self.вхід), dict(хибний, row_id='чужий')]):
            результат = П.відповідь_пакета(відповідь(записи), маніфест['rows'], self.коди)
            self.assertEqual(set(результат['valid']), {self.вхід['row_id']})
            self.assertEqual(set(результат['rejected']), {інший['row_id']})

    def test_шість_фактичних_відповідей_і_схема(self):
        """Offline replay frozen93: 19 структурно придатних, п'ять відхилених; не якість кольору."""
        індекс = П.читати_json((П.ДАНІ / 'попередні_спроби.json').read_bytes())
        форма = Draft202012Validator(П.контракт()[0]['properties']['rows']['items'])
        валідні = відхилені = 0
        for доказ in індекс['records']:
            байти = (П.ДАНІ / доказ['file']).read_bytes()
            self.assertEqual(П.відбиток(байти), доказ['sha256'])
            запис = П.читати_json(байти)
            рядки = П.читати_json(запис['request']['messages'][1]['content'])['rows']
            with patch.object(П, 'МОДЕЛЬ', запис['identity']['model']):
                результат = П.відповідь_пакета(запис['response'], рядки, self.коди)
            валідні += len(результат['valid']); відхилені += len(результат['rejected'])
            for ряд in П.читати_json(запис['response']['choices'][0]['message']['content'])['rows']:
                self.assertEqual(форма.is_valid(ряд), ряд['row_id'] in результат['valid'])
        self.assertEqual((валідні, відхилені), (19, 5))
        тіло = П.запит([self.вхід, рядок('Другий')], *П.контракт()[:2])
        схема = тіло['response_format']['json_schema']['schema']
        self.assertEqual((схема['properties']['rows']['minItems'], схема['properties']['rows']['maxItems']), (2, 2))
        перевірка = Draft202012Validator(схема)
        self.assertFalse(перевірка.is_valid({'rows': [невідоме(self.вхід)]}))
        self.assertFalse(перевірка.is_valid({'rows': [невідоме(self.вхід), невідоме(рядок('Чужий'))]}))

    def test_історичний_дозвіл_і_джерельна_умова(self):
        """Звіряє всі відомі prior attempts; чинний повтор чекає джерельних доказів."""
        історія = self.реальна_історія()
        дозвіл = П.читати_json((П.ДАНІ / 'повтор_6152300721.json').read_bytes())
        self.assertEqual((len(історія), sum(len(р['attempts']) for р in історія)), (16, 24))
        with П.Ж.відкрити(історія) as журнал:
            for р in історія:
                журнал.перевірити_повтор(р, П.контракт()[2], дозвіл)
                with self.assertRaises(ValueError):
                    журнал.перевірити_повтор(р, П.контракт()[2], None)
        маніфест = {'source': {}, 'rows': [self.вхід], 'occurrences': [{'admission': 'unknown'}]}
        with self.assertRaisesRegex(ValueError, 'спершу підтвердити'):
            П.виконати(маніфест, self.тека / 'а', лише_переклад=True, дозвіл=дозвіл,
                       транспорт=lambda _: self.fail('До перевірки джерела'))


if __name__ == '__main__':
    unittest.main(verbosity=2)

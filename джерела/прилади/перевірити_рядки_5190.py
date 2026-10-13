"""Перевіряє offline протокол пілота 5190; жодного HTTP або моделі.

Підробна відповідь доводить тільки форму, cache/provenance та облік часу.
Не є перевіркою якості MamayLM, кольорових кодів, вікон або фото.
"""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as XML

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
        self.assertEqual((len(бачені), len(set(бачені)), звіт['requests_this_run']), (97, 97, 25))
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
        def обірвана(тіло):
            """Імітує обрізання відповіді за лімітом виходу."""
            дані = заглушка(тіло)
            дані['choices'][0]['finish_reason'] = 'length'
            return дані
        for транспорт, пакет in ((обірвана, 4), (заглушка, 1)):
            with self.assertRaises(ValueError):
                П.виконати(маніфест, збійна, пакет=пакет, транспорт=транспорт)
        self.assertFalse((збійна / 'cache').exists())
        self.assertFalse((збійна / '.5190.lock').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)

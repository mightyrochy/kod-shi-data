# -*- coding: utf-8 -*-
"""Стенд лічби «вхід суду з її слів» на малому дереві: стадії втрати, вхід суду, списки, обсяг сцен, таблиця читання
(без запуску продукту й без реальних записів).

Запуск: `python3 джерела/прилади/тест_корінь_е2_втрата_слова_вхід.py` з кореня репозиторію."""
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import корінь_е2_втрата_слова_вхід as К  # noqa: E402

ПАСПОРТ_ПОЛЯ = '''
ПОЛЯ_ПАСПОРТА = {
    "нагода": {"поле": "occasion", "вісь": ("occasion", "occasion")},
    "місце": {"поле": "place", "вісь": ("place", "place")},
    "формат": {"поле": "setting", "вісь": ("setting", "setting"), "мова": lambda м: м.перелік("setting")},
    "тривалість_год": {"поле": "duration_h"},
    "смуга_погоди": {"поле": "weather_band", "вісь": ("weather_band", "weather_band")},
    "бажання": {"поле": "wants"},
}
'''
ДРІТ = '''
ПОЛЯ_ВИПАДКУ = {"нагода": "occasion", "формат": "setting", "бажання": "wishes", "тривалість_год": "duration_h"}
_ВИПАДОК_У_ДНІ = {"місце": "place", "смуга_погоди": "weather_band"}
'''
ПОЛОМКИ = '''
ВХІД = ("сценарій.тривалість_год|поверхня: none", "сценарій.смуга_погоди: none_or_cold_suppresses_draped",
        "сценарій.нагода: sport_or_home")
'''


def дерево(тека):
    джерела = os.path.join(тека, 'джерела')
    os.makedirs(джерела)
    for ім, текст in (('паспорт_поля.py', ПАСПОРТ_ПОЛЯ), ('дріт_моделі.py', ДРІТ), ('поломки.py', ПОЛОМКИ)):
        with open(os.path.join(джерела, ім), 'w', encoding='utf-8') as ф:
            ф.write(текст)


def запис(**над):
    з = {'прогін': 'п', 'сцена': 'с1', 'прохід': 1, 'модель': 'м', 'оновлення': {}, 'схема': {'duration_h', 'setting', 'occasion',
         'place', 'weather_band', 'wants'}, 'розділи': {'case': {}, 'day': {}, 'person': {}, 'her_items': ''},
         'паспорт': {'тривалість_год': None, 'формат': 'невідомо', 'нагода': 'свято', 'місце': 'ресторан', 'смуга_погоди': None,
                     'бажання': [], 'слова': '', 'цитати_полів': {}, 'виміри': {}, 'звідки': {}},
         'діагноз': [], 'репліки': ['р'], 'розділи_з': 'промпт складання'}
    з.update(над)
    return з


def ряд(поле, уривок='її слова', рівень='пряме'):
    return {'репліка': 'р', 'поле': поле, 'уривок': уривок, 'рівень': рівень, 'примітка': ''}


class Реєстри(unittest.TestCase):
    def setUp(self):
        self.тека = tempfile.mkdtemp()
        дерево(self.тека)
        self.р = К.Реєстри(self.тека)

    def test_поля_з_коду(self):
        self.assertEqual(self.р.ключ('setting'), 'формат')
        self.assertEqual(self.р.вимір('setting'), 'setting')
        self.assertIsNone(self.р.ключ('нема'))

    def test_ключі_стилістки_з_двох_реєстрів(self):
        self.assertEqual(self.р.ключі_стилістки('setting'), {'setting'})
        self.assertEqual(self.р.ключі_стилістки('wants'), {'wants', 'wishes'})
        self.assertEqual(self.р.ключі_стилістки('weather_band'), {'weather_band'})

    def test_вхід_суду_з_літералів_вмісту_поломок(self):
        self.assertEqual(self.р.суд_укр, {'тривалість_год', 'поверхня', 'смуга_погоди', 'нагода'})
        self.assertIn('duration_h', self.р.суд)
        self.assertNotIn('setting', self.р.суд)


class Порожнє(unittest.TestCase):
    def test_порожнє(self):
        for в in (None, '', 'unknown', 'невідомо', [], {}, {'value': 'unknown'}, {'quote': 'q', 'value': None}, [None, '']):
            self.assertTrue(К.порожнє(в), в)
        for в in ('walk', 0.5, ['a'], {'value': 'outdoor'}):
            self.assertFalse(К.порожнє(в), в)


class Розбір(unittest.TestCase):
    def test_update_з_огорожі_і_без(self):
        self.assertEqual(К.відповідь_update('```json\n{"update": {"a": 1}}\n```'), {'a': 1})
        self.assertEqual(К.відповідь_update('{"update": {"b": 2}}'), {'b': 2})
        self.assertEqual(К.відповідь_update('не json'), {})

    def test_репліка_і_схема(self):
        self.assertEqual(К.перша_репліка('x "her_new_message": "ну ось\\n" y'), 'ну ось\n')
        self.assertEqual(К.схема_з_промпта('"- setting — де" "- duration_h — скільки"'), {'setting', 'duration_h'})

    def test_об_єкт_за_ключем_з_рядками_з_дужками(self):
        текст = '{"case": {"a": "} не кінець", "b": {"c": 1}}, "day": {"d": 2}}'
        self.assertEqual(К.об_єкт_за_ключем(текст, 'case')[0], {'a': '} не кінець', 'b': {'c': 1}})
        self.assertEqual(К.об_єкт_за_ключем(текст, 'day')[0], {'d': 2})


class Стадії(unittest.TestCase):
    def setUp(self):
        self.тека = tempfile.mkdtemp()
        дерево(self.тека)
        self.р = К.Реєстри(self.тека)
        self.схема = {'duration_h', 'setting', 'occasion', 'place', 'weather_band', 'wants'}

    def стадія(self, з, т):
        return К.стадія(self.р, з, 'р', т, self.схема)[0]

    def test_поза_схемою(self):
        self.assertEqual(self.стадія(запис(), ряд('день')), 'схема')
        self.assertEqual(self.стадія(запис(), ряд('нема_в_схемі')), 'схема')

    def test_модель_не_записала(self):
        з = запис(оновлення={'р': [{'occasion': {'value': 'wedding'}}]})
        self.assertEqual(self.стадія(з, ряд('setting')), 'модель')

    def test_писач_втратив(self):
        з = запис(оновлення={'р': [{'setting': {'quote': 'надворі', 'value': 'outdoor'}}]})
        self.assertEqual(self.стадія(з, ряд('setting')), 'писач')

    def test_читач_не_передав_стилістці(self):
        з = запис(оновлення={'р': [{'place': {'value': 'x'}}]})
        з['паспорт']['місце'] = 'ресторан'
        self.assertEqual(self.стадія(з, ряд('place')), 'читач')

    def test_дійшло(self):
        з = запис(оновлення={'р': [{'place': {'value': 'x'}}]})
        з['розділи']['day'] = {'place': 'restaurant'}
        self.assertEqual(self.стадія(з, ряд('place')), 'дійшло')

    def test_без_запису_відповіді_моделі(self):
        self.assertEqual(self.стадія(запис(), ряд('setting')), 'модель_чи_писач')

    def test_без_паспорта(self):
        з = запис(паспорт=None, розділи=None, оновлення={'р': [{'place': {'value': 'x'}}]})
        self.assertEqual(self.стадія(з, ряд('place')), 'писач_чи_читач')
        з = запис(паспорт=None, розділи=None, оновлення={'р': [{}]})
        self.assertEqual(self.стадія(з, ряд('place')), 'модель')     # модель не записала — паспорта не потрібно

    def test_цитата_моделі_довша_за_уривок_так_само_збіг(self):
        з = запис(оновлення={'р': [{'wants': {'quote': 'надворі без підборів', 'value': ['no_heel']}}]})
        з['розділи']['case'] = {'wishes': ['no_heel'], 'field_quotes': {'wishes': 'надворі без підборів'}}
        з['паспорт']['слова'] = 'надворі без підборів'
        self.assertEqual(self.стадія(з, ряд('wants', 'без підборів')), 'дійшло')

    def test_суд_без_входу_none_нижче_за_дійшло(self):
        з = запис(діагноз=['control · no_input=K-SHO-16=сценарій.тривалість_год|поверхня: none | R-X=особа.бік_b.вхід: y'])
        з['розділи']['case'] = {'duration_h': 0.5}
        self.assertEqual(self.стадія(з, ряд('duration_h')), 'читач')

    def test_холод_не_брак_входу_коли_паспорт_має_смугу(self):
        з = запис(діагноз=['control · no_input=K-OUT-33=сценарій.смуга_погоди: none_or_cold_suppresses_draped'])
        з['розділи']['day'] = {'weather_band': 'deep_frost'}
        з['паспорт']['смуга_погоди'] = 'deep_frost'
        self.assertEqual(self.стадія(з, ряд('weather_band')), 'дійшло')

    def test_брак_смуги_у_паспорті_і_в_діагнозі_читач(self):
        з = запис(діагноз=['control · no_input=K-OUT-33=сценарій.смуга_погоди: none_or_cold_suppresses_draped'])
        з['розділи']['day'] = {'weather_band': 'cold'}
        self.assertEqual(self.стадія(з, ряд('weather_band')), 'читач')

    def test_інша_причина_не_брак_входу(self):
        з = запис(діагноз=['control · no_input=X=сценарій.нагода: sport_or_home'])
        з['розділи']['case'] = {'occasion': 'sport'}
        self.assertEqual(self.стадія(з, ряд('occasion')), 'дійшло')

    def test_список_лічиться_по_уривку(self):
        з = запис(оновлення={'р': [{'wants': {'quote': 'без підборів', 'value': ['no_heel']}}]})
        з['розділи']['case'] = {'wishes': ['no_heel'], 'field_quotes': {'wishes': 'тільки не чорне'}}
        з['паспорт']['слова'] = 'тільки не чорне'
        self.assertEqual(self.стадія(з, ряд('wants', 'без підборів')), 'писач')
        з['паспорт']['бажання'] = 'без підборів'
        з['паспорт']['слова'] = 'без підборів'
        з['розділи']['case']['field_quotes']['wishes'] = 'без підборів'
        self.assertEqual(self.стадія(з, ряд('wants', 'без підборів')), 'дійшло')


class Зведення(unittest.TestCase):
    def рядок(self, прохід, стадія, поле='setting', уривок='надворі', рівень='пряме'):
        return {'запис': ('п', 'с1', прохід), 'поле': поле, 'уривок': уривок, 'рівень': рівень, 'стадія': стадія}

    def test_сцена_дійшла_лише_коли_дійшла_в_усіх_проходах(self):
        з = К.згорнути([self.рядок(1, 'дійшло'), self.рядок(2, 'писач')])
        self.assertEqual((len(з['setting']['назвала']), len(з['setting']['дійшло'])), (1, 0))
        self.assertEqual(len(з['setting']['втрата']['писач']), 1)
        self.assertEqual(К.місць(з), 1)

    def test_виведене_не_лічиться_у_назвала(self):
        з = К.згорнути([self.рядок(1, 'модель', 'surface', 'сніг', 'виведене')])
        self.assertEqual((len(з['surface']['назвала']), len(з['surface']['виведене'])), (0, 1))
        self.assertEqual(К.місць(з), 0)

    def test_списки_по_елементах(self):
        з = К.згорнути([self.рядок(1, 'дійшло', 'wants', 'а'), self.рядок(1, 'писач', 'wants', 'б')])
        self.assertEqual((len(з['wants']['назвала']), len(з['wants']['дійшло'])), (2, 1))


class Записи(unittest.TestCase):
    def test_нічна_сцена_від_файлів_до_лічби(self):
        тека = tempfile.mkdtemp()
        дерево(тека)
        р = К.Реєстри(тека)
        ніч = os.path.join(тека, 'ніч')
        в = os.path.join(ніч, 'с1', 'VIDPOVIDI')
        os.makedirs(в)
        промпт1 = ('── ПРОМПТ (1 симв.) ──\n{"x": 1, "her_new_message": "в суботу надворі", "codes": "update field codes '
                   '(setting, occasion)"}\n── ВІДПОВІДЬ ──\n{"update": {"setting": {"quote": "надворі", "value": "outdoor"}}}')
        складання = ('── ПРОМПТ (1 симв.) ──\n{"outfits_wanted": 1, "case":{"event":"е","occasion":"wedding"},'
                     '"day":{"place":"x"}}\n── ВІДПОВІДЬ ──\n{}')
        for ім, текст in (('seed3_01_мовний_шар_хід_розмови.txt', промпт1), ('seed3_02_ПАКЕТ_V1_ОБРАЗИ_V1.txt', складання)):
            with open(os.path.join(в, ім), 'w', encoding='utf-8') as ф:
                ф.write(текст)
        записи = К.записи_нічного(ніч)
        self.assertEqual(len(записи), 1)
        з = записи[0]
        self.assertEqual(з['репліки'], ['в суботу надворі'])
        self.assertEqual(з['розділи']['case']['occasion'], 'wedding')
        таблиця = {'в суботу надворі': [ряд('день', 'в суботу'), ряд('setting', 'надворі'), ряд('place', 'надворі', 'виведене')]}
        рядки, без = К.лічба(записи, таблиця, р)
        self.assertEqual(без, set())
        за_полем = {x['поле']: x['стадія'] for x in рядки}
        # `place` нема в схемі синтетичного промпта; `setting` модель записала, а діагнозу сторінки (паспорта) нема —
        # писач чи читач не розрізнено
        self.assertEqual(за_полем, {'день': 'схема', 'setting': 'писач_чи_читач', 'place': 'схема'})

    def test_репліка_без_рядка_читання_не_мовчить(self):
        з = запис(репліки=['невідома репліка'], оновлення={'невідома репліка': [{}]})
        рядки, без = К.лічба([з], {}, К.Реєстри(self._дерево()))
        self.assertEqual((рядки, без), ([], {'невідома репліка'}))

    def _дерево(self):
        тека = tempfile.mkdtemp()
        дерево(тека)
        return тека


class Читання(unittest.TestCase):
    def test_невідомий_рівень_зупиняє(self):
        тека = tempfile.mkdtemp()
        with open(os.path.join(тека, 'читання.tsv'), 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f, delimiter='\t')
            w.writerow(['репліка', 'поле', 'уривок', 'рівень', 'примітка'])
            w.writerow(['р', 'setting', 'у', 'щось', ''])
        with self.assertRaises(SystemExit):
            К.читання(тека)

    def test_таблиця_за_реплікою(self):
        тека = tempfile.mkdtemp()
        with open(os.path.join(тека, 'читання.tsv'), 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f, delimiter='\t')
            w.writerow(['репліка', 'поле', 'уривок', 'рівень', 'примітка'])
            w.writerow(['р', 'setting', 'у', 'пряме', ''])
            w.writerow(['р', 'place', 'у', 'виведене', ''])
        self.assertEqual([x['поле'] for x in К.читання(тека)['р']], ['setting', 'place'])


if __name__ == '__main__':
    unittest.main()

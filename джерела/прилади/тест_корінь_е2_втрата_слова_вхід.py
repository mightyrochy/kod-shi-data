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
    "день_тижня": {"поле": "weekday", "вимір": ("weekday", {}, False)},
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

    def test_холод_без_паспорта_не_лічиться_бракум_входу(self):
        з = запис(паспорт=None, паспорта_нема=True, діагноз=['control · no_input=K-OUT-33=сценарій.смуга_погоди: none_or_cold_x'],
                  оновлення={'р': [{'weather_band': 'cold'}]})
        з['розділи']['day'] = {'weather_band': 'cold'}
        self.assertEqual(self.стадія(з, ряд('weather_band')), 'дійшло')

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

    # ── #4102: `день` і `як_носить` — поля схеми (`weekday`, `wear`), стадії ті самі, що в решти ──
    СХЕМА_ПІСЛЯ = {'duration_h', 'setting', 'occasion', 'place', 'weather_band', 'wants', 'weekday', 'wear'}

    def test_день_у_схемі_лічиться_стадіями(self):
        з = запис(схема=self.СХЕМА_ПІСЛЯ)
        self.assertEqual(self.стадія(з, ряд('день', 'в суботу')), 'модель_чи_писач')   # відповідей моделі не записано
        з = запис(схема=self.СХЕМА_ПІСЛЯ, оновлення={'р': [{'occasion': {'value': 'x'}}]})
        self.assertEqual(self.стадія(з, ряд('день', 'в суботу')), 'модель')
        з['оновлення'] = {'р': [{'weekday': {'quote': 'в суботу', 'value': 'saturday'}}]}
        self.assertEqual(self.стадія(з, ряд('день', 'в суботу')), 'писач')
        з['паспорт']['день_тижня'] = 'saturday'
        self.assertEqual(self.стадія(з, ряд('день', 'в суботу')), 'читач')
        з['розділи']['day'] = {'weekday': 'saturday'}
        self.assertEqual(self.стадія(з, ряд('день', 'в суботу')), 'дійшло')

    def test_день_поза_схемою_лишається_схемою(self):
        з = запис(оновлення={'р': [{'weekday': {'value': 'saturday'}}]})        # схема запису — до #4102
        self.assertEqual(self.стадія(з, ряд('день', 'в суботу')), 'схема')

    def test_як_носить_елементом_речі(self):
        з = запис(схема=self.СХЕМА_ПІСЛЯ)
        ц = 'шарфом під підборіддям'
        з['оновлення'] = {'р': [{'wants': [{'quote': 'шарф', 'slot': 'scarf'}]}]}
        self.assertEqual(self.стадія(з, ряд('як_носить', 'під підборіддям')), 'модель')
        з['оновлення'] = {'р': [{'wants': [{'quote': ц, 'wear': {'value': 'near_face'}}]}]}
        self.assertEqual(self.стадія(з, ряд('як_носить', 'під підборіддям')), 'писач')
        з['паспорт']['бажання'] = [{'як_носить': 'біля_обличчя', 'цитата': ц}]
        self.assertEqual(self.стадія(з, ряд('як_носить', 'під підборіддям')), 'читач')
        з['розділи']['case'] = {'wishes': [{'wear': 'near_face', 'quote': ц}]}
        self.assertEqual(self.стадія(з, ряд('як_носить', 'під підборіддям')), 'дійшло')

    def test_схема_з_промпта_бере_ознаку_речі_wear(self):
        п = '"update field codes (occasion, weekday, wants)", "  · wear — how she wears it; codes", "  · travel — she is away"'
        self.assertEqual(К.схема_з_промпта(п), {'occasion', 'weekday', 'wants', 'wear'})   # `travel` — код, не поле

    # ── сусіднє поле того самого ходу (дошка 16183) ──
    РЕПЛІКА = 'Йду на вечерю в ресторан, хочу намисто'

    def сусід(self, **над):
        з = запис(оновлення={self.РЕПЛІКА: [{'occasion': {'quote': 'вечерю в ресторан', 'value': 'festive_dinner'}}]},
                  репліки=[self.РЕПЛІКА])
        з['паспорт'].update({'нагода': None, 'подія': 'вечерю в ресторан'})
        з['розділи']['case'] = {'event': 'вечерю в ресторан'}
        з.update(над)
        return з

    def стадія_сусіда(self, з):
        return К.стадія(self.р, з, self.РЕПЛІКА, ряд('occasion', 'Йду на вечерю'), self.схема)[0]

    def test_слово_дійшло_сусіднім_полем_не_писач(self):
        self.assertEqual(self.стадія_сусіда(self.сусід()), 'дійшло')

    def test_слово_лише_в_паспорті_сусіднього_поля_читач(self):
        з = self.сусід()
        з['розділи']['case'] = {}
        self.assertEqual(self.стадія_сусіда(з), 'читач')

    def test_слово_ніде_не_лежить_лишається_писачем(self):
        з = self.сусід()
        з['паспорт']['подія'] = None
        з['розділи']['case'] = {'place': 'restaurant'}
        self.assertEqual(self.стадія_сусіда(з), 'писач')

    def test_уся_репліка_у_чужому_ключі_не_доводить_дійшло(self):
        з = self.сусід()
        з['паспорт']['подія'] = self.РЕПЛІКА
        з['розділи']['case'] = {'event': self.РЕПЛІКА}
        self.assertEqual(self.стадія_сусіда(з), 'писач')

    def test_модель_не_писала_поля_сусід_не_рятує(self):
        з = self.сусід(оновлення={self.РЕПЛІКА: [{'place': {'value': 'x'}}]})
        self.assertEqual(self.стадія_сусіда(з), 'модель')

    def test_суд_без_входу_нижче_за_слово_сусіда(self):
        з = self.сусід(діагноз=['no_input=K-1=сценарій.нагода: none'])
        self.assertEqual(self.стадія_сусіда(з), 'читач')


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

    def test_gemini_обміни_до_записів_і_стадій(self):
        тека = tempfile.mkdtemp()
        дерево(тека)
        р = К.Реєстри(тека)
        сцена = os.path.join(тека, 'модель-м', 'стенд', 'службове', 'с1')
        os.makedirs(сцена)

        def обмін(прохід, промпт, відповідь, статус=200):
            запит = json.dumps({'model': 'м', 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': промпт}]}]})
            пов = json.dumps({'content': [{'type': 'text', 'text': відповідь}]})
            return {'початок': 'т', 'прохід': прохід, 'запит': запит, 'статус': статус, 'відповідь': пов}
        чат = '{"x": 1, "her_new_message": "в суботу надворі", "codes": "update field codes (setting, occasion)"}'
        складання = '{"outfits_wanted": 1, "case":{"event":"е","occasion":"wedding"},"day":{"place":"x"}}'
        рядки = [обмін(1, чат, '{"update": {"setting": {"quote": "надворі", "value": "outdoor"}}}'),
                 обмін(1, складання, '{}'),
                 обмін(2, чат, '{"update": {"setting": {"quote": "надворі", "value": "outdoor"}}}'),   # складання не дійшло
                 обмін(3, чат, '', 502)]                                                                # без відповіді моделі
        with open(os.path.join(сцена, 'обміни.jsonl'), 'w', encoding='utf-8') as ф:
            ф.write('\n'.join(json.dumps(x, ensure_ascii=False) for x in рядки) + '\n')
        with open(os.path.join(сцена, 'руки.jsonl'), 'w', encoding='utf-8') as ф:
            ф.write(json.dumps({'прохід': 1, 'поломка_руки_2': {'діагноз': ['control · no_input=K-OUT-33=сценарій.смуга_погоди: none_or_cold_x']}}) + '\n')
        записи, не_виміряно = К.записи_gemini(тека)
        self.assertEqual([(з['прогін'], з['прохід']) for з in записи], [('модель-м', 1), ('модель-м', 2)])
        self.assertEqual([к for к, _ in не_виміряно], [('модель-м', 'с1', 3)])
        self.assertTrue(all(з['паспорта_нема'] for з in записи))
        таблиця = {'в суботу надворі': [ряд('setting', 'надворі'), ряд('weather_band', 'мороз')]}
        за = {(x['запис'][2], x['поле']): x['стадія'] for x in К.лічба(записи, таблиця, р)[0]}
        # прохід 1: setting модель написала, стилістка його не отримала — паспорта нема, писач чи читач не розрізнено;
        # weather_band поза схемою синтетичного промпта. Прохід 2: складання образів у записі нема.
        self.assertEqual(за, {(1, 'setting'): 'писач_чи_читач', (1, 'weather_band'): 'схема',
                              (2, 'setting'): 'складання_нема', (2, 'weather_band'): 'схема'})

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

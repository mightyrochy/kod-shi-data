import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'джерела' / 'прилади'))
import корінь_пк_слово_дослівно as прилад


class Журнал(unittest.TestCase):
    def test_збіг_та_відхилення(self):
        одиниця = dict(прилад.одиниці_тексту("Правило (власник 02.11): точний текст.")[0], файл="а.md")
        журнал = ('- **02.11.2026 10:00 UTC**: «Правило: точний текст.»\n'
                  '- **02.11.2026 11:00 UTC**: «Так» → `а.md`: «Правило: точний текст.»')
        def пункт(текст, дані=None):
            return прилад.оцінити(одиниця, дані or {}, {"02.11"}, текст)[0]

        self.assertIsNone(пункт(журнал))
        self.assertEqual(пункт(журнал.replace('точний', 'інший', 1)), 'п.1')
        self.assertEqual(пункт(журнал.replace('02.11.2026 10:', '01.11.2026 10:')), 'п.1')
        self.assertEqual(пункт(журнал.replace('→ `а.md`', '→ `б.md`')), 'п.1')
        self.assertEqual(пункт(журнал.replace('«Правило: точний текст.»', '«інше»', 1)), 'п.1')
        дані = {('а.md', одиниця['ключ']): {'вердикт': 'Ш'}}
        self.assertEqual(пункт(журнал, дані), 'п.1')


if __name__ == '__main__':
    unittest.main()

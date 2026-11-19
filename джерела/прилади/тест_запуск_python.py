"""Перевіряє транспорт на Windows із чужим кодуванням, ізоляцією й порожніми відповідями."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from запуск_python import запустити_python


class Транспорт(unittest.TestCase):
    """Контракти текстового й байтового запуску, діагнозу та коду виходу."""

    def test_кодування(self):
        """Дочірній і читач узгоджені попри змінні середовища й -I."""
        середовище = dict(os.environ, PYTHONUTF8='0', PYTHONIOENCODING='cp1251')
        for прапорці in ([], ['-I']):
            for текст in (False, True):
                with self.subTest(прапорці=прапорці, текст=текст):
                    р = запустити_python([sys.executable, *прапорці, '-c',
                                          "import sys; print('їжачок ґанок 🦔'); print('чому 🦔', file=sys.stderr)"],
                                         capture_output=True, text=текст, env=середовище, потрібен_вивід=True)
                    self.assertEqual(р.returncode, 0)
                    self.assertEqual(р.stdout, 'їжачок ґанок 🦔\n' if текст else 'їжачок ґанок 🦔\r\n'.encode()
                                     if os.name == 'nt' else 'їжачок ґанок 🦔\n'.encode())
                    self.assertIn('чому 🦔' if текст else 'чому 🦔'.encode(), р.stderr)

    def test_діагноз(self):
        """Порожній успіх і невдалий процес називають код та stderr, не NoneType."""
        for код in (0, 7):
            with self.subTest(код=код), self.assertRaisesRegex(subprocess.SubprocessError,
                    f'код виходу {код}; stdout: порожній; stderr: першопричина'):
                запустити_python([sys.executable, '-I', '-c',
                    f"import sys; print('першопричина', file=sys.stderr); sys.exit({код})"],
                    capture_output=True, text=True, потрібен_вивід=True)

    def test_порожній_дозволений(self):
        """Проба без текстового протоколу може звітувати лише кодом."""
        р = запустити_python([sys.executable, '-c', 'pass'], capture_output=True, text=True)
        self.assertEqual((р.returncode, р.stdout, р.stderr), (0, '', ''))

    def test_байти_не_utf8(self):
        """Помилка декодера приходить читачеві з кодом і stderr."""
        with self.assertRaisesRegex(subprocess.SubprocessError, 'код виходу 0; не UTF-8:'):
            запустити_python([sys.executable, '-c', "import sys; sys.stdout.buffer.write(bytes([255]))"],
                             capture_output=True, text=True)

    def test_захист_транспорту(self):
        """Спільний транспорт копіюється з голови, а його зміна з продуктом лишається червоною."""
        import стенд_храповика_кореня as стенд
        транспорт = Path(__file__).with_name('запуск_python.py').read_text(encoding='utf-8')
        база = {
            'аудит/корені/Проба.md': 'прилад: джерела/прилади/лічба.py\nбаза: джерела/код.txt\n',
            'джерела/прилади/лічба.py': 'from запуск_python import запустити_python\n' + стенд.прилад(),
            'джерела/прилади/запуск_python.py': транспорт,
            'джерела/код.txt': 'МІСЦЕ\n',
        }
        зміна = {'джерела/прилади/запуск_python.py': транспорт + '\n# Проба зміни транспорту.\n'}
        код, текст = стенд.прогнати(база, зміна, стенд.ХРАПОВИК)
        self.assertEqual(код, 0, текст)
        self.assertIn('місць 1 → 1', текст)
        код, текст = стенд.прогнати(база, {**зміна, 'джерела/продукт.py': '# Зміна продукту.\n'}, стенд.ХРАПОВИК)
        self.assertNotEqual(код, 0, текст)
        self.assertIn('прилад і виправлення — різними PR', текст)
        база['джерела/прилади/лічба.py'] = 'import інший\n' + стенд.прилад()
        база['джерела/прилади/інший.py'] = ''
        код, текст = стенд.прогнати(база, {'джерела/код.txt': 'МІСЦЕ\n\n'}, стенд.ХРАПОВИК)
        self.assertNotEqual(код, 0, текст)
        self.assertIn('назви в «база:» паспорта', текст)

    def test_перелік_команд(self):
        """Команди переліку, зокрема && та -I, проходять тим самим транспортом."""
        import tempfile
        import корінь_пк_дотримання as прилад
        with tempfile.TemporaryDirectory() as тека:
            Path(тека, 'добре.py').write_text("print('їжачок 🦔')", encoding='utf-8')
            Path(тека, 'збій.py').write_text("import sys; print('причина 🦔', file=sys.stderr); sys.exit(7)", encoding='utf-8')
            команди = {'одна': 'python3 -I добре.py', 'дві': 'python3 добре.py && python3 -I добре.py',
                       'збій': 'python3 -I збій.py && python3 добре.py'}
            self.assertEqual(прилад.запустити_проби(команди, тека), {'одна': True, 'дві': True, 'збій': False})


if __name__ == '__main__':
    unittest.main()

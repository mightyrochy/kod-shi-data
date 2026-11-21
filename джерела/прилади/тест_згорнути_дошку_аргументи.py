# -*- coding: utf-8 -*-
"""Тест розбору аргументів `згорнути_дошку.py`: `--help`/`-h`, невідомий аргумент, `--лише-перевірити` і згортання.

Перевіряє поведінку приладу запуском у тимчасовій теці (без читання тексту коду):
- `--help` і `-h` друкують довідку з шапки приладу, виходять з кодом 0 і не змінюють файлів на диску;
- невідомий прапорець чи позиційний аргумент дає помилку `argparse` (код 2) і не змінює файлів на диску;
- `--лише-перевірити` (з текою `аудит/дошка/` і без неї) зберігає звичний вивід і нічого не пише на диск;
- запуск без аргументів згортає файл у `аудит/БЕКЛОГ.md` і видаляє його з `аудит/дошка/`.

Запуск: python3 джерела/прилади/тест_згорнути_дошку_аргументи.py
"""
import os
import shutil
import sys
import tempfile
import unittest

ТУТ = os.path.dirname(os.path.abspath(__file__))
if ТУТ not in sys.path:
    sys.path.insert(0, ТУТ)
from запуск_python import запустити_python

ПРИЛАД = os.path.join(ТУТ, 'згорнути_дошку.py')
ПОЛЯ = os.path.join(ТУТ, 'дошка_поля.py')

ДОШКА_ПОЧАТОК = (
    '# Дошка\n\n'
    '| № | джерело | вага | статус | доказ | файли | команда |\n'
    '|---|---|---|---|---|---|---|\n'
    '| 1 | джерело 1 | низька | **ВІДКРИТО** · факт | доказ | файл | команда |\n'
    '| 2 | джерело 2 | низька | **ЗАКРИТО #7** · факт | доказ | файл | команда |\n'
)

НОВИЙ_РЯДОК = (
    '| 16997 | диспетчер · симптом '
    '<!-- дошка: дата=2026-11-21; рід=процес; попередник=ні; механізм=інше; корінь=жоден --> '
    '| середня | **ВІДКРИТО** · виявлено: диспетчер; внесено: давнє | доказ | файл | команда |\n'
)


def створити_пісочницю(з_файлом=True):
    """Створює тимчасову копію приладу з мінімальною дошкою й опційним файлом у `аудит/дошка/`."""
    тека = tempfile.mkdtemp(prefix='згорнути_дошку_аргументи_')
    прилади = os.path.join(тека, 'джерела', 'прилади')
    os.makedirs(прилади)
    шлях_приладу = os.path.join(прилади, 'згорнути_дошку.py')
    shutil.copy(ПРИЛАД, шлях_приладу)
    shutil.copy(ПОЛЯ, os.path.join(прилади, 'дошка_поля.py'))
    аудит = os.path.join(тека, 'аудит')
    os.makedirs(аудит)
    дошка = os.path.join(аудит, 'БЕКЛОГ.md')
    with open(дошка, 'w', encoding='utf-8') as ф:
        ф.write(ДОШКА_ПОЧАТОК)
    файл_дошки = os.path.join(аудит, 'дошка', 'гілка.md')
    if з_файлом:
        os.makedirs(os.path.dirname(файл_дошки))
        with open(файл_дошки, 'w', encoding='utf-8') as ф:
            ф.write(НОВИЙ_РЯДОК)
    return тека, шлях_приладу, дошка, файл_дошки


class АргументиЗгорнутиДошку(unittest.TestCase):
    """Перевіряє CLI-аргументи `згорнути_дошку.py` у тимчасовій теці."""

    def _перевірити_без_запису(self, дошка, файл_дошки):
        """Звіряє, що дошка й файл у `аудит/дошка/` залишились побайтово незмінними."""
        with open(дошка, encoding='utf-8') as ф:
            self.assertEqual(ф.read(), ДОШКА_ПОЧАТОК)
        self.assertTrue(os.path.isfile(файл_дошки))
        with open(файл_дошки, encoding='utf-8') as ф:
            self.assertEqual(ф.read(), НОВИЙ_РЯДОК)

    def test_довідка(self):
        """`--help` і `-h` друкують довідку з шапки, дають код 0 і не чіпають файлів."""
        for прапорець in ('--help', '-h'):
            with self.subTest(прапорець=прапорець):
                тека, шлях_приладу, дошка, файл_дошки = створити_пісочницю(з_файлом=True)
                try:
                    р = запустити_python([sys.executable, шлях_приладу, прапорець],
                                         cwd=тека, capture_output=True, text=True)
                    self.assertEqual(р.returncode, 0, msg=р.stderr)
                    self.assertEqual(р.stderr, '')
                    self.assertIn('--лише-перевірити', р.stdout)
                    self.assertIn('ЗГОРТАННЯ ДОШКИ', р.stdout)
                    self.assertIn('ЗАПУСК', р.stdout)
                    self._перевірити_без_запису(дошка, файл_дошки)
                finally:
                    shutil.rmtree(тека, ignore_errors=True)

    def test_невідомий_аргумент(self):
        """Невідомий прапорець або позиційний аргумент дає код 2 і не згортає дошки."""
        for зайвий in ('--нема-такого', 'зайвий'):
            with self.subTest(аргумент=зайвий):
                тека, шлях_приладу, дошка, файл_дошки = створити_пісочницю(з_файлом=True)
                try:
                    р = запустити_python([sys.executable, шлях_приладу, зайвий],
                                         cwd=тека, capture_output=True, text=True)
                    self.assertEqual(р.returncode, 2)
                    self.assertEqual(р.stdout, '')
                    self.assertIn(зайвий, р.stderr)
                    self._перевірити_без_запису(дошка, файл_дошки)
                finally:
                    shutil.rmtree(тека, ignore_errors=True)

    def test_лише_перевірити(self):
        """`--лише-перевірити` зберігає чинний вивід (з текою й без неї) і нічого не пише."""
        тека, шлях_приладу, дошка, файл_дошки = створити_пісочницю(з_файлом=True)
        try:
            for прапорці_py in ([], ['-I']):
                with self.subTest(режим='з_файлом', прапорці_py=прапорці_py):
                    р = запустити_python([sys.executable, *прапорці_py, шлях_приладу, '--лише-перевірити'],
                                         cwd=тека, capture_output=True, text=True)
                    self.assertEqual(р.returncode, 0, msg=р.stderr)
                    self.assertEqual(р.stderr, '')
                    self.assertEqual(
                        р.stdout.strip(),
                        'файлів 1, згорнуто 1; нових рядків 1, замін 0, змін стану 0, вже було 0; помилок 0',
                    )
                    self._перевірити_без_запису(дошка, файл_дошки)
        finally:
            shutil.rmtree(тека, ignore_errors=True)

        тека, шлях_приладу, дошка, _ = створити_пісочницю(з_файлом=False)
        try:
            р = запустити_python([sys.executable, шлях_приладу, '--лише-перевірити'],
                                 cwd=тека, capture_output=True, text=True)
            self.assertEqual(р.returncode, 0, msg=р.stderr)
            self.assertEqual(р.stderr, '')
            self.assertEqual(р.stdout.strip(), 'аудит/дошка/ нема — нічого згортати')
            with open(дошка, encoding='utf-8') as ф:
                self.assertEqual(ф.read(), ДОШКА_ПОЧАТОК)
        finally:
            shutil.rmtree(тека, ignore_errors=True)

    def test_без_аргументів_згортає(self):
        """Без аргументів прилад згортає файл у дошку й видаляє його, як і раніше."""
        тека, шлях_приладу, дошка, файл_дошки = створити_пісочницю(з_файлом=True)
        try:
            р = запустити_python([sys.executable, шлях_приладу], cwd=тека, capture_output=True, text=True)
            self.assertEqual(р.returncode, 0, msg=р.stderr)
            self.assertEqual(р.stderr, '')
            self.assertEqual(
                р.stdout.strip(),
                'файлів 1, згорнуто 1; нових рядків 1, замін 0, змін стану 0, вже було 0; помилок 0',
            )
            self.assertFalse(os.path.exists(файл_дошки))
            with open(дошка, encoding='utf-8') as ф:
                згорнута = ф.read()
            self.assertIn(НОВИЙ_РЯДОК.strip(), згорнута)
        finally:
            shutil.rmtree(тека, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()

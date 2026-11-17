# -*- coding: utf-8 -*-
"""Виконує самоперевірку приладу Е2-смуга-погоди та повертає ненульовий код при провалі."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import корінь_е2_смуга_погоди as ПРИЛАД


class СамоперевіркаПогоди(unittest.TestCase):
    """Усі штучні дерева проходять тим самим шляхом, що й --самоперевірка."""

    def test_усі_випадки(self):
        """Перевіряє кожне очікування й друкує підсумок для журналу CI."""
        випадки = ПРИЛАД.самоперевірка()
        self.assertTrue(випадки, "самоперевірка не повернула випадків")
        for назва, пройшов in випадки:
            with self.subTest(випадок=назва):
                self.assertTrue(пройшов, назва)
        print("самоперевірка: %d з %d" % (sum(ок for _, ок in випадки), len(випадки)))


if __name__ == "__main__":
    unittest.main()

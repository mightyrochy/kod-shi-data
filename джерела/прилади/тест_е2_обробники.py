# -*- coding: utf-8 -*-
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


шлях = Path(__file__).with_name('е2_обробники.py')
специфікація = importlib.util.spec_from_file_location('е2_обробники', шлях)
модуль = importlib.util.module_from_spec(специфікація)
специфікація.loader.exec_module(модуль)


class Інвентар(unittest.TestCase):
    def test_обробники_а_не_коментарі_чи_рядки(self):
        with tempfile.TemporaryDirectory() as т:
            дж = Path(т) / 'джерела'
            (дж / 'показ').mkdir(parents=True)
            (дж / 'показ.html').write_text(
                '<button onclick="зберегти()">Так</button>\n<script>\n'
                'к.onclick = () => малювати();\n</script>', encoding='utf-8')
            (дж / 'показ' / 'а.js').write_text(
                '// x.onclick = вигадано\nconst x = "y.onclick = брехня";\n'
                'function старт(){\n'
                '  е.addEventListener("change", () => зберегти(дані));\n'
                '  е.onclick = обробити;\n}\n', encoding='utf-8')
            записи = модуль.інвентар(т)
            self.assertEqual([(з['рядок'], з['подія'], з['виклики']) for з in записи], [
                (1, 'onclick', ['зберегти']), (3, 'onclick', ['малювати']),
                (4, 'change', ['зберегти']), (5, 'onclick', ['обробити'])])
            self.assertEqual(записи[2]['функція'], 'старт')

    def test_помилковий_js_не_дає_частковий_інвентар(self):
        with tempfile.TemporaryDirectory() as т:
            дж = Path(т) / 'джерела'
            (дж / 'показ').mkdir(parents=True)
            (дж / 'показ.html').write_text('', encoding='utf-8')
            (дж / 'показ' / 'а.js').write_text('function (', encoding='utf-8')
            with self.assertRaises(subprocess.CalledProcessError):
                модуль.інвентар(т)


if __name__ == '__main__':
    unittest.main()

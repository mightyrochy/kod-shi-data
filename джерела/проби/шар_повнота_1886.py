"""Відтворює ж2 з неповною моделлю та звіряє ж1 без живих викликів."""
import json
import pathlib
import subprocess
import sys


def main():
    """Друкує покриття заяв і причину лексичного сигналу ж1."""
    корінь = pathlib.Path(__file__).resolve().parents[2]
    тека = корінь / 'аудит/перевірки/доробка-1886'
    вхід = json.loads((тека / 'вхід.json').read_text(encoding='utf-8'))
    for к in вхід['ж1']:
        без = [н for н in к['назви'] if н.lower() not in к['текст'].lower()]
        print('ж1 рука', к['рука'], 'лексично поза прозою:', без)
        if к['рука'] == '4':
            assert без == ['shoes']
            assert 'Leather ballet flats' in к['текст'] and 'Шкіряні балетки' in к['опис']
    return subprocess.run(['node', str(тека / 'повнота.cjs')], cwd=корінь).returncode


if __name__ == '__main__':
    sys.exit(main())

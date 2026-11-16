"""Відтворює ж2 з неповною моделлю та звіряє ж1 без живих викликів."""
import json
import pathlib
import subprocess
import sys


def main():
    """Друкує покриття заяв і причину лексичного сигналу ж1."""
    корінь = pathlib.Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(корінь / 'джерела'))
    import мовний_шар as М
    for сир in ('{"а":"рядок" "б":"другий"}', '{"а":"\\"цитата\\""\n"б":"знак : , }"}',
                '{"а":"рядок" "б":', '{"а":"рядок";"б":"другий"}', '{"а":"рядок" "а":"інший"}'):
        об, чому = М._обʼєкт(сир)
        assert об is None and чому.startswith(("invalid_json(", "json_cut_off(")), чому
    print('пропущені коми / обрив / інша помилка / дублі: причина з місцем вади на повтор (Е2-межі п.4), не ремонт')
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

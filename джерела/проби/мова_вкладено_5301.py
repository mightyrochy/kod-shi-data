# -*- coding: utf-8 -*-
"""Повторює вихідний мовний шар на сирих записах VIDPOVIDI без виклику моделі."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import мовний_шар as М


def повторити(тека):
    """Друкує прийняті тексти з блоку ТЕКСТИ кожного запису й загальну кількість."""
    записів = текстів = прийнято = 0
    for файл in sorted(Path(тека).rglob('*_мовний_шар.txt')):
        сирий = файл.read_text(encoding='utf-8')
        if '\nТЕКСТИ:\n' not in сирий:
            continue
        розмітка, _ = json.JSONDecoder().raw_decode(сирий.split('\nТЕКСТИ:\n', 1)[1].lstrip())
        розмітка = [dict(р, ключ=str(р['н'])) for р in розмітка]
        відповідь = re.split(r'── ВІДПОВІДЬ[^\n]*\n', сирий, maxsplit=1)[1]
        вихід = М.прийняти(розмітка, відповідь)
        взято = len(розмітка) - len(вихід['без_відповіді'])
        записів += 1
        текстів += len(розмітка)
        прийнято += взято
        print(f'{файл.relative_to(тека)}: {взято}/{len(розмітка)}; {вихід["причина"]}')
    print(f'Разом: {записів} записів; {прийнято}/{текстів}')


if __name__ == '__main__':
    повторити(sys.argv[1])

"""Контактні аркуші кадрів вибірки пулу (очі по кадру): 24 речі зі страти, зерно 11658.

Запуск: python3 -X utf8 аудит/проби/річ_запис_аркуш.py СТРАТА (розбіжні | згідні) — мережа: кадри з сайтів крамниць.
Пише ТЕКА/аркуш_СТРАТА.png і аркуш_СТРАТА.json (номер → id, назва, тип, слот запису).
"""
import io
import json
from pathlib import Path
import random
import sys

import requests
from PIL import Image, ImageDraw

ТЕКА = Path(__file__).resolve().parent / 'річ_запис_каталог_2026_10_30'


def main():
    """Зібрати аркуш 6×4."""
    страта = sys.argv[1]
    речі = json.loads((ТЕКА / 'пул_вибірки.json').read_text(encoding='utf-8'))[страта]
    вибір = sorted(random.Random(11658).sample(range(len(речі)), 24))
    аркуш = Image.new('RGB', (6 * 200, 4 * 270), 'white')
    м = d = ImageDraw.Draw(аркуш)
    легенда = {}
    for к, і in enumerate(вибір):
        р = речі[і]
        легенда[к + 1] = dict(індекс=і, id=р['id'], назва=р['назва'][:70], тип=р['тип'], слот=р['слот'], кадр=р['кадр'])
        x, y = (к % 6) * 200, (к // 6) * 270
        try:
            ф = Image.open(io.BytesIO(requests.get(р['кадр'], timeout=25).content)).convert('RGB')
            ф.thumbnail((196, 240))
            аркуш.paste(ф, (x + 2, y + 24))
        except Exception as п:
            d.text((x + 5, y + 100), 'нема кадру', fill='red')
        d.text((x + 4, y + 4), f'{к + 1}: {р["слот"]}/{р["тип"]}'[:34], fill='black')
    аркуш.save(ТЕКА / f'аркуш_{страта}.png')
    (ТЕКА / f'аркуш_{страта}.json').write_text(json.dumps(легенда, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

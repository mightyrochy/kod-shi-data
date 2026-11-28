# -*- coding: utf-8 -*-
"""Кадри каталогу, спільні для багатьох різних речей: логотип, банер, значок чи мініатюра іншого товару, а не річ.

Запуск з кореня репозиторію: python3 -I аудит/звіти/запис-речі-код/скрипти/кадри_спільні.py
Пише дані/кадри_спільні.txt. Адресу кадру зведено без розміру (`/images/N/<розмір>/` → `/images/N/*/`), щоб той самий
логотип у кількох розмірах був одним кадром; адреси `_next/image` — цілком, бо там річ у параметрах запиту.
"""
import collections
import gzip
import json
import re
from pathlib import Path

ПОРІГ = 20
ТУТ = Path(__file__).resolve().parent.parent


def ключ(адреса):
    адреса = str(адреса)
    if '_next/image' in адреса:
        return адреса
    return re.sub(r'/images/(\d+)/[^/]+/', r'/images/\1/*/', адреса.split('?')[0])


def головна():
    with gzip.open('каталог_записи_v1.jsonl.gz', 'rt', encoding='utf-8') as ф:
        записи = [json.loads(р) for р in ф if р.strip()]
    речей = collections.Counter()
    for з in записи:
        for к in {ключ(а) for а in з.get('кадри') or []}:
            речей[к] += 1
    спільні = {к for к, н in речей.items() if н >= ПОРІГ}
    з_кадром, першим, усі = [], [], []
    for з in записи:
        кк = [ключ(а) for а in з.get('кадри') or []]
        if any(к in спільні for к in кк):
            з_кадром.append(з)
        if кк and кк[0] in спільні:
            першим.append(з['ід'])
        if кк and all(к in спільні for к in кк):
            усі.append(з['ід'])
    рядки = [
        f'записів {len(записи)}; кадрів, спільних для ≥ {ПОРІГ} речей: {len(спільні)}',
        f'речей з таким кадром {len(з_кадром)}; з ним першим {len(першим)}; лише з такими кадрами {len(усі)}',
        'за збирачем: ' + ', '.join(f'{к} {н}' for к, н in collections.Counter(з['збирач'] for з in з_кадром).most_common()),
        'за крамницею: ' + ', '.join(f'{к} {н}' for к, н in
                                     collections.Counter(з['адреса'].split('/')[2] for з in з_кадром).most_common()),
        '', '## спільні кадри (речей · адреса)',
    ]
    рядки += [f'{н} · {к}' for н, к in sorted(((н, к) for к, н in речей.items() if к in спільні), reverse=True)]
    рядки += ['', '## речі лише з такими кадрами', ' '.join(усі)]
    (ТУТ / 'дані' / 'кадри_спільні.txt').write_text('\n'.join(рядки) + '\n', encoding='utf-8')
    print('\n'.join(рядки[:3]))


if __name__ == '__main__':
    головна()

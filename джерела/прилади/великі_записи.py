# -*- coding: utf-8 -*-
"""Не пропускає нові чи змінені великі записи аудит/ у дерево PR для main.

Незмінені залежності приладів не забороняє. Сирий запис можна закомітити в гілці
прогону, а перед PR прибрати з її голови: звіт посилається на SHA цього запису.
"""
import argparse
import json
from pathlib import Path

from читачі_записів import git, дерево, захищений


def порушення(файли, змінені, межа):
    """Лічить лише великі файли аудит/, що залишилися зміненими в дереві PR."""
    return [(п, файли[п][0]) for п in sorted(змінені)
            if п.startswith('аудит/') and not захищений(п) and п in файли and файли[п][0] > межа]


def main():
    """Порівнює кінцеві дерева, дозволяючи окремі сирі коміти гілки прогону."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--база', required=True)
    парсер.add_argument('--голова', default='HEAD')
    а = парсер.parse_args()
    налаштування = json.loads(Path(__file__).with_name('записи_межа.json').read_text(encoding='utf-8'))
    база = git('merge-base', а.база, а.голова).decode().strip()
    змінені = set(п.decode('utf-8') for п in
                 git('diff', '--name-only', '--no-renames', '-z', база, а.голова).split(b'\0') if п)
    червоні = порушення(дерево(а.голова), змінені, налаштування['байтів'])
    for шлях, розмір in червоні:
        print(f'ВЕЛИКИЙ ЗАПИС: {шлях} — {розмір} байтів; лишити у коміті гілки прогону, зняти з дерева PR')
    print(f'великих нових/змінених записів: {len(червоні)}; межа: {налаштування["байтів"]} байтів')
    return int(bool(червоні))


if __name__ == '__main__':
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""Друкує короткий стан активного виміру, не втручаючись у стенд."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


def виконати():
    звіт = Path(__file__).resolve().parent
    for файл in sorted(звіт.glob('повний-*.log')):
        події = []
        for рядок in файл.read_text(encoding='utf-8').splitlines():
            if рядок.startswith('ЧАС '):
                try:
                    події.append(json.loads(рядок[4:]))
                except json.JSONDecodeError:
                    pass  # Записувач міг саме друкувати останній рядок.
        сцени = [п for п in події if п['подія'] == 'кінець сцени']
        остання = next((п for п in reversed(події) if п['подія'] == 'початок'), None)
        print(файл.name, 'завершено:', len(сцени),
              'остання:', (сцени[-1]['сцена'], round(сцени[-1]['секунд'], 3)) if сцени else None)
        print('Етап:', (остання['сцена'], остання['етап'], остання['utc']) if остання else None)
    журнали = sorted(Path(os.environ['TEMP']).glob('відтворення-*/лог.txt'), key=lambda ф: ф.stat().st_mtime)
    if журнали:
        текст = журнали[-1].read_text(encoding='utf-8')
        виклики = re.findall(r'↔ запис #\d+[^\n]*', текст)
        print('Останній виклик:', виклики[-1] if виклики else 'ще немає')
    print(datetime.now(timezone.utc).isoformat())


if __name__ == '__main__':
    виконати()

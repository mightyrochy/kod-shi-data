"""cProfile запитів на записаному вході мосту; окремо міряє момент готовності першої руки.

python3 джерела/прилади/профіль_запитів.py --сторінка /tmp/до/index.html \
    --входи аудит/проби/знімок_входи_сід3.jsonl.gz --вихід /tmp/профіль
Профіль сповільнює виклик: час продукту міряють знімок_мосту.py й часи_збору.js.
"""
import argparse
import asyncio
import cProfile
import contextlib
import io
import json
import os
import pstats
import sys
import tempfile
import time
import zipfile

import знімок_мосту as З


def головна():
    """Відтворює префікс сцени до останніх запитів та зберігає профілі й тотожний вихід."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--сторінка', required=True)
    парсер.add_argument('--входи', required=True)
    парсер.add_argument('--вихід', required=True)
    парсер.add_argument('--без-профілю', action='store_true', help='годинник і процесорний час без накладних витрат cProfile')
    арг = парсер.parse_args()
    текст = З.прочитати(арг.входи)
    рядки = [json.loads(р) for р in текст.splitlines() if р.strip()]
    межа = max(н + 1 for н, р in enumerate(рядки) if р['ім'] == 'запити')
    вихід = os.path.abspath(арг.вихід)
    os.makedirs(вихід, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='профіль_запитів_') as тека:
        zipfile.ZipFile(io.BytesIO(З.модулі_зі_сторінки(арг.сторінка))).extractall(тека)
        З.підготувати(тека)
        # cProfile уже імпортував stdlib profile; у продукту є власний однойменний модуль.
        sys.modules.pop('profile', None)
        import bridge
        виклик = bridge.виклик
        виміри = []

        def виміряти(ім, вхід):
            """Профілює лише запити; попередні виклики відтворюють справжній стан кешів."""
            if ім != 'запити':
                return виклик(ім, вхід)
            профіль = cProfile.Profile()
            початок, процесор = time.perf_counter(), time.process_time()
            перша, перша_процесорний, промпт = None, None, None
            with contextlib.nullcontext() if арг.без_профілю else профіль:
                if hasattr(bridge, 'запити_кроками'):
                    кроки = bridge.запити_кроками(вхід)
                    try:
                        while True:
                            промпт = next(кроки)
                            перша = (time.perf_counter() - початок) * 1000
                            перша_процесорний = (time.process_time() - процесор) * 1000
                    except StopIteration as кінець:
                        результат = кінець.value
                else:
                    результат = виклик(ім, вхід)
            повний = (time.perf_counter() - початок) * 1000
            процесорний = (time.process_time() - процесор) * 1000
            об = json.loads(результат) if isinstance(результат, str) else результат
            if об.get('помилка'):
                raise RuntimeError(об['помилка'])
            if промпт:
                assert промпт['промпт'] == об['руки']['1']
                assert промпт['частини'] == (об.get('руки_частини') or {}).get('1')
            номер = str(len(виміри) + 1)
            if not арг.без_профілю:
                профіль.dump_stats(os.path.join(вихід, номер + '.prof'))
                with open(os.path.join(вихід, номер + '.txt'), 'w') as файл:
                    pstats.Stats(профіль, stream=файл).strip_dirs().sort_stats('cumulative').print_stats(30)
            виміри.append(dict(повний_мс=повний, перша_мс=перша, процесорний_мс=процесорний,
                              перша_процесорний_мс=перша_процесорний, запитів_руки_1=(
                len(промпт['частини']) if промпт and промпт['частини'] else 1)))
            return результат

        bridge.виклик = виміряти
        знімок, час = asyncio.run(З.прогнати(текст, межа))
        записи = [json.loads(р) for р in знімок.splitlines()[1:]]
        помилки = [(р['н'], р['ім'], р['помилка']) for р in записи if 'помилка' in р]
        if помилки:
            raise RuntimeError(помилки)
        with open(os.path.join(вихід, 'знімок.jsonl'), 'w') as файл:
            файл.write(знімок)
        with open(os.path.join(вихід, 'час.json'), 'w') as файл:
            json.dump(dict(профіль=виміри, час=час), файл, ensure_ascii=False, indent=2)
        print(json.dumps(виміри, ensure_ascii=False))


if __name__ == '__main__':
    головна()

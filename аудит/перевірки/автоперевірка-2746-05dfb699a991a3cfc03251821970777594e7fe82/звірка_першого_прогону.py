"""Звірити збережені мірила PR #2746 і контракт читання каталогу без мережевих викликів."""
import contextlib
import gzip
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch

def main():
    """Перелічити факти призначеної голови та виконати пробу читача ДО → ПІСЛЯ."""
    root = pathlib.Path(sys.argv[1]).resolve()
    evidence = root / 'аудит/проби/Е2-вікно-0111'

    def read(name):
        return json.loads((evidence / name).read_text(encoding='utf-8'))

    for window in (6016, 5632):
        name = f'розбір_слот{window}'
        run = read(name + '/прогін.json')
        failed = [x for x in run['речі'] if x.get('впало')]
        stderr = (evidence / name / 'stderr.txt').read_text(encoding='utf-8')
        print(f'розбір {window}: речей={len(run["речі"])}, впало={len(failed)}, скорочень={stderr.count("промпт скорочено до вікна")}')
        journal = evidence / name / 'журнал.jsonl'
        if journal.exists():
            rows = [json.loads(x) for x in journal.read_text(encoding='utf-8').splitlines()]
            print('  журнал: записів=%d, max(вхід+стеля)=%d, перевищень=%d' % (
                len(rows), max(x.get('вхід_т', 0) + x.get('стеля_виводу', 0) for x in rows),
                sum(x.get('вхід_т', 0) + x.get('стеля_виводу', 0) > window for x in rows)))

    for window in (3000, 2816):
        run = read(f'жнива/вибірка_{window}.json')
        rows = [json.loads(x) for x in (evidence / f'жнива/журнал_{window}.jsonl').read_text(encoding='utf-8').splitlines()]
        print('жнива %d: речей=%d, збоїв=%d, запитів=%d, max(вхід+стеля)=%d, перевищень=%d, кадрів=%s' % (
            window, len(run['речі']), run['мета']['збоїв'], len(rows),
            max(x['usage']['prompt_tokens'] + x['max_tokens'] for x in rows),
            sum(x['usage']['prompt_tokens'] + x['max_tokens'] > window for x in rows),
            sorted({x['кадрів'] for x in rows})))

    for window in (52224, 50176):
        rows = read(f'б1_{window}/модель_виклики.json')['виклики']
        log = (evidence / f'б1_{window}/лог.txt').read_text(encoding='utf-8')
        stylist = [x for x in rows if x.get('модель_сторінки') == 'qwen/qwen3.5-9b']
        print('б1 %d: викликів=%d, HTTP400=%d, скорочень=%d, max(вхід+стеля)=%d, перевищень=%d' % (
            window, len(rows), sum(x['статус'] == 400 for x in rows),
            log.count('warning: model · prompt shrunk to fit window'),
            max(x['вхід'] + x['стеля'] for x in stylist),
            sum(x['вхід'] + x['стеля'] > window for x in stylist)))
        for n, line in enumerate(log.splitlines(), 1):
            if 'warning: model · prompt shrunk' in line or re.search(r'рука [12] · repair', line):
                print(f'  рядок {n}: {line.strip()}')
            if line.lstrip().startswith(('рука 1 {', 'рука 2 {')):
                data = json.loads(line[line.index('{'):])
                print('  рука=%s, речей=%s, фото=%s, збій=%s' % tuple(data.get(k) for k in ('рука','речей','фото','збій')))
        print('  ремонти:', [(x['вхід'], x['стеля']) for x in stylist if x['тип'] == 'ВЕРДИКТ_V1→ОБРАЗИ_V1'])

    sys.path.insert(0, str(root / 'джерела'))
    import жнива_прогін as harvest

    base = subprocess.run(['git','show','f17348e1f3740739f4da172e5301e5806a1c6172:джерела/жнива_прогін.py'], cwd=root, capture_output=True, check=True).stdout.decode('utf-8')
    old = {'__name__': 'жнива_до', '__file__': str(root / 'джерела/жнива_прогін.py')}
    exec(compile(base, old['__file__'], 'exec'), old)

    with tempfile.TemporaryDirectory(prefix='звірка_2746_') as scratch:
        scratch = pathlib.Path(scratch)
        xml = scratch / 'каталог.xml'
        xml.write_text('<yml_catalog><shop><categories><category id="1">Сукні</category></categories><offers><offer id="1" available="true"><name>Сукня</name><price>1000</price><currencyId>UAH</currencyId><categoryId>1</categoryId><url>https://example.invalid/1</url></offer></offers></shop></yml_catalog>', encoding='utf-8')
        archive = scratch / 'каталог.xml.gz'
        with gzip.open(archive, 'wb') as out:
            out.write(xml.read_bytes())
        for label, namespace in [('ДО',old), ('ПІСЛЯ',harvest.__dict__)]:
            namespace['проба_реферера'] = lambda offers: {'без_мережі': []}
            for mode, args in [('XML',['--каталог',str(xml)]), ('GZ',['--каталог',str(archive)]), ('типовий',[])]:
                argv = ['жнива_прогін.py','--реферер'] + args
                with patch.object(sys,'argv',argv), patch.object(harvest.F,'каталог_на_диску',return_value=str(xml)), contextlib.redirect_stdout(io.StringIO()):
                    try:
                        namespace['main']()
                        result = 'гаразд'
                    except Exception as error:
                        result = type(error).__name__ + ': ' + str(error)[:120]
                print(f'читання {label} {mode}: {result}')


if __name__ == "__main__":
    main()

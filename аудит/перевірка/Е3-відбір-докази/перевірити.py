"""Виконує батарею та сім'ю відбору послідовно, зберігаючи повні журнали й коди."""
import json
import os
import pathlib
import subprocess
import sys
import time
import gzip
import tempfile


def головна():
    """Дочекатися кожної перевірки й підсумувати факти без приховування провалів."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    джерела = корінь / 'джерела'
    os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                      NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')
    основні = ['стенд_знімок.py --дим', 'тест_живого_шляху.py', 'тест_протоколу.py',
               'прилади/розділи_гейтів.py', 'audit_contracts.py']
    проби = sorted({p for шаблон in ('відбір_*.py', 'семплер_*.py', 'cmp_*.py',
                     'ремонт_*.py', 'ремонт2_*.py', 'повнота_*.py', 'промпти3_ремонт*.py',
                     'поділ_composer_ast.py', 'поділ_pipeline_ast.py')
                   for p in (джерела / 'проби').glob(шаблон)
                   if not p.name.endswith(('_живо.py',))})
    записи = pathlib.Path(tempfile.mkdtemp(prefix='e3-selection-records-'))
    for з in (корінь / 'аудит/тести/сирі_2026-09-25/t7_remont_c59f301/stend_seed13').glob('seed13_*.txt.gz'):
        (записи / з.stem).write_bytes(gzip.decompress(з.read_bytes()))
    команди = [[sys.executable, *s.split()] for s in основні]
    команди += [['node', 'тест_показу.js']]
    команди += [[sys.executable, str(p)] + ([str(записи), '13']
                 if p.name in ('ремонт_опис_біля_номера.py', 'ремонт_слоти.py') else []) for p in проби]
    підсумок = []
    for н, команда in enumerate(команди):
        поч = time.monotonic()
        with (тека / f'{н:02d}.log').open('w', encoding='utf-8') as журнал:
            р = subprocess.run(команда, cwd=джерела, stdout=журнал, stderr=subprocess.STDOUT)
        запис = dict(команда=команда[1:], код=р.returncode, секунд=round(time.monotonic() - поч, 2))
        підсумок.append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
        (тека / 'батарея.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return int(any(x['код'] for x in підсумок))


if __name__ == '__main__':
    sys.exit(головна())

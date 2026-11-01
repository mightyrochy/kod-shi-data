"""Звіряє записаний TSV виміру сторожів без читання активних журналів."""
import csv
import io
import json
import subprocess
from collections import Counter

SOURCE = '03b369eef50b'
PATH = 'аудит/корені/ПК-межа-без-джерела-вимір-codex-agy.tsv'
blob = subprocess.check_output(['git', 'show', f'{SOURCE}:{PATH}'])
rows = list(csv.DictReader(io.StringIO(blob.decode('utf-8-sig')), delimiter='\t'))
assert len(rows) == 1951
print('Джерело: ' + SOURCE + ':' + PATH)
print('Рядків: ' + str(len(rows)))
for engine in ('codex', 'agy'):
    chosen = [r for r in rows if r['рушій'] == engine and r['код_кінця'] == 'DONE']
    measured = [r for r in chosen if r['без_міжходових_сек']]
    winner = max(measured, key=lambda r: float(r['без_міжходових_сек']))
    print(f'{engine}: DONE {len(chosen)}, виміряно {len(measured)}; максимум {winner["без_міжходових_хв"]} хв; {winner["прогін"]}')
    print('  Події: ' + (winner['внутрішня_подія_1'] or winner['подія_1']) + ' → ' + (winner['внутрішня_подія_2'] or winner['подія_2']))
    if engine == 'codex':
        excluded = [r for r in chosen if int(r['міжходових_пар'] or 0)]
        assert sum(int(r['міжходових_пар']) for r in excluded) == 12 and len(excluded) == 5
        assert len(chosen) == 232 and len(measured) == 209
        assert winner['без_міжходових_хв'] == '21.87'
        for r in excluded:
            print(f'  Виключено міжходових пар: {r["прогін"]}: {r["міжходових_пар"]}')
        print('  Виключено: turn.completed/turn.failed → наступний turn.started, включно з thread.started; нездорові прогони; 23 DONE без журналу не домислено.')
    else:
        turns = [turn for r in chosen for turn in json.loads(r['усі_ходи'])]
        assert len(chosen) == len(measured) == 61 and len(turns) == 62
        assert all(t['статус'] == 'SUCCESS' for t in turns)
        assert winner['без_міжходових_хв'] == '102.69'
        assert round(max(t['секунди'] for t in turns) / 60, 2) == 102.69
        print('  Виключено: очікування між ходами, підготовка й завершення обгортки; взято result.duration_seconds кожного з 62 SUCCESS-ходів, не зовнішній час прогону.')
print('Claude: n=null; нема виміру, що представляє роботу — рішення менеджера 01.11, КОЛО PR #2685 у паспорті кореня.')

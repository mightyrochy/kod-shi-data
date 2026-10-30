# -*- coding: utf-8 -*-
"""Вимір «чи бачить жінка фото речі на картці» на записаних прогонах (наряд фото-видиме-вимір, 30.10).

Читає `вердикти.txt` (речі образу рук 1–2 з адресою `фото`) і `знімки/фото_карток.txt` (картинки картки: прийшло чи ні)
кожного запису ПІСЛЯ-Е3 і автоживих; `--http` ще відкриває кожну унікальну адресу (GET, код і тип). Друкує таблицю md.
    python3 -I аудит/проби/фото_видиме_таблиця.py [--http] > таблиця.md
"""
import concurrent.futures as cf, glob, json, os, re, subprocess, sys
from collections import defaultdict

К = os.path.dirname(os.path.abspath(__file__)) + '/'
ТЕКИ = sorted(glob.glob(К + 'б1/ПІСЛЯ-Е3/*/')) + sorted({os.path.dirname(f) + '/' for f in glob.glob(К + 'автоживий-*/**/вердикти.txt', recursive=True)})
ЗАПИСИ, АДРЕСИ = defaultdict(list), set()
for д in ТЕКИ:
    if not os.path.exists(д + 'вердикти.txt'): continue
    ф = open(д + 'знімки/фото_карток.txt').read() if os.path.exists(д + 'знімки/фото_карток.txt') else ''
    картки = {м.group(1): (int(м.group(2)), int(м.group(3))) for м in re.finditer(r'рука (\d) · картинок (\d+), прийшло (\d+)', ф)}
    for п in json.load(open(д + 'вердикти.txt'))['прогони']:
        for в in п['вердикти']:
            р = str(в['рука'])
            if р not in '12': continue
            а = [(q.get('фото') or '') for q in в.get('речі_образу') or []]
            АДРЕСИ.update(x for x in а if x)
            ЗАПИСИ[д.replace(К, '').replace('б1/ПІСЛЯ-Е3/', 'Е3/').replace('автоживий-', 'ав-')[:90]].append((р, а, *картки.get(р, (0, 0))))

def відкрити(a):
    o = subprocess.run(['curl', '-s', '-o', '/dev/null', '-m', '20', '-L', '-A', 'Mozilla/5.0', '-w', '%{http_code} %{content_type}', a],
                       capture_output=True, text=True).stdout
    return a, o
ВІДПОВІДІ = dict(cf.ThreadPoolExecutor(16).map(відкрити, АДРЕСИ)) if '--http' in sys.argv else {}
ок = lambda a: ВІДПОВІДІ.get(a, '200').startswith('200')
print('| запис | карток | речей | з адресою | відкривається | img у DOM | видно |\n|---|---|---|---|---|---|---|')
сума = [0] * 6
for з, рядки in ЗАПИСИ.items():
    р = [len(рядки), sum(len(a) for _, a, _, _ in рядки), sum(1 for _, a, _, _ in рядки for x in a if x),
         sum(1 for _, a, _, _ in рядки for x in a if x and ок(x)), sum(i for *_, i, _ in рядки), sum(v for *_, v in рядки)]
    сума = [x + y for x, y in zip(сума, р)]
    print('| %s | %s |' % (з, ' | '.join(map(str, р))))
print('| **разом (%d записів)** | %s |' % (len(ЗАПИСИ), ' | '.join('**%d**' % x for x in сума)))

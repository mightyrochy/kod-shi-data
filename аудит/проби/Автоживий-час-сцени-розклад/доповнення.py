#!/usr/bin/env python3
"""Таблиця «Доповнення диспетчера» звіту часу сцени (наряд Автоживий-час-сцени-доповнення-скриптом).
Запуск з кореня репозиторію: python3 аудит/проби/Автоживий-час-сцени-розклад/доповнення.py
Записи — ті самі, що в розклад.py (він і викликається: аудит/проби → тимчасовий JSON); визначення «повної» сцени —
функція `повний` з зведення.py, взята з його вихідного тексту (не копія). Набір: повна, не sonnet-прогін, режим
повне/+фото, без сцен із запитом > 3000 с (як у зведення.py). Стовпці — дата `початок` сцени: 07.11, 13.11.
Медіани сцени — за сценами набору; медіани запитів — за запитами цих сцен; у дужках — n (сцен, запитів чи файлів)."""
import ast, glob, json, os, statistics as st, subprocess, sys, tempfile

ТЕКА = os.path.dirname(os.path.abspath(__file__))
ПРОБИ = os.path.dirname(ТЕКА)
ДАТИ = (('2026-11-07', '07.11'), ('2026-11-13', 'нічний 13.11'))

def взяти_повний():
    дер = ast.parse(open(ТЕКА + '/зведення.py', encoding='utf-8').read())
    f = next(n for n in дер.body if isinstance(n, ast.FunctionDef) and n.name == 'повний')
    ns = {}
    exec(compile(ast.Module([f], []), 'зведення.py', 'exec'), ns)
    return ns['повний']

повний = взяти_повний()
з_ф = tempfile.NamedTemporaryFile(suffix='.json', delete=False); з_ф.close()
subprocess.run([sys.executable, '-I', ТЕКА + '/розклад.py', ПРОБИ, з_ф.name], check=True, stdout=subprocess.DEVNULL)
S = json.load(open(з_ф.name, encoding='utf-8')); os.unlink(з_ф.name)

def коротко(m):
    return {'mamaylm-gemma-3-12b-it-v2.0': 'MamayLM', 'qwen/qwen3.5-9b': 'qwen', 'claude-sonnet-5-5': 'sonnet'}.get(m, m)

def набір(дата):
    r = []
    for d in S:
        if d['дата'] != дата or d['режим'] not in ('повне', 'повне +фото') or not повний(d): continue
        c = d['виклики']
        if c and all(x['модель'] == 'claude-sonnet-5-5' for x in c): continue
        if any(x['с'] > 3000 for x in c): continue
        r.append(d)
    return r

def КР(d):
    # крок 1 — до «чат→паспорт» (п), 2 — «збирання» мінус п, 3–5 — решта (як у зведення.py)
    з = d['з'] if d['з'] is not None else d['п']
    return d['п'], з - d['п'], d['секунд'] - з

def вхід_симв(d, n):
    p = '%s/%s/VIDPOVIDI/обмін/%05d.json' % (ПРОБИ, d['тека'], n)
    j = json.load(open(p, encoding='utf-8'))
    q = j['запит']; q = json.loads(q) if isinstance(q, str) else q
    return sum(len(x.get('text', '')) if isinstance(x, dict) else len(x)
               for m in q['messages'] for x in (m['content'] if isinstance(m['content'], list) else [m['content']]))

def ф(v):
    return '—' if v is None else (('%.1f' % v).replace('.', ',') if abs(v - round(v)) > 1e-9 and abs(v) < 100 else '%d' % round(v))

def мед(v):
    return st.median(v) if v else None

def клітина(v, n):
    return 'не виміряно: немає записів (n=0)' if v is None else '%s (n=%d)' % (ф(v), n)

ВИД = {'ПАКЕТ': 'ПАКЕТ_V1→ОБРАЗИ_V1', 'ВЕРДИКТ': 'ВЕРДИКТ_V1→ОБРАЗИ_V1', 'ПАЛІТРА': 'вибір палітри (стилістка)',
       'ОПИС': 'ОПИС_V1→ОПИС_ВІДПОВІДЬ_V1', 'ПОВНОТА': 'ПОВНОТА→ДОПОВНЕННЯ_V1'}
стовпці = []
for дата, назва in ДАТИ:
    R = набір(дата); n = len(R); c = {}
    c['сцена, с'] = (мед([d['секунд'] for d in R]), n)
    c['крок 1 (чат→паспорт), с'] = (мед([КР(d)[0] for d in R]), n)
    c['крок 2 (збирання), с'] = (мед([КР(d)[1] for d in R]), n)
    c['кроки 3–5, с'] = (мед([КР(d)[2] for d in R]), n)
    c['сума запитів, с'] = (мед([sum(x['с'] for x in d['виклики']) for d in R]), n)
    c['поза моделлю, с'] = (мед([d['секунд'] - sum(x['с'] for x in d['виклики']) for d in R]), n)
    c['запитів на сцену'] = (мед([len(d['виклики']) for d in R]), n)
    for м in ('qwen', 'MamayLM'):
        зап = [x['с'] for d in R for x in d['виклики'] if коротко(x['модель']) == м]
        нс = [sum(коротко(x['модель']) == м for x in d['виклики']) for d in R]
        c[м + ': мед. запиту, с'] = (мед(зап), len(зап))
        c[м + ': запитів на сцену'] = (мед(нс), n)
    for к, вид in ВИД.items():
        зап = [x['с'] for d in R for x in d['виклики'] if x['вид'] == вид and (к != 'ПАКЕТ' or коротко(x['модель']) == 'qwen')]
        c['`%s`, мед. запиту, с' % вид + (' (qwen)' if к == 'ПАКЕТ' else '')] = (мед(зап), len(зап))
    вх = [вхід_симв(d, x['n']) for d in R for x in d['виклики'] if x['вид'] == ВИД['ПАКЕТ'] and коротко(x['модель']) == 'qwen']
    c['розмір входу `ПАКЕТ_V1→ОБРАЗИ_V1` (qwen), симв., мед. за файлами `обмін`'] = (мед(вх), len(вх))
    стовпці.append((назва, c))

рядки = ['| складник | ' + ' | '.join(н for н, _ in стовпці) + ' |', '|---|' + '---|' * len(стовпці)]
for к in стовпці[0][1]:
    рядки.append('| ' + к + ' | ' + ' | '.join(клітина(*c[к]) for _, c in стовпці) + ' |')
print('\n'.join(рядки))

# -*- coding: utf-8 -*-
import os
import json, re, collections
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
rows = json.load(open(РОБОЧА + '/rows.json', encoding='utf-8'))
def стан(s):
    t = s.replace('*', '').strip().upper()
    for k in ['ЗАКРИТО','ВІДКРИТО','ЧАСТКОВО','ЗНЯТО','ВІДКЛАДЕНО','ПЕРЕНЕСЕНО','ДУБЛЬ','ЗЛИТО']:
        if t.startswith(k): return k
    if t.startswith('НЕ ДОДАНО') or t.startswith('НЕ ВАДА') or t.startswith('НЕ РОБИТИ'): return 'НЕ ЗАДАЧА'
    return 'ІНШЕ'
for r in rows: r['стан'] = стан(r['st'])
# detection source by regex over src cell
ДЖ = [
 ('тестувальниця', r'тестувальниц'),
 ('власник', r'власни[кц]|скріншот|телефон'),
 ('живий прогін', r'ЖИВ|живий|живі|живого|ОЦІНКА-Ж|РОЗБІР-0210|РОЗБІР-\d+ А\d|ФОКУС|ZHYVA|прохід із живою'),
 ('стенд/проба/CI', r'стенд|СТЕНД|проба|пробою|гейт|батаре|CI|БАТ-|звірк'),
 ('перевірка/рецензія', r'перевірк|ПЕРЕВІРК|ПЕР-|рецензі|Gemini|gemini|codex review'),
 ('огляд/ревізія/аудит', r'РВ-|ревізі|огляд|ОГЛЯД|аудит|розбір Codex|ChatGPT|дослідженн|Research|Д\.1|Opus'),
 ('каталог/жнива', r'ЖНИВ|жнив|КАТАЛОГ|каталог|реєстр|МАМАЙ|ФІД|фід|кадр'),
 ('менеджер/куратор', r'менеджер|куратор|диспетчер|лист'),
 ('сесія-виконавець', r'знахідк|звіт сесії|виконав|сесі|наряд|#\d+'),
]
def джерело(s):
    for k, p in ДЖ:
        if re.search(p, s): return k
    return 'інше'
for r in rows: r['дж'] = джерело(r['src'])
c = collections.Counter(r['дж'] for r in rows)
print('ДЖЕРЕЛО (перше збіжне правило):'); [print(' ', v, k) for k, v in c.most_common()]
# by state
ct = collections.defaultdict(collections.Counter)
for r in rows: ct[r['дж']][r['стан']] += 1
for k in ct: print(k, dict(ct[k]))
# weight
def вага(w):
    w = w.replace('*','').lower()
    for k in ['критична','висока','середня','низька']:
        if k in w: return k
    return 'інше'
cw = collections.defaultdict(collections.Counter)
for r in rows: cw[вага(r['w'])][r['стан']] += 1
print('ВАГА×СТАН'); [print(' ', k, dict(v)) for k, v in cw.items()]
json.dump(rows, open(РОБОЧА + '/rows2.json','w',encoding='utf-8'), ensure_ascii=False)

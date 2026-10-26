# -*- coding: utf-8 -*-
import os
import json, csv, re, collections
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
rows = json.load(open(РОБОЧА + '/rows2.json', encoding='utf-8'))
reg = {int(x['номер']): x for x in csv.DictReader(open('аудит/дошка_розбір_chatgpt/результат/реєстр.tsv', encoding='utf-8'), delimiter='\t')}
D = re.compile(r'\b(\d{1,2})\.(09|10)\b')
def дата(r):
    if r['n'] in reg: return reg[r['n']]['поява_дата'][5:]
    m = D.search(r['src']) or D.search(r['raw'])
    return f"{m[2]}-{int(m[1]):02d}" if m else '??'
for r in rows: r['дата'] = дата(r)
# тижні
def тиждень(d):
    if d == '??': return '??'
    m, dd = d.split('-'); m=int(m); dd=int(dd)
    doy = (dd if m==9 else 30+dd)
    # 18.09=18 ... 
    w = (doy-14)//7
    return {0:'14–20.09',1:'21–27.09',2:'28.09–04.10',3:'05–11.10',4:'12–18.10',5:'19–25.10',6:'26.10–'}.get(w, str(w))
c = collections.defaultdict(collections.Counter)
for r in rows: c[тиждень(r['дата'])][r['стан']] += 1
for w in sorted(c): print(w, sum(c[w].values()), dict(c[w].most_common(5)))
json.dump(rows, open(РОБОЧА + '/rows3.json','w',encoding='utf-8'), ensure_ascii=False)
# rows > 8648 (after Д.1)
new = [r for r in rows if r['n'] not in reg]
print('нових після Д.1:', len(new), collections.Counter(r['стан'] for r in new).most_common())

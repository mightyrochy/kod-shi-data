# -*- coding: utf-8 -*-
"""Додаткові зрізи розмітки для синтезу (читає розмітка.tsv після aggregate.py)."""
import csv, collections, re, os
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
R = list(csv.DictReader(open(РОБОЧА + '/розмітка.tsv', encoding='utf-8'), delimiter='\t'))
for d in R:
    d['т'] = '6) 19.10–' if '19.10' in d['тиждень'] else d['тиждень']
Z = [d for d in R if d['стан'] in ('ЗАКРИТО', 'ЧАСТКОВО')]
def pct(a, b): return f'{100*a/max(b,1):.0f}%'
МОДЕЛЬНІ = {'слово→код', 'модель-стилістка', 'код→слово'}
ДЕТЕРМ = {'ядро', 'вимір', 'показ', 'доставка', 'джерело'}
print('== закриття за ланкою (симптом / корінь / доказ живий / доказ нема), закриті+часткові')
for name, S in [('модельні ланки', МОДЕЛЬНІ), ('детерміновані', ДЕТЕРМ), ('мірило', {'мірило'})]:
    X = [d for d in Z if d['ланка'] in S]; n = len(X)
    c = collections.Counter(d['закриття'] for d in X); e = collections.Counter(d['доказ'] for d in X)
    print(f'  {name:16s} n={n:4d} симптом {pct(c["симптом"],n)} корінь {pct(c["корінь"],n)} мірило {pct(c["мірило"],n)} | живий {pct(e["живий"],n)} проба {pct(e["проба"],n)} нема {pct(e["нема"],n)} текст {pct(e["текст"],n)}')
print('== за підсистемою: симптом/корінь серед закритих')
cs = collections.defaultdict(collections.Counter)
for d in Z: cs[d['підсистема']][d['закриття']] += 1
for k, c in sorted(cs.items(), key=lambda x: -sum(x[1].values())):
    n = sum(c.values()); print(f'  {k:20s} n={n:4d} симптом {pct(c["симптом"],n):>4s} корінь {pct(c["корінь"],n):>4s}')
print('== хто виявив видимі вади (рід вада-видима)')
V = [d for d in R if d['рід'] == 'вада-видима']
print(' ', collections.Counter(d['виявлено'] for d in V).most_common())
print('  ланка видимих:', collections.Counter(d['ланка'] for d in V).most_common())
print('== за тижнем: частка повторів (не «ні»), власник, живий, авто (стенд-проба-CI), побіжно')
ct = collections.defaultdict(list)
for d in R: ct[d['т']].append(d)
for k in sorted(ct):
    X = ct[k]; n = len(X); v = collections.Counter(d['виявлено'] for d in X)
    rep = sum(1 for d in X if d['повтор'] != 'ні'); reg = sum(1 for d in X if d['повтор'].startswith('регресія'))
    mch = collections.Counter(t for d in X for t in d['механізм'].split('+'))
    print(f'  {k:16s} n={n:4d} повтор {pct(rep,n):>4s} (регресія {pct(reg,n):>4s}) | власник {pct(v["власник"],n):>4s} живий {pct(v["живий-прогін"],n):>4s} авто {pct(v["стенд-проба-CI"],n):>4s} побіжно {pct(v["виконавець-побіжно"],n):>4s} огляд {pct(v["огляд-аудит"],n):>4s} перевірка {pct(v["перевірка-рецензія"],n):>4s} | мірило-не-те {pct(mch["мірило-не-те"],n):>4s} копія {pct(mch["копія-поняття"],n):>4s} рід-мірила {pct(sum(1 for d in X if d["рід"]=="вада-мірила"),n):>4s} рід-процесу {pct(sum(1 for d in X if d["рід"]=="вада-процесу"),n):>4s}')
print('== регресії: PR, що їх внесли (повтор регресія:#N), топ')
prc = collections.Counter()
for d in R:
    if d['повтор'].startswith('регресія:'):
        for x in re.findall(r'#(\d+)', d['повтор']): prc[x] += 1
print(' ', prc.most_common(15), 'усього PR:', len(prc), 'рядків-регресій з #PR:', sum(prc.values()))
print('== відкриті (ВІДКРИТО+ЧАСТКОВО): рід, підсистема, виявлено')
O = [d for d in R if d['стан'] in ('ВІДКРИТО', 'ЧАСТКОВО')]
print('  n=', len(O)); print(' ', collections.Counter(d['рід'] for d in O).most_common())
print(' ', collections.Counter(d['підсистема'] for d in O).most_common())
print(' ', collections.Counter(d['виявлено'] for d in O).most_common())
print('== інше: — кластери за ключовими словами')
ін = [t.split(':', 1)[1].strip() for d in R for t in d['механізм'].split('+') if t.startswith('інше:')]
print('  усього', len(ін))
кл = collections.OrderedDict([
 ('походження/типове/невідоме', r'походж|типов|невідом|дефолт|за замовч|запасн|підстав|or 0|відсутн|без входу|порожн|None|похідн|вигадан.*значен'),
 ('червона проба/поза CI/без власника', r'червон|поза CI|без власника|не запуск|мовчки пада|continue-on'),
 ('заява PR/звіт хибний', r'заява|звіт|PR не|не відпов|старш.*голов|діф|опис PR'),
 ('ковтання винятку/тихе', r'ковта|except|виняток|мовчк|тих'),
 ('дошка/посилання/документ', r'дошк|посилан|рядок N|документ|номер'),
 ('стеля/обрізка/ліміт', r'стел|обріз|ліміт|межа=|обрізк|урізан'),
 ('гілка/злиття/конфлікт', r'гілк|злитт|конфлікт|незлит'),
 ('поріг/вікно на око', r'поріг|порог|на око|вікн'),
 ('середовище/версія/кеш', r'середовищ|верс|кеш|Pyodide|CPython|застаріл'),
 ('шум/один прогін/вибірка', r'шум|один прогін|вибірк|сід|недетермін'),
])
cc = collections.Counter(); rest = []
for t in ін:
    hit = [k for k, p in кл.items() if re.search(p, t, re.I)]
    if hit: cc[hit[0]] += 1
    else: rest.append(t)
for k, v in cc.most_common(): print(f'  {v:4d} {k}')
print('  не в кластерах:', len(rest)); print('  ', ' | '.join(collections.Counter(rest).most_common(60) and [f'{a}' for a, _ in collections.Counter(rest).most_common(60)]))

print('== повертались після закриття (пізніший рядок називає закритий своєю темою чи поверненням)')
by = {int(d['n']): d for d in R}
назад = collections.defaultdict(set)
for d in R:
    m = re.match(r'^(тема|повернення|регресія):(.*)$', d['повтор'])
    if m and not m.group(2).strip().startswith('#'):
        for x in re.findall(r'\d{2,5}', m.group(2)):
            x = int(x)
            if x in by and x < int(d['n']): назад[x].add(int(d['n']))
def поверт(key):
    ct = collections.defaultdict(lambda: [0, 0])
    for d in Z:
        k = key(d); ct[k][0] += 1; ct[k][1] += bool(назад[int(d['n'])])
    return ', '.join(f'{k} {b}/{a} ({pct(b, a)})' for k, (a, b) in sorted(ct.items(), key=lambda x: -x[1][0]))
print('  закриття:', поверт(lambda d: d['закриття']))
print('  доказ:', поверт(lambda d: d['доказ']))
print('  ланка:', поверт(lambda d: 'модельні' if d['ланка'] in МОДЕЛЬНІ else 'детерміновані' if d['ланка'] in ДЕТЕРМ else 'інші'))
V = [d for d in Z if d['рід'] == 'вада-видима']
print('== закриті видимі вади × доказ:', len(V), collections.Counter(d['доказ'] for d in V).most_common())
ct = collections.defaultdict(lambda: [0, 0])
for d in R: ct[d['виявлено']][0] += 1; ct[d['виявлено']][1] += d['повтор'] != 'ні'
print('== повтор серед знайденого:', ', '.join(f'{k} {b}/{a} ({pct(b, a)})' for k, (a, b) in sorted(ct.items(), key=lambda x: -x[1][0])))
sp = lambda s: [x.strip() for x in re.split(r'[,;+]', s) if x.strip()]
print('== механізм: рядків, відкритих, закрито симптомом, повторів')
for tag in ['копія-поняття', 'запис-без-читача', 'мірило-не-те', 'інструкція-моделі', 'форма-виходу-моделі', 'дані-неповні', 'регресія', 'неповна-правка']:
    X = [d for d in R if tag in sp(d['механізм'])]; z = [d for d in X if d['стан'] in ('ЗАКРИТО', 'ЧАСТКОВО')]
    print(f'  {tag}: {len(X)}; відкр {sum(d["стан"] in ("ВІДКРИТО", "ЧАСТКОВО") for d in X)}; симптом {sum(d["закриття"] == "симптом" for d in z)}/{len(z)}; повтор {sum(d["повтор"] != "ні" for d in X)}')
ПОХ = re.compile(r'походж|типов|невідом|вигад|цитат|без входу|за замовч|default|нуль зливає|грубше за', re.I)
def є(d, теги): return bool(set(sp(d['механізм'])) & теги)
родини = {
    'Г1 мірило': lambda d: є(d, {'мірило-не-те', 'нема-мірила', 'вимір-хибний'}) or d['рід'] == 'вада-мірила',
    'Г2 модель і текст': lambda d: є(d, {'інструкція-моделі', 'форма-виходу-моделі', 'модель-вигадує', 'латка', 'код-читає-слова', 'код-пише-слова'}),
    'Г3 походження': lambda d: є(d, {'правило-без-входу', 'модель-вигадує', 'чуже-поле'}) or any(t.startswith('інше') and ПОХ.search(t) for t in sp(d['механізм'])) or bool(ПОХ.search(d['суть'])),
    'Г4 копії й читачі': lambda d: є(d, {'копія-поняття', 'запис-без-читача', 'неповна-правка', 'регресія', 'чуже-поле'}),
    'Г5 дані': lambda d: d['рід'] == 'вада-даних' or d['підсистема'] in ('каталог-жнива', 'кадр-фото') or 'дані-неповні' in sp(d['механізм']),
}
print('== родини причин (рядок може належати кільком)')
for k, f in родини.items():
    X = [d for d in R if f(d)]; z = [d for d in X if d['стан'] in ('ЗАКРИТО', 'ЧАСТКОВО')]
    print(f'  {k}: {len(X)} ({pct(len(X), len(R))}), відкритих {sum(d["стан"] in ("ВІДКРИТО", "ЧАСТКОВО") for d in X)}, закриття {collections.Counter(d["закриття"] for d in z).most_common(3)}')
print('  хоч одна родина:', sum(any(f(d) for f in родини.values()) for d in R), 'з', len(R))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Збирає таблиці виміру «користь перевірок» (наряд Перевірки-користь-вимір, 26.11).

Запуск з кореня репозиторію (потрібні повна історія `git fetch --shallow-since=2026-11-11 origin main`
і `gh` для PR без злитого коміту): `python3 -I аудит/звіти/перевірки-користь-2611/зібрати.py`.
Пише CSV поруч зі скриптом. Числа звіту рахує `порахувати.py` лише з цих CSV.

Джерела: сире/ (знімок GitHub 26.11), git-історія main, `аудит/БЕКЛОГ.md` і файли гілок дошки в історії,
`аудит/витрати/сесії_1911.csv` і `сесії_2611.csv`, звіти `аудит/{перевірки,перевірка,звіти}/`,
ручні таблиці поруч (`вердикти_ручні.tsv`, `блокуючі_авто.tsv`, `зауваження_ручні.tsv`).
"""
import csv, glob, json, os, re, subprocess, sys
from datetime import datetime, timezone

ТУТ = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ = os.path.abspath(os.path.join(ТУТ, '..', '..', '..'))
os.chdir(КОРІНЬ)
ВІКНО_З, ВІКНО_ДО = '2026-11-12T00:00:00Z', '2026-11-26T00:00:00Z'


def git(*a):
    return subprocess.run(['git', '-c', 'core.quotepath=off', *a], capture_output=True, text=True, encoding='utf-8').stdout


def utc(iso):
    """ISO з будь-яким зсувом → 'YYYY-MM-DDTHH:MM:SSZ'."""
    d = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return d.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def пиши(ім, шапка, рядки):
    with open(os.path.join(ТУТ, ім), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(шапка)
        w.writerows(рядки)


# ---------- 1. PR вікна й їхній клас за файлами ----------
prs = {}
for r in csv.DictReader(open(os.path.join(ТУТ, 'сире/pr_вікно.tsv'), encoding='utf-8'), delimiter='\t'):
    prs[int(r['PR'])] = r

файли_pr = {}
ключ = None
for l in git('log', '--since=2026-11-11', '--format=@@%H|%s', '--name-only').split('\n'):
    if l.startswith('@@'):
        sha, subj = l[2:].split('|', 1)
        m = (re.search(r'\(#(\d+)\)\s*$', subj) or re.match(r'Злиття #(\d+)', subj)
             or re.match(r'Merge pull request #(\d+)', subj))
        ключ = int(m.group(1)) if m else None
    elif l and ключ:
        файли_pr.setdefault(ключ, set()).add(l)


def файли_через_gh(n):
    r = subprocess.run(['gh', 'api', '-X', 'GET', f'repos/mightyrochy/kod-shi-data/pulls/{n}/files',
                        '--paginate', '--jq', '.[].filename'], capture_output=True, text=True)
    return set(x for x in r.stdout.split('\n') if x)


КОД_РОЗШ = ('.py', '.js', '.json', '.html', '.tsv', '.cjs', '.ps1', '.sh', '.yml', '.yaml')


def клас_файлу(p):
    b = os.path.basename(p)
    if p.startswith('джерела/') and not p.startswith(('джерела/прилади/', 'джерела/проби/')) \
            and not b.startswith('тест_') and p.endswith(КОД_РОЗШ):
        return 'продукт'
    if p.startswith('zhnyvarka/') and p.endswith(КОД_РОЗШ):
        return 'продукт'
    if p.startswith(('.github/', '.claude/', '.githooks/', 'джерела/прилади/', 'джерела/проби/', 'ohliad-',
                     'аудит/адаптери/', 'open-source-stylist/')) or b.startswith('тест_') \
            or (p.startswith('аудит/') and p.endswith(КОД_РОЗШ) and not p.endswith('.tsv')):
        return 'прилад'
    return 'документ'


def клас_pr(fs):
    if not fs:
        return 'невідомо'
    к = {клас_файлу(p) for p in fs}
    return 'продукт' if 'продукт' in к else 'прилад' if 'прилад' in к else 'документ'


pr_рядки = []
for n in sorted(prs):
    p = prs[n]
    fs = файли_pr.get(n)
    джерело = 'git'
    if not fs:
        fs = файли_через_gh(n)
        джерело = 'gh'
    pr_рядки.append([n, p['створено'], p['закрито'], p['злито'], p['гілка'], p['гілка'].split('/')[0],
                     'так' if p['злито'] else 'ні', клас_pr(fs), len(fs), джерело])
пиши('pr.csv', ['PR', 'створено_utc', 'закрито_utc', 'злито_utc', 'гілка', 'префікс_гілки', 'злито', 'клас',
                'файлів', 'файли_з'], pr_рядки)
pr_в_вікні = set(prs)

# ---------- 2. дошка ----------
мапа_класу = {'видима': 'а', 'внутрішня': 'б', 'дані': 'б', 'мірило': 'в', 'вимір': 'в', 'процес': 'г',
              'рішення': 'г', 'вимога': 'г'}
рядки_дошки = {}
for ф in [os.path.join(КОРІНЬ, 'аудит/БЕКЛОГ.md')] + glob.glob(os.path.join(КОРІНЬ, 'аудит/дошка/**/*.md'), recursive=True):
    for l in open(ф, encoding='utf-8'):
        m = re.match(r'^\|\s*(\d{4,5})\s*\|', l)
        if not m or int(m.group(1)) < 14000:
            continue
        n = int(m.group(1))
        мета = re.search(r'<!-- дошка: ([^>]*?)-->', l)
        md = dict(kv.split('=', 1) for kv in (мета.group(1).strip().split('; ') if мета else []) if '=' in kv)
        в = re.search(r'виявлено:\s*([^;|*]+?)\s*;\s*внесено:\s*([^|*]+?)\s*(?:\||\*|$)', l)
        ст = re.search(r'\*\*(ВІДКРИТО|ЗАКРИТО|ЧАСТКОВО|НЕ ВАДА)\*\*', l)
        клітинки = [c.strip() for c in l.split('|')]
        текст = re.sub(r'<!--.*?-->', '', клітинки[2] if len(клітинки) > 2 else '')
        текст = re.sub(r'\s+', ' ', текст)[:600]
        if n in рядки_дошки and рядки_дошки[n]['виявлено']:
            continue
        рядки_дошки[n] = dict(id=n, дата=md.get('дата', ''), рід=md.get('рід', ''), механізм=md.get('механізм', ''),
                              корінь=md.get('корінь', ''), виявлено=в.group(1) if в else '',
                              внесено=в.group(2) if в else '', статус=ст.group(1) if ст else '', текст=текст)
пиши('дошка_рядки.csv', ['id', 'дата', 'рід', 'клас', 'механізм', 'корінь', 'виявлено', 'внесено', 'статус', 'текст'],
     [[r['id'], r['дата'], r['рід'], мапа_класу.get(r['рід'], ''), r['механізм'], r['корінь'], r['виявлено'],
       r['внесено'], r['статус'], r['текст']] for r in sorted(рядки_дошки.values(), key=lambda x: x['id'])])

# ---------- 3. вердикти ----------
дати_звітів = {}  # ім'я файлу без .md → UTC дата додавання
for l in git('log', '--since=2026-11-11', '--diff-filter=A', '--name-only', '--format=@@%aI').split('\n'):
    if l.startswith('@@'):
        д = utc(l[2:])
    elif l and re.search(r'аудит/(перевірки|перевірка|звіти)/', l) and l.endswith('.md'):
        дати_звітів.setdefault(re.sub(r'\.md$', '', l.split('/', 2)[-1]), д)
    elif l and re.match(r'аудит/проби/(перевірка-[^/]+)/ЗВІТ\.md$', l):
        дати_звітів.setdefault(l.split('/')[2], д)

# дати «Злиття #N — ПЕРЕВІРЕНО…»
злиття_перевірено = {}
for l in git('log', '--since=2026-11-12', '--format=%aI|%s').split('\n'):
    m = re.match(r'([^|]+)\|Злиття #(\d+)(?: і з\d #\d+)? — (ПЕРЕВІРЕНО|ДОРОБИТИ)', l)
    if m:
        злиття_перевірено.setdefault(int(m.group(2)), (utc(m.group(1)), m.group(3)))


def рушій_із_моделі(м):
    if м.startswith('gpt-'):
        return 'Codex'
    if м.startswith('gemini-'):
        return 'agy (Gemini)'
    return 'Claude'


# 3a. ручні (звіти Claude та згадки)
КЛОД_МОДЕЛЬ = {'перевірка-4334-62120aa1': 'Opus 5.5', 'перевірка-4545-382543360e99': 'Opus 5.5',
               'перевірка-4529-4af27536369e': 'Sonnet 5.5', 'перевірка-4529-d03e6b64fdda': 'Sonnet 5.5',
               'перевірка-4543-f00d2e113207': 'Sonnet 5.5', 'перевірка-4543-b04c9149864e': 'Sonnet 5.5',
               'перевірка-4535-4ca92294f529': 'Sonnet 5.5', 'перевірка-4535-b12945726408': 'Sonnet 5.5',
               'перевірка-4527-9d05c1692a8a': 'Sonnet 5.5', 'перевірка-4259': 'Sonnet 5.5'}
ЗМІНА_РУШІЯ = {'перевірка-4627-звіт-проходу': ('agy (Gemini)', 'gemini-4-neon-high')}
вер = []
for l in open(os.path.join(ТУТ, 'вердикти_ручні.tsv'), encoding='utf-8'):
    l = l.rstrip('\n')
    if not l or l.startswith('#'):
        continue
    основа, pr, в, р, бл, коло, прим = (l.split('|') + [''] * 7)[:7]
    дата = дати_звітів.get(основа) or ''
    if not дата:
        дата = {'перевірка-1211-11': '2026-11-12T19:21:00Z', 'перевірка-1611-0745-4013-перша': '2026-11-16T05:44:00Z',
                'автоперевірка-4397-bc54a46c': '2026-11-19T17:38:00Z', 'перевірка-1911-1/ЗВІТ': '2026-11-19T00:54:00Z',
                'перевірка-1711-0055/ЗВІТ': '2026-11-17T01:06:00Z', 'перевірка-4729': '2026-11-25T20:40:00Z'}.get(основа, '')
    # злиті комітом диспетчера звіти, чиї дати не знайдено за іменем: лишаються порожніми
    рушій_ручн, модель_ручн = ЗМІНА_РУШІЯ.get(основа, ('Claude', КЛОД_МОДЕЛЬ.get(основа, 'не названо')))
    вер.append(dict(джерело='звіт' if дата and основа in дати_звітів else 'згадка', звіт=основа, дата=дата,
                    pr=int(pr), ризик=р, рушій=рушій_ручн, модель=модель_ручн,
                    вердикт=в, блок=бл, примітка=прим))

# 3b. автозвіти Codex/agy
блок_авто = {}
for l in open(os.path.join(ТУТ, 'блокуючі_авто.tsv'), encoding='utf-8'):
    l = l.rstrip('\n')
    if l and not l.startswith('#'):
        к, б = l.split('|')[:2]
        блок_авто[к] = б
for ф in sorted(glob.glob(os.path.join(КОРІНЬ, 'аудит/перевірки/автоперевірка-*.md'))):
    ім = os.path.basename(ф)[:-3]
    m = re.match(r'автоперевірка-(\d+)-([0-9a-f]+)$', ім)
    if not m:
        continue
    pr, sha = int(m.group(1)), m.group(2)
    дата = дати_звітів.get(ім, '')
    if not дата or дата < ВІКНО_З:
        continue
    t = open(ф, encoding='utf-8').read().split('\n')
    перші = ' '.join(t[:3])
    мод = re.search(r'(gpt-[\w.-]+?-(?:high|max|low)|gemini-[\w.-]+?-(?:high|max|low))', перші)
    в = re.search(r'(ПЕРЕВІРЕНО|ДОРОБИТИ|КОЛО|ЗАБЛОКОВАНО)', перші)
    р = re.search(r'Р([0-3])', перші)
    if not (мод and в):
        continue
    вер.append(dict(джерело='автозвіт', звіт=ім, дата=дата, pr=pr, ризик=('Р' + р.group(1)) if р else 'Р2',
                    рушій=рушій_із_моделі(мод.group(1)), модель=мод.group(1), вердикт=в.group(1),
                    блок=блок_авто.get(f'{pr}-{sha[:8]}', ''), примітка=''))
# 3c. «Злиття #N — ПЕРЕВІРЕНО» у темі коміту диспетчера — окремо, лише як свідчення
for pr, (д, в) in sorted(злиття_перевірено.items()):
    вер.append(dict(джерело='коміт-злиття', звіт=f'тема коміту «Злиття #{pr}»', дата=д, pr=pr, ризик='',
                    рушій='не названо', модель='не названо', вердикт=в, блок='', примітка=''))

вер.sort(key=lambda r: (r['pr'], r['дата'], r['джерело']))
# коло: порядковий номер вердикту по PR серед джерел звіт/автозвіт/згадка
лічильник = {}
for r in вер:
    if r['джерело'] == 'коміт-злиття':
        r['коло'] = ''
        continue
    лічильник[r['pr']] = лічильник.get(r['pr'], 0) + 1
    r['коло'] = лічильник[r['pr']]
пиши('вердикти.csv', ['джерело', 'звіт', 'дата_utc', 'PR', 'ризик', 'рушій', 'модель', 'вердикт', 'коло',
                      'блокуючі_рядки', 'PR_у_вікні', 'примітка'],
     [[r['джерело'], r['звіт'], r['дата'], r['pr'], r['ризик'], r['рушій'], r['модель'], r['вердикт'], r['коло'],
       r['блок'], 'так' if r['pr'] in pr_в_вікні else 'ні', r['примітка']] for r in вер])

# ---------- 4. PR, згадані у файлах дошки сесій перевірки (вердикт у файл не потрапив) ----------
# файл гілки дошки `перевірка-*`/`автоперевірка-*`, доданий у вікні; PR — з шапки й початку тексту його рядків
сесії = []
ф_дат = None
for l in git('log', '--since=2026-11-12', '--diff-filter=A', '--name-only', '--format=@@%H %aI').split('\n'):
    if l.startswith('@@'):
        sha, ф_дат = l[2:].split(' ', 1)
    elif l.startswith('аудит/дошка/') and re.search(r'/(автоперевірка|перевірка|claude-перевірка)[^/]*\.md$', l):
        t = git('show', f'{sha}:{l}')
        шапка = t.split('\n')[0][:300]
        pr_ = set()
        for x in re.findall(r'#(\d{4})', шапка):
            pr_.add(int(x))
        for рядок in t.split('\n'):
            if re.match(r'^\|\s*\d{4,5}\s*\|', рядок):
                кл = [c.strip() for c in рядок.split('|')]
                for x in re.findall(r'#(\d{4})', кл[2][:160] if len(кл) > 2 else ''):
                    pr_.add(int(x))
        сесії.append([l.split('/', 2)[-1], utc(ф_дат), sorted(p for p in pr_ if p in pr_в_вікні)])
пиши('сесії_дошки.csv', ['файл_гілки_дошки', 'дата_utc', 'PR_з_шапки_і_рядків'],
     [[a, b, ' '.join(map(str, c))] for a, b, c in сесії])

# ---------- 5. Codex ----------
codex_рядки = []
for r in csv.DictReader(open(os.path.join(ТУТ, 'сире/codex_інлайн.tsv'), encoding='utf-8'), delimiter='\t'):
    ш = r['шлях']
    клас = клас_файлу(ш) if ш else 'невідомо'
    б = re.search(r'/badge/(P\d)-', r['текст'])
    codex_рядки.append([r['id'], r['PR'], r['створено'], б.group(1) if б else '', ш, клас,
                        re.sub(r'<[^>]*>|!\[[^\]]*\]\([^)]*\)', '', r['текст'])[:600].strip()])
пиши('codex_зауваження.csv', ['id', 'PR', 'створено_utc', 'вага', 'шлях', 'клас_шляху', 'початок_тексту'], codex_рядки)
підс = list(csv.DictReader(open(os.path.join(ТУТ, 'сире/codex_підсумки.tsv'), encoding='utf-8'), delimiter='\t'))
пиши('codex_підсумки.csv', ['id', 'PR', 'створено', 'sha', 'є_знахідки', 'нерозв_знахідки'],
     [[r['id'], r['PR'], r['створено'], r['sha'], r['є_знахідки'], r['нерозв_знахідки']] for r in підс])

# ---------- 6. витрати сесій перевірки (Claude) ----------
витр = []
for ім, колонка in (('сесії_1911.csv', 'cost_у_вікні'), ('сесії_2611.csv', 'cost_usd')):
    for r in csv.DictReader(open(os.path.join(КОРІНЬ, 'аудит/витрати', ім), encoding='utf-8')):
        if r['вид'] != 'перевірка':
            continue
        c = float(r.get(колонка) or 0)
        оцінка = 'оцінка' in r['назва'].lower()
        витр.append([ім, r['id'], r['назва'], r['створено'], r['модель'], r['зусилля'], c, 'оцінка прогону' if оцінка else 'перевірка PR'])
пиши('витрати_перевірок.csv', ['таблиця', 'сесія', 'назва', 'створено', 'модель', 'зусилля', 'cost_usd_у_вікні', 'що'], витр)
# ---------- 7. зауваження: блокуючі вердиктів, рядки дошки перевірки, Codex ----------
комміти_pr = {}
for r in csv.DictReader(open(os.path.join(ТУТ, 'сире/коміти_pr.tsv'), encoding='utf-8'), delimiter='\t'):
    комміти_pr.setdefault(int(r['PR']), []).append(utc(r['дата_коміту_utc']))
pr_злито = {n: (prs[n]['злито'] if n in prs else '') for n in prs}
ПЕРЕВІРЕНО_PR = {}
for r in вер:
    if r['вердикт'] == 'ПЕРЕВІРЕНО':
        ПЕРЕВІРЕНО_PR.setdefault(r['pr'], []).append(r)
вердикти_pr = {}
for r in вер:
    if r['джерело'] != 'коміт-злиття':
        вердикти_pr.setdefault(r['pr'], []).append(r)


def доля_блокуючого(pr, дата_вердикту):
    if pr not in prs:
        return 'поза вікном', 'PR закрито поза вікном'
    if not prs[pr]['злито']:
        return 'PR закрито без злиття', f"закрито {prs[pr]['закрито'][:10]}"
    після = [d for d in комміти_pr.get(pr, []) if d > дата_вердикту]
    if після:
        return 'виправлено до злиття', f'комітів у PR після вердикту: {len(після)}; злито {prs[pr]["злито"][:16]}'
    return 'злито без доробки', f'комітів після вердикту нема; злито {prs[pr]["злито"][:16]}'


зауваження = []
вже = set()
for r in вер:
    if r['вердикт'] not in ('ДОРОБИТИ', 'КОЛО') or r['джерело'] == 'коміт-злиття':
        continue
    for x in [i for i in r['блок'].split(',') if i]:
        if (r['pr'], x) in вже:
            continue
        вже.add((r['pr'], x))
        d = рядки_дошки.get(int(x))
        if not d:
            continue
        д, пояс = доля_блокуючого(r['pr'], r['дата'])
        зауваження.append(['вердикт-блокуюче', f"{r['pr']}:{x}", r['pr'], x, r['звіт'], r['ризик'], r['рушій'],
                           мапа_класу.get(d['рід'], '?'), 'рід дошки: ' + d['рід'], 'так', д, пояс, d['текст']])
for l in open(os.path.join(ТУТ, 'зауваження_ручні.tsv'), encoding='utf-8'):
    l = l.rstrip('\n')
    if not l or l.startswith('#'):
        continue
    pr, основа, клас, текст = l.split('|', 3)
    pr = int(pr)
    в_ = [r for r in вер if r['pr'] == pr and r['звіт'] == основа or (основа.startswith('автоперевірка') and r['pr'] == pr and r['звіт'].startswith(основа))]
    в_ = в_[0] if в_ else None
    дата = в_['дата'] if в_ else ''
    д, пояс = доля_блокуючого(pr, дата)
    зауваження.append(['вердикт-блокуюче', f'{pr}:рука{len(зауваження)}', pr, '', основа, в_['ризик'] if в_ else '',
                       в_['рушій'] if в_ else '', клас, 'рука (за текстом вердикту)', 'так', д, пояс, текст])
блок_id = {int(z[3]) for z in зауваження if z[3]}
pr_з_вердиктом = set(вердикти_pr)
for n, d in sorted(рядки_дошки.items()):
    if d['виявлено'] != 'перевірка' or not ('2026-11-12' <= d['дата'] <= '2026-11-25') or n in блок_id:
        continue
    прв = None
    for k in re.findall(r'#(\d{4})', d['внесено']) + re.findall(r'#(\d{4})', d['текст']):
        if int(k) in pr_з_вердиктом:
            прв = int(k)
            break
    if d['внесено'].strip().startswith('давнє'):
        доля = ('давня вада, не від PR', '«внесено: давнє»')
    elif прв is None:
        доля = ('PR вади не визначено', 'внесено — PR без вердикту перевірки або PR звіту')
    elif прв not in prs:
        доля = ('поза вікном', f'PR {прв} закрито поза вікном')
    elif prs[прв]['злито']:
        доля = ('злито з вадою', f'PR {прв} злито {prs[прв]["злито"][:10]}; рядок {d["статус"] or "?"}')
    else:
        доля = ('PR закрито без злиття', f'PR {прв} закрито без злиття')
    зауваження.append(['дошка-перевірка', str(n), прв or '', n, '', '', '', мапа_класу.get(d['рід'], '?'),
                       'рід дошки: ' + d['рід'], 'ні', доля[0], доля[1], d['текст']])
for r in codex_рядки:
    клас_ш = {'продукт': 'аб', 'прилад': 'в', 'документ': 'г', 'невідомо': '?'}[r[5]]
    pr = int(r[1])
    доля = 'злито' if (pr in prs and prs[pr]['злито']) else ('закрито без злиття' if pr in prs else 'поза вікном')
    зауваження.append(['codex-рецензія', r[0], pr, '', '', '', 'Codex (рецензент)', клас_ш, 'шлях файлу: ' + r[4],
                       'ні', 'PR ' + доля, '', r[6]])
пиши('зауваження.csv', ['джерело', 'ключ', 'PR', 'рядок_дошки', 'звіт', 'ризик', 'рушій', 'клас', 'спосіб_класу',
                        'блокуюче', 'доля', 'пояснення_долі', 'текст'], зауваження)

# ---------- 8. що пройшло крізь ----------
крізь = []
for n, d in sorted(рядки_дошки.items()):
    if d['виявлено'] not in ('живий', 'тестувальниця', 'власник'):
        continue
    for k in re.findall(r'#(\d{4})', d['внесено']):
        k = int(k)
        if k in pr_в_вікні and k in ПЕРЕВІРЕНО_PR:
            в = ПЕРЕВІРЕНО_PR[k][-1]
            крізь.append([n, d['дата'], d['рід'], мапа_класу.get(d['рід'], ''), d['виявлено'], k, в['ризик'], в['рушій'],
                          в['джерело'], 'так' if prs[k]['злито'] else 'ні', d['статус'], d['текст']])
пиши('пройшло_крізь.csv', ['рядок', 'дата', 'рід', 'клас', 'виявлено', 'PR', 'ризик', 'рушій_вердикту', 'джерело_вердикту',
                           'PR_злито', 'статус', 'текст'], крізь)
print('готово:', len(pr_рядки), 'PR,', len(вер), 'вердиктів,', len(рядки_дошки), 'рядків дошки,', len(codex_рядки), 'Codex-зауважень')

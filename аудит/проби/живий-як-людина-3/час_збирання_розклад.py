#!/usr/bin/env python3
"""час_збирання_розклад.md: куди йдуть секунди збирання образів (наряд Час-збирання-розклад).
Дані — лише записи третього живого прогону «як людина» поруч зі скриптом:
  стенд/службове/<сN>/обміни.jsonl.gz     кожен виклик моделі: початок (UTC), секунди, тіло запиту й відповіді
  стенд/журнал_моделі_продукту.jsonl      ті самі виклики: токени з `claude -p` (той самий порядок, що в обмінах)
  <сN>/verdykty-*.json                    вердикти: якій руці (1–4) належить виклик — `етапи.виклики` (точний збіг тексту
                                          запиту) і `мова_шару` (`де`: hand_N, `коли`: початок виклику сторінкою)
  <сN>/хід.md                             час натиску «Зібрати образи» (рядок кроку пишеться одразу після кліку)
  стенд/службове/<сN>/руки.jsonl          перший запис «готово» після проходу (верхня межа показу образів)
Прохід — як у `стенд/час_збирання.py`: від початку першого виклику збирання до кінця останнього, що почався до першого
перекладу вердикту жінки. Додано «від кліку»: клік → палітра стилістки й код → перший виклик збирання.
Запуск: python3 -I час_збирання_розклад.py > час_збирання_розклад_таблиці.md  (лише stdlib; нічого не змінює й не пише)"""
import gzip, json, glob, os, re, datetime as D, statistics as S

БАЗА = os.path.dirname(os.path.abspath(__file__))
ЗБИР = {'assembly', 'repair', 'choice', 'completeness', 'description', 'prose', 'item_list'}
НАЗВА = {
    'assembly': 'каталожні руки 1–2: складання (assembly)',
    'repair': 'каталожні руки 1–2: ремонт (repair)',
    'completeness': 'каталожні руки 1–2: повнота (completeness_repair)',
    'choice': 'каталожні руки 1–2: вибір образу (choice)',
    'description': 'каталожні руки 1–2: опис образу з фото (description)',
    'prose': 'прозові руки 3–4: проза образу (hand_prompt)',
    'item_list': 'прозові руки 3–4: перелік речей (item_list)',
    'lang_texts': 'мовний шар: тексти картки',
    'lang_msgs': 'мовний шар: повідомлення картки (рядки)',
    'palette': 'вибір палітри стилісткою (palette_choice, до проходу)',
}
ПОРЯДОК = ['assembly', 'repair', 'completeness', 'choice', 'description', 'prose', 'item_list', 'lang_texts', 'lang_msgs']


def т(x): return D.datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp()


def текст(q):
    m = json.loads(q)['messages'][0]['content']
    return m if isinstance(m, str) else ' '.join(b.get('text', '') for b in m if isinstance(b, dict))


def вид(з):
    if з.startswith('Photo 1'): return 'description'
    if 'You are a translator in a styling app' in з[:200]: return 'verdict_tr'
    if з.startswith('{"version":"1"'):
        for k, v in (('Build outfits', 'assembly'), ('Improve the outfits', 'repair'),
                     ('Choose one of', 'choice'), ('The code checked', 'completeness')):
            if k in з[:400]: return v
        return 'catalog_other'
    if 'Put together one outfit' in з[:200]: return 'prose'
    if 'You read the description of an outfit' in з[:200]: return 'item_list'
    if 'Ти — перекладачка' in з[:100]:
        if 'тексти, які зараз' in з[:300]: return 'lang_texts'
        if 'рядки, які зараз' in з[:300]: return 'lang_msgs'
        return 'lang_reply'
    if 'She left the colour scheme' in з[:300]: return 'palette'
    if 'live chat' in з[:300]: return 'chat'
    return 'other'


def завантажити():
    J = [json.loads(l) for l in open(БАЗА + '/стенд/журнал_моделі_продукту.jsonl', encoding='utf-8')]
    res = {}
    for d in sorted(glob.glob(БАЗА + '/стенд/службове/*/')):
        s = os.path.basename(d.rstrip('/'))
        L = [json.loads(l) for l in gzip.open(d + 'обміни.jsonl.gz', 'rt', encoding='utf-8')]
        Js = [j for j in J if j['прохід'] == s]
        assert len(L) == len(Js), s
        V = json.load(open(glob.glob(БАЗА + '/' + s + '/verdykty*.json')[0], encoding='utf-8'))
        calls = []
        for i, (o, j) in enumerate(zip(L, Js)):
            з = текст(o['запит']); t0 = т(o['час']); dur = float(o['с'])
            calls.append(dict(s=s, t0=t0, dur=dur, t1=t0 + dur, вид=вид(з), з=з,
                              вх=j['вхід_нових'] + j['вхід_кеш_читання'] + j['вхід_кеш_запис'], вих=j['вихід'],
                              симв_о=j['симв_відповіді'], симв_в=j['промпт_симв'], рука=None, де=None, лаг=None))
        calls.sort(key=lambda c: c['t0'])
        тек = None; n = 0
        for c in calls:
            c['прохід'] = None
            if c['вид'] == 'verdict_tr': тек = None
            elif c['вид'] in ЗБИР and тек is None: n += 1; тек = n; c['прохід'] = n
            elif тек is not None and c['вид'] != 'chat': c['прохід'] = тек
        for pi, p in enumerate(V['прогони'], 1):
            for v in p['вердикти']:
                for x in v['етапи']['виклики']:
                    tx = x['запит']['текст']
                    hit = [c for c in calls if c['прохід'] == pi and c['вид'] in ЗБИР and c['з'] == tx]
                    if not hit: hit = [c for c in calls if c['прохід'] == pi and c['вид'] in ЗБИР and tx in c['з']]
                    if len(hit) == 1: hit[0]['рука'] = v['рука']
                for e in v['мова_шару']:
                    if not e.get('мс'): continue
                    tk = т(e['коли'])
                    near = [c for c in calls if c['прохід'] == pi and c['вид'].startswith('lang') and c['рука'] is None
                            and 0 <= c['t0'] - tk < 3]
                    near.sort(key=lambda c: abs(c['t0'] - tk))
                    if near: near[0]['рука'] = v['рука']; near[0]['де'] = e['де']; near[0]['лаг'] = near[0]['t0'] - tk
        res[s] = calls
    return res


def кліки(s):
    дата = D.datetime(2026, 11, 15, tzinfo=D.timezone.utc).timestamp()
    res = []
    for б in open(БАЗА + '/' + s + '/хід.md', encoding='utf-8').read().split('\n### '):
        m = re.match(r'\d+ · (\d\d):(\d\d):(\d\d) UTC', б)
        if m and 'дія: натиснула «кнопка: Зібрати образи»' in б:
            h, mi, se = map(int, m.groups()); res.append(дата + h * 3600 + mi * 60 + se)
    return res


def готово(s):
    return [т(json.loads(l)['час']) for l in open(БАЗА + '/стенд/службове/' + s + '/руки.jsonl', encoding='utf-8')
            if json.loads(l).get('готово')]


def об_єднання(iv, a, b):
    iv = sorted((max(x, a), min(y, b)) for x, y in iv if y > a and x < b)
    tot = 0; cur = None
    for x, y in iv:
        if cur is None or x > cur[1]:
            if cur: tot += cur[1] - cur[0]
            cur = [x, y]
        else: cur[1] = max(cur[1], y)
    if cur: tot += cur[1] - cur[0]
    return tot


def макс_одночасно(iv):
    ev = sorted([(x, 1) for x, y in iv] + [(y, -1) for x, y in iv], key=lambda e: (e[0], e[1]))
    m = k = 0
    for _, d in ev: k += d; m = max(m, k)
    return m


def мед(x): return S.median(x) if x else 0


def f(x, n=0): return f'{x:.{n}f}'.replace('.', ',') if False else f'{x:.{n}f}'


def прохід_дані(R):
    """усі 16 проходів: клік, виклики, палітра, критична рука, розклад критичного шляху"""
    П = []
    for s, cs in R.items():
        K = кліки(s); G = готово(s)
        for p in (1, 2):
            pc = [c for c in cs if c['прохід'] == p]
            ws = min(c['t0'] for c in pc); we = max(c['t1'] for c in pc); tc = K[p - 1]
            pre = [c for c in cs if tc - 1 <= c['t0'] < ws and c['вид'] == 'palette']
            allc = pre + pc
            крит = max(pc, key=lambda c: c['t1'])['рука']
            # критична рука: де закінчується останній виклик (мовний шар руки)
            hand = sorted([c for c in pc if c['рука'] == крит], key=lambda c: c['t0'])
            hs = hand[0]['t0']
            seg = {}
            def дод(k, d): seg[k] = seg.get(k, 0) + d
            # розклад по 0.05 с: що робить критична рука в кожну мить від кліку до кінця
            крок = 0.05; t = tc
            while t < we:
                mid = t + крок / 2
                акт = [c for c in hand if c['t0'] <= mid < c['t1']]
                if any(c['t0'] <= mid < c['t1'] for c in pre): k = 'palette'
                elif mid < hs:
                    k = 'код_до_перших' if pre and mid < min(c['t0'] for c in pre) else 'код_після_палітри'
                elif акт: k = max(акт, key=lambda c: c['t1'])['вид']
                else: k = 'код_між'
                дод(k, крок); t += крок
            # тривалість критичної руки і ланцюг (послідовні виклики, без паралельних дублів)
            зак = [g for g in G if g >= we]
            П.append(dict(s=s, p=p, tc=tc, ws=ws, we=we, pc=pc, pre=pre, крит=крит, hs=hs, seg=seg,
                          показ=(зак[0] - we) if зак else None,
                          busy=об_єднання([(c['t0'], c['t1']) for c in allc], tc, we),
                          conc=макс_одночасно([(c['t0'], c['t1']) for c in pc])))
    return П


def ols(X, y):
    """найменші квадрати 3×3 (a, b, c) без numpy"""
    n = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(n)] for i in range(n)]
    B = [sum(r[i] * yy for r, yy in zip(X, y)) for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(A[r][i])); A[i], A[p] = A[p], A[i]; B[i], B[p] = B[p], B[i]
        for r in range(i + 1, n):
            k = A[r][i] / A[i][i]
            for c in range(i, n): A[r][c] -= k * A[i][c]
            B[r] -= k * B[i]
    x = [0] * n
    for i in reversed(range(n)):
        x[i] = (B[i] - sum(A[i][j] * x[j] for j in range(i + 1, n))) / A[i][i]
    ym = sum(y) / len(y)
    ss = sum((yy - ym) ** 2 for yy in y)
    sr = sum((yy - sum(a * b for a, b in zip(r, x))) ** 2 for r, yy in zip(X, y))
    return x, 1 - sr / ss


def main():
    R = завантажити(); П = прохід_дані(R)
    позн = lambda p: f"{p['s'].split('_')[0]}·{p['p']}"
    in_pass = [c for cs in R.values() for c in cs if c['прохід']]
    pal = [c for p in П for c in p['pre']]
    print('<!-- таблиці згенеровано `час_збирання_розклад.py`; нічого тут не правиться руками -->\n')
    print(f'Проходів: {len(П)}; викликів у проходах (за `час_збирання.py`): {len(in_pass)}; викликів палітри між кліком і першим '
          f'викликом збирання: {len(pal)}; рук без атрибуції за вердиктами: {sum(1 for c in in_pass if c["рука"] is None)}.\n')

    # ---------- 1. за видом виклику
    print('### 1. За видом виклику (усі 16 проходів)\n')
    print('| вид виклику | викликів | Σ с | частка Σ с проходів | медіана с | найдовший с | вхід, ток (медіана) | вихід, ток (Σ) | вихід, ток (медіана) | вихід, ток/с (Σ/Σ) |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    Σвсі = sum(c['dur'] for c in in_pass)
    рядки = ПОРЯДОК + ['palette']
    for k in рядки:
        cs = [c for c in (pal if k == 'palette' else in_pass) if c['вид'] == k]
        if not cs: continue
        Σ = sum(c['dur'] for c in cs)
        ч = f'{100 * Σ / Σвсі:.0f} %' if k != 'palette' else '—'
        print(f"| {НАЗВА[k]} | {len(cs)} | {Σ:.0f} | {ч} | {мед([c['dur'] for c in cs]):.1f} | {max(c['dur'] for c in cs):.0f} | "
              f"{мед([c['вх'] for c in cs]):.0f} | {sum(c['вих'] for c in cs)} | {мед([c['вих'] for c in cs]):.0f} | "
              f"{sum(c['вих'] for c in cs) / Σ:.0f} |")
    print(f"| **разом у проходах** | {len(in_pass)} | {Σвсі:.0f} | 100 % | {мед([c['dur'] for c in in_pass]):.1f} | "
          f"{max(c['dur'] for c in in_pass):.0f} | {мед([c['вх'] for c in in_pass]):.0f} | {sum(c['вих'] for c in in_pass)} | "
          f"{мед([c['вих'] for c in in_pass]):.0f} | {sum(c['вих'] for c in in_pass) / Σвсі:.0f} |\n")
    print('«Σ с» — сума тривалостей викликів, а не секунди на годиннику: виклики йдуть одночасно (розділ 2). Токени — з `claude -p` '
          '(`вихід` включає приховане міркування моделі: стеля сторінки `max_tokens` стендом не застосовується).\n')

    # ---------- 2. послідовність
    print('### 2. Послідовність і одночасність у проході\n')
    print('| прохід | викликів | клік→перший виклик збирання, с | перший→останній виклик (прохід за `час_збирання.md`), с | клік→кінець останнього виклику, с | '
          'з них хоч один виклик у польоті, с | жоден виклик не йде, с | Σ тривалостей викликів, с | макс. одночасних | рука, що закінчила останньою |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for p in П:
        F = p['we'] - p['tc']
        print(f"| {позн(p)} | {len(p['pc'])} | {p['ws'] - p['tc']:.0f} | {p['we'] - p['ws']:.0f} | {F:.0f} | {p['busy']:.0f} | {F - p['busy']:.0f} | "
              f"{sum(c['dur'] for c in p['pc']) + sum(c['dur'] for c in p['pre']):.0f} | {p['conc']} | {p['крит']} |")
    F_ = [p['we'] - p['tc'] for p in П]; W_ = [p['we'] - p['ws'] for p in П]; B_ = [p['busy'] for p in П]
    print(f"| **медіана** | {мед([len(p['pc']) for p in П]):.0f} | {мед([p['ws'] - p['tc'] for p in П]):.0f} | {мед(W_):.0f} | {мед(F_):.0f} | {мед(B_):.0f} | "
          f"{мед([f - b for f, b in zip(F_, B_)]):.0f} | {мед([sum(c['dur'] for c in p['pc']) + sum(c['dur'] for c in p['pre']) for p in П]):.0f} | {мед([p['conc'] for p in П]):.0f} | |\n")

    # ---------- 3. найдовший виклик
    print('### 3. Найдовший виклик кожного проходу\n')
    print('| прохід | вид | рука | тривалість, с | вихід, ток | ток/с | вхід, ток | відповідь, симв. | частка проходу від кліку |')
    print('|---|---|---|---|---|---|---|---|---|')
    довгі = []
    for p in П:
        c = max(p['pc'], key=lambda c: c['dur']); довгі.append(c)
        print(f"| {позн(p)} | {c['вид']} | {c['рука']} | {c['dur']:.0f} | {c['вих']} | {c['вих'] / c['dur']:.0f} | {c['вх']} | {c['симв_о']} | "
              f"{100 * c['dur'] / (p['we'] - p['tc']):.0f} % |")
    from collections import Counter
    print(f"\nВид найдовшого виклику: {dict(Counter(c['вид'] for c in довгі))}. Медіана: {мед([c['dur'] for c in довгі]):.0f} с, "
          f"{мед([c['вих'] for c in довгі]):.0f} ток вихід, {мед([c['вих'] / c['dur'] for c in довгі]):.0f} ток/с; "
          f"медіана ток/с усіх викликів проходів: {мед([c['вих'] / c['dur'] for c in in_pass]):.0f}.\n")

    # ---------- 4. клік → перший виклик; кінець → показ
    print('### 4. Від кліку до першого виклику й від останнього виклику до показу\n')
    print('| прохід | клік→початок виклику палітри, с | виклик палітри, с | палітра→перший виклик збирання, с | останній виклик→перший запис «готово» у `руки.jsonl`, с (верхня межа) |')
    print('|---|---|---|---|---|')
    for p in П:
        pl = p['pre']
        a = f"{pl[0]['t0'] - p['tc']:.0f}" if pl else '—'
        b = f"{sum(c['dur'] for c in pl):.1f}" if pl else '—'
        cc = f"{p['ws'] - pl[-1]['t1']:.0f}" if pl else f"{p['ws'] - p['tc']:.0f} (палітри нема)"
        sh = f"≤ {p['показ']:.0f}" if p['показ'] is not None else 'нема запису'
        print(f"| {позн(p)} | {a} | {b} | {cc} | {sh} |")
    pk = [p['показ'] for p in П if p['показ'] is not None]
    print(f"\nМедіана: клік→перший виклик збирання {мед([p['ws'] - p['tc'] for p in П]):.0f} с; "
          f"верхня межа «останній виклик→готово»: медіана {мед(pk):.0f} с, мін {min(pk):.0f}, макс {max(pk):.0f} (запис `руки.jsonl` ставить крок опитування жінки з очікуванням 5–90 с, тож це стеля, не вимір).\n")
    лаг = [c['лаг'] for c in in_pass if c['лаг'] is not None]
    print(f"Затримка «сторінка викликала → стенд почав» для викликів мовного шару ({len(лаг)} з `мова_шару.коли`): медіана {мед(лаг):.2f} с, макс {max(лаг):.2f} с.\n")

    # ---------- 5. стенд чи будова
    print('### 5. Властивість стенда чи будова продукту\n')
    X = [[1, c['вих'], c['вх'] / 1000] for c in in_pass]; y = [c['dur'] for c in in_pass]
    (a, b, cc_), r2 = ols(X, y)
    print(f"Регресія тривалості виклику по всіх {len(in_pass)} викликах проходів: `с = a + b·вихід_ток + c·вхід_ктток`: a = {a:.1f} с (накладні одного виклику), "
          f"1/b = {1 / b:.0f} ток/с (швидкість виходу), c = {cc_:.2f} с на 1000 токенів входу; R² = {r2:.2f}.\n")
    by = {}
    for k in ПОРЯДОК:
        cs = [c for c in in_pass if c['вид'] == k]
        if len(cs) < 3: continue
        by[k] = cs
    print('| вид | мін. тривалість, с | медіана ток/с | вихід видимий (≈симв/3,3), ток | вихід усього, ток | частка прихованого, % (оцінка) |')
    print('|---|---|---|---|---|---|')
    for k, cs in by.items():
        вид_ = [c['симв_о'] / 3.3 for c in cs]
        print(f"| {k} | {min(c['dur'] for c in cs):.1f} | {мед([c['вих'] / c['dur'] for c in cs]):.0f} | {мед(вид_):.0f} | {мед([c['вих'] for c in cs]):.0f} | "
              f"{100 * max(0, 1 - sum(вид_) / sum(c['вих'] for c in cs)):.0f} |")
    # одночасність з іншими ситуаціями стенда
    всі = [(c['t0'], c['t1']) for cs in R.values() for c in cs]
    def інші(c):
        return sum(1 for cs in R.values() for o in cs if o['s'] != c['s'] and o['t0'] <= c['t0'] < o['t1'])
    for c in in_pass: c['інші'] = інші(c)
    низ = [c for c in in_pass if c['вид'] in ('assembly', 'description', 'lang_texts') and c['інші'] <= 2]
    вис = [c for c in in_pass if c['вид'] in ('assembly', 'description', 'lang_texts') and c['інші'] > 2]
    print(f"\nОдночасні виклики інших ситуацій на старті виклику (3 ситуації йшли разом): ≤2 — {len(низ)} викликів (assembly/description/lang_texts), "
          f"медіана {мед([c['вих'] / c['dur'] for c in низ]):.0f} ток/с; >2 — {len(вис)}, медіана {мед([c['вих'] / c['dur'] for c in вис]):.0f} ток/с.\n")

    # ---------- розклад: куди йдуть секунди
    print('### Куди йдуть секунди (клік «Зібрати образи» → кінець останнього виклику)\n')
    cats = [('код_до_перших', 'код від кліку до виклику палітри (сторінка)'),
            ('palette', 'виклик: вибір палітри стилісткою'),
            ('код_після_палітри', 'код від кліку (або від кінця палітри) до першого виклику руки, що закінчила останньою (`містП("запити")`: пул і промпти)'),
            ('assembly', 'виклик: складання (assembly)'), ('prose', 'виклик: проза рук 3–4'),
            ('repair', 'виклик: ремонт (repair)'), ('completeness', 'виклик: повнота'), ('choice', 'виклик: вибір образу (choice)'),
            ('item_list', 'виклик: перелік речей'), ('description', 'виклик: опис з фото (description)'),
            ('lang_texts', 'виклик: мовний шар — тексти картки'), ('lang_msgs', 'виклик: мовний шар — повідомлення'),
            ('код_між', 'код між викликами руки (перевірка відповіді, наступний промпт, фото)')]
    Fs = sorted(П, key=lambda p: p['we'] - p['tc']); mp = Fs[len(Fs) // 2 - 1], Fs[len(Fs) // 2]
    mp = min(П, key=lambda p: abs((p['we'] - p['tc']) - мед(F_)))
    Fm = mp['we'] - mp['tc']
    print(f"Критичний шлях = руки, що закінчила останньою (у кожному проході — каталожна рука). Медіанний за клік→кінець прохід — {позн(mp)} ({Fm:.0f} с).\n")
    print(f'| куди йде час | с у проході {позн(mp)} | частка | медіана по 16 проходах, с | частка від медіани F | мін–макс, с |')
    print('|---|---|---|---|---|---|')
    tot = {}
    for k, n in cats:
        v = [p['seg'].get(k, 0) for p in П]
        tot[k] = v
        if not any(v): continue
        print(f"| {n} | {mp['seg'].get(k, 0):.0f} | {100 * mp['seg'].get(k, 0) / Fm:.0f} % | {мед(v):.0f} | {100 * мед(v) / мед(F_):.0f} % | {min(v):.0f}–{max(v):.0f} |")
    print(f"| **разом** | {Fm:.0f} | 100 % | {мед(F_):.0f} | | {min(F_):.0f}–{max(F_):.0f} |\n")
    м_викл = [sum(p['seg'].get(k, 0) for k, _ in cats if k not in ('код_до_перших', 'код_після_палітри', 'код_між')) for p in П]
    м_код = [F - m for F, m in zip(F_, м_викл)]
    print(f"Виклики моделі на критичному шляху: медіана {мед(м_викл):.0f} с із {мед(F_):.0f} с ({100 * мед(м_викл) / мед(F_):.0f} %); код без жодного виклику цієї руки: медіана {мед(м_код):.0f} с ({100 * мед(м_код) / мед(F_):.0f} %). "
          f"У медіанному проході: {sum(mp['seg'].get(k, 0) for k, _ in cats if k not in ('код_до_перших', 'код_після_палітри', 'код_між')):.0f} с у викликах, "
          f"{Fm - sum(mp['seg'].get(k, 0) for k, _ in cats if k not in ('код_до_перших', 'код_після_палітри', 'код_між')):.0f} с — код.\n")
    вікно = [sum(p['seg'].get(k, 0) for k, _ in cats if k not in ('код_до_перших', 'код_після_палітри', 'код_між', 'palette')) / (p['we'] - p['ws']) for p in П]
    print(f"У вікні проходу за `час_збирання.md` (перший→останній виклик збирання) руки, що закінчила останньою, виклики моделі займають: медіана {100 * мед(вікно):.0f} % вікна (мін {100 * min(вікно):.0f}, макс {100 * max(вікно):.0f}); "
          f"решта вікна — код між її викликами.\n")
    перші = [p['ws'] - p['tc'] for p in П if p['p'] == 1]; другі = [p['ws'] - p['tc'] for p in П if p['p'] == 2]
    print(f"Клік→перший виклик збирання: перший прохід ситуації — медіана {мед(перші):.0f} с ({min(перші):.0f}–{max(перші):.0f}), другий — медіана {мед(другі):.0f} с ({min(другі):.0f}–{max(другі):.0f}).\n")
    # довжина ланцюга
    лан = [len([c for c in p['pc'] if c['рука'] == p['крит'] and c['вид'] in ('assembly', 'repair', 'completeness', 'choice', 'description')]) for p in П]
    лан2 = [len([c for c in p['pc'] if c['рука'] == p['крит']]) for p in П]
    print(f"Послідовних викликів у ланцюзі руки, що закінчила останньою: складання→ремонт→[повнота]→вибір→опис = {мед(лан):.0f} (мін {min(лан)}, макс {max(лан)}), разом із мовним шаром {мед(лан2):.0f}; "
          f"із палітрою до них — на один більше, коли палітру питали.\n")
    # частка викликів в проході (для листа)
    ч_викл = [sum(c['dur'] for c in p['pc']) for p in П]
    print(f"Σ тривалостей викликів / клік→кінець: медіана {мед([a / (p['we'] - p['tc']) for a, p in zip(ч_викл, П)]):.1f}× (одночасність).\n")
    # ---------- залежності: пари виклик→наступний
    print('### Послідовні виклики однієї руки: проміжок між кінцем виклику й початком наступного (код між викликами)\n')
    print('| перехід (за залежністю входу від виходу) | пар | медіана проміжку, с | макс, с |')
    print('|---|---|---|---|')
    пари = {}
    for p in П:
        for h in ('1', '2', '3', '4'):
            ch = sorted([c for c in p['pc'] if c['рука'] == h and c['вид'] != 'lang_msgs'], key=lambda c: c['t0'])
            for u, v in zip(ch, ch[1:]):
                if v['t0'] >= u['t1'] - 0.01:
                    пари.setdefault(f"{u['вид']} → {v['вид']}", []).append(v['t0'] - u['t1'])
    for k, v in sorted(пари.items(), key=lambda kv: -len(kv[1])):
        print(f"| {k} | {len(v)} | {мед(v):.1f} | {max(v):.1f} |")
    # зсув старту другої каталожної руки відносно першої
    print('\n### Старт каталожних рук: зсув другої відносно першої\n')
    зс = []; пізня_крит = 0
    for p in П:
        ст = sorted([(min(c['t0'] for c in p['pc'] if c['рука'] == h), h) for h in ('1', '2')])
        зс.append(ст[1][0] - ст[0][0]); пізня_крит += (p['крит'] == ст[1][1])
    пр = []
    for p in П:
        m = [min(c['t0'] for c in p['pc'] if c['рука'] == h) for h in ('3', '4')]
        пр.append(min(m) - min(min(c['t0'] for c in p['pc'] if c['рука'] == h) for h in ('1', '2')))
    print(f"Друга каталожна рука починає перший виклик на {мед(зс):.0f} с (мін {min(зс):.0f}, макс {max(зс):.0f}) пізніше за першу; у {пізня_крит} із 16 проходів останньою закінчує саме друга за часом старту. "
          f"Перша прозова рука починає на {мед(пр):.0f} с пізніше за першу каталожну (мін {min(пр):.0f}, макс {max(пр):.0f}).")
    # прозові і каталожні руки: кінець руки
    print('\n### Довжина ланцюга кожної руки, с (початок першого → кінець останнього виклику руки)\n')
    print('| прохід | рука 1 | рука 2 | рука 3 | рука 4 |')
    print('|---|---|---|---|---|')
    for p in П:
        ря = []
        for h in ('1', '2', '3', '4'):
            ch = [c for c in p['pc'] if c['рука'] == h]
            ря.append(f"{min(c['t0'] for c in ch) - p['tc']:.0f}→{max(c['t1'] for c in ch) - p['tc']:.0f}" if ch else '—')
        print(f"| {позн(p)} | " + ' | '.join(ря) + ' |')
    print('\n(числа — секунди від кліку; ключ: рука 1–2 — каталожні, 3–4 — прозові)')


if __name__ == '__main__':
    main()

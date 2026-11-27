# Розбір одного проходу стенда (пункти 1, 2, 4 наряду). Вхід — тека проходу (`сцена.sh`): обміни.jsonl, часи.json, стан.json, лог.txt.
# Вихід — JSON у stdout: виклики моделі (вид, початок, кінець, токени), кроки Python, секунди до карток за критичним
# шляхом, склад запиту складання за частинами й колонками пулу, спільний початок запитів (для кешу).
# Запуск: python3 розбір.py <тека> > <тека>.json
import json, re, sys, collections, datetime

тека = sys.argv[1].rstrip('/')


def мс(iso):
    return datetime.datetime.fromisoformat(iso.replace('Z', '+00:00')).timestamp() * 1000


ВИДИ = [  # (початок запиту або ключ у перших 600 знаках, вид)
    ('You read a woman', 'розмова: Ч1 (поля ситуації)'),
    ('"role": "You are the stylist of a styling app in a live chat', 'розмова: хід стилістки'),
    ('Ти — перекладачка', 'переклад'),
    ('She left the colour scheme', 'вибір палітри'),
    ('Build outfits for her case', 'складання руки'),
    ('Improve the outfits using the supplied verdicts', 'ремонт'),
    ('Choose one of the offered outfits', 'вибір образу'),
    ('Explain the chosen outfit', 'пояснення образу (без фото)'),
    ('Put together one outfit for her case', 'рука 3–4: проза'),
    ('list its items as data', 'рука 3–4: перелік речей'),
]


def вид(запит):
    if запит.startswith('Catalogue photo'):
        return 'пояснення образу (з фото)'
    гол = запит[:700]
    for к, в in ВИДИ:
        if к in гол:
            return в
    if 'Catalogue photo' in запит[:60]:
        return 'пояснення образу (з фото)'
    return 'інше: ' + гол[:60].replace('\n', ' ')


обміни = []
for р in open(f'{тека}/обміни.jsonl', encoding='utf8'):
    д = json.loads(р)
    if 'с' not in д:
        continue
    u = д.get('usage') or {}
    поч = мс(д['час'])
    обміни.append(dict(вид=вид(д['запит']), поч=поч, кін=поч + д['с'] * 1000, с=д['с'], симв=len(д['запит']),
                       вхід_ток=(u.get('input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0),
                       кеш_запис=u.get('cache_creation_input_tokens') or 0, кеш_читання=u.get('cache_read_input_tokens') or 0,
                       вихід_ток=u.get('output_tokens') or 0, думка_ток=(u.get('output_tokens_details') or {}).get('thinking_tokens') or 0,
                       фото=д.get('фото') or 0, статус=д['статус'], запит=д['запит'], відповідь=д['відповідь']))
ч = json.load(open(f'{тека}/часи.json'))
т0 = ч['т0']
лог = open(f'{тека}/лог.txt', encoding='utf8').read()
м = re.search(r'КЛІК_МС (\d+)', лог)
клік = float(м.group(1)) if м else т0
картки = [е for е in ч['події'] if е['к'] == 'картки' and е.get('н', 0) > 0]
кін_карток = картки[0]['т'] if картки else None
python = [dict(ім=п[0], поч=п[1], кін=п[2]) for п in ч['python'] if п[1] >= клік - 50]

# ── виклики після кліку; паралельність
після = sorted([о for о in обміни if о['кін'] > клік and о['поч'] >= клік - 200], key=lambda о: о['поч'])
for о in після:
    о['паралельно_з'] = [i for i, ін in enumerate(після) if ін is not о and ін['поч'] < о['кін'] and ін['кін'] > о['поч']]

# ── критичний шлях: у кожен зріз часу — діяльність, що кінчається найпізніше; без діяльності — «поза викликами»
меж = sorted({клік, кін_карток} | {x for о in після for x in (о['поч'], о['кін'])} | {x for п in python for x in (п['поч'], п['кін'])})
меж = [x for x in меж if клік <= x <= кін_карток]
сума = collections.Counter()
сума_python_за_сусідом = collections.Counter()


def сусід(п):
    # Python-крок називаємо за останнім викликом моделі, що скінчився до нього, і першим, що почався після
    до = [о for о in після if о['кін'] <= п['поч'] + 5]
    пот = [о for о in після if о['поч'] >= п['кін'] - 5]
    а = до[-1]['вид'] if до else 'клік'
    б = пот[0]['вид'] if пот else 'картки'
    return f'код після «{а}» до «{б}»'


for a, b in zip(меж, меж[1:]):
    сер = (a + b) / 2
    акт = [('модель', о['кін'], о['вид']) for о in після if о['поч'] <= сер <= о['кін']]
    акт += [('код', п['кін'], сусід(п)) for п in python if п['поч'] <= сер <= п['кін'] and п['кін'] - п['поч'] > 20]
    if акт:
        к = max(акт, key=lambda x: (x[1], x[0] == 'модель'))
        сума[(к[0], к[2])] += (b - a) / 1000
    else:
        сума[('поза', 'поза викликами й кодом (показ, черга, очікування сторінки)')] += (b - a) / 1000

# ── склад запиту складання
складання = [о for о in обміни if о['вид'] == 'складання руки' and о['кін'] > клік]
склад = []
for о in складання:
    q = json.loads(о['запит'])
    c = lambda x: len(json.dumps(x, ensure_ascii=False, separators=(',', ':')))
    ч_ = {к: c(в) for к, в in q.items() if к != 'pool'}
    пул = q['pool']
    кол = {}
    for назва, ряд in zip(пул['cols'], zip(*пул['rows'])):
        кол[назва] = sum(c(в) + 1 for в in ряд)
    склад.append(dict(симв=о['симв'], вхід_ток=о['вхід_ток'], ток_на_симв=round(о['вхід_ток'] / о['симв'], 4), кандидатів=len(пул['rows']),
                      частини_симв=ч_, пул_симв=c(пул), колонки_симв=кол, колонки=пул['cols']))

# ── спільний початок запитів однакових видів (скільки симв. може піти з кешем)
спільне = []
for в in ('складання руки', 'ремонт', 'вибір образу', 'пояснення образу (з фото)'):
    ц = [о for о in після if о['вид'] == в]
    for о in ц:
        for ін in після:
            if ін is not о and ін['поч'] < о['поч'] and (ін['вид'], ін['поч']) != (в, о['поч']):
                n = 0
                for x, y in zip(о['запит'], ін['запит']):
                    if x != y:
                        break
                    n += 1
                if n > 2000:
                    спільне.append(dict(вид=в, симв=о['симв'], з=ін['вид'], спільний_початок=n, ток_кеш_читання=о['кеш_читання']))

# ── суд: вироки руки 1 з першого запиту ремонту (є — коли суд знайшов що ремонтувати) або вибору
суд = None
for ключ in ('Improve the outfits', 'Choose one of the offered'):
    ц = [о for о in після if ключ in о['запит'][:700]] if ключ else []
    if ц:
        q = json.loads(ц[0]['запит'])
        вр = q.get('verdict') or []
        зн = [[ф for ф in в.get('findings', []) if not ф.get('withheld') and ф.get('weight', 0) > 0] for в in вр]
        суд = dict(джерело=ц[0]['вид'], образів=len(вр), без_знахідок=sum(1 for з in зн if not з),
                   знахідок_на_образ=round(sum(len(з) for з in зн) / len(вр), 2) if вр else None,
                   коди=dict(collections.Counter(ф['code'] for з in зн for ф in з).most_common(8)))
        break
ст = json.load(open(f'{тека}/стан.json'))
вихід = dict(тека=тека, клік_мс=клік, т0=т0, до_карток_с=round((кін_карток - клік) / 1000, 1) if кін_карток else None,
             діагноз_ядра=ст.get('діагноз'),
             виклики=[{k: (round((v - клік) / 1000, 1) if k in ('поч', 'кін') else v) for k, v in о.items() if k not in ('запит', 'відповідь')} for о in після],
             python_кроки=[dict(ім=п['ім'], поч=round((п['поч'] - клік) / 1000, 1), кін=round((п['кін'] - клік) / 1000, 1), с=round((п['кін'] - п['поч']) / 1000, 1)) for п in python if п['кін'] - п['поч'] > 100],
             критичний_шлях=[dict(вид=к[1], джерело=к[0], с=round(v, 1)) for к, v in sorted(сума.items(), key=lambda x: -x[1])],
             склад_запиту_складання=склад, спільний_початок=спільне,
             картки=len(ст.get('картки') or []), суд=суд)
json.dump(вихід, sys.stdout, ensure_ascii=False, indent=1)

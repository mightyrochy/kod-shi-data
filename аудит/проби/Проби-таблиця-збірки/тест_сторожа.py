"""Сторож таблиці (`джерела/прилади/сторож_таблиці.py`): збіг — тиша, байт коду, файл даних, відсутня чи битa таблиця — зупинка з
причиною, явна згода — повільний шлях. Самодостатня: теку й таблицю будує сама.  python3 -I аудит/проби/Проби-таблиця-збірки/тест_сторожа.py"""
import gzip, hashlib, json, os, sys, tempfile

КОРІНЬ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(КОРІНЬ, 'джерела', 'прилади'))
import сторож_таблиці as С


def тека_збірки(змінити=None):
    т = tempfile.mkdtemp(prefix='сторож_')
    код, дані = b'x = 1\n', b'{"k": 1}'
    open(os.path.join(т, 'колір_тон.py'), 'wb').write(код)
    open(os.path.join(т, 'каталог_дані.json'), 'wb').write(дані)
    ключ = dict(код={'колір_тон': hashlib.md5(код).hexdigest()}, дані={'каталог_дані.json': hashlib.md5(дані).hexdigest(), 'нема.json': None})
    with gzip.open(os.path.join(т, С.ТАБЛИЦЯ), 'wt', encoding='utf-8') as ф:
        json.dump(dict(версія=1, ключ=ключ), ф)
    if змінити:
        змінити(т)
    return т


def падає(т, частина):
    try:
        С.вимагати(т)
    except SystemExit as е:
        assert частина in str(е), str(е)
        return
    raise AssertionError('сторож мовчить: ' + частина)


assert С.розбіжність(тека_збірки()) is None
# байт у кінці модуля (коментар) — 15018: таблиця застаріла, і запуск має зупинитися
падає(тека_збірки(lambda т: open(os.path.join(т, 'колір_тон.py'), 'ab').write(b'# x')), 'змінився код побудови: колір_тон')
падає(тека_збірки(lambda т: open(os.path.join(т, 'каталог_дані.json'), 'ab').write(b' ')), 'змінились дані побудови: каталог_дані.json')
падає(тека_збірки(lambda т: open(os.path.join(т, 'нема.json'), 'wb').write(b'1')), "з'явився")
падає(тека_збірки(lambda т: os.remove(os.path.join(т, С.ТАБЛИЦЯ))), 'нема у теці ' + С.ТАБЛИЦЯ)
падає(тека_збірки(lambda т: open(os.path.join(т, С.ТАБЛИЦЯ), 'wb').write(b'not gzip')), 'не читається')
# явна згода — повертає причину, не зупиняє
т = тека_збірки(lambda т: os.remove(os.path.join(т, С.ТАБЛИЦЯ)))
assert 'нема' in С.вимагати(т, дозволити_повільний=True)
os.environ['ТАБЛИЦЯ_ПОВІЛЬНИЙ'] = '1'
assert 'нема' in С.вимагати(т)
print('сторож таблиці: звірки (код, дані, фід, нема, битa, згода) — так')

# фід: md5 має збігатися з ключ.фід; інший фід — зупинка (15229)
т = тека_збірки(); ф = os.path.join(т, 'фід.xml'); open(ф, 'wb').write(b'<a/>')
assert 'фід інший' in С.розбіжність(т, фід=ф)
ключ_ф = lambda т: None
with gzip.open(os.path.join(т, С.ТАБЛИЦЯ), 'rt', encoding='utf-8') as г: тб = json.load(г)
тб['ключ']['фід'] = hashlib.md5(b'<a/>').hexdigest()
with gzip.open(os.path.join(т, С.ТАБЛИЦЯ), 'wt', encoding='utf-8') as г: json.dump(тб, г)
assert С.розбіжність(т, фід=ф) is None
open(ф, 'ab').write(b' ')
assert 'фід інший' in С.розбіжність(т, фід=ф)

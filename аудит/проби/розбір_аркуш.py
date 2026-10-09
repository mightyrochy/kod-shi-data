# -*- coding: utf-8 -*-
# Аркуш звірки розбору каталогу очима (п.10 CLAUDE.md; наряд К-2, рішення власника 27.09): на кожну річ прогону —
# фото, яке показує КАРТКА (`фід_фото.кадри_речі` — той самий вибір, що в `огляд_крамниць.py`), крамниця й назва
# речі, рядок особливостей `features` двох моделей поруч і 5 головних кодів обох; під спойлером — текст крамниці,
# який бачила модель (`каталог_розбір.вхід`). Питання аркуша: чи рядок ловить, чим річ особлива на фото, і чи нема в
# ньому нічого понад текст крамниці. Фото вбудовані (зменшені, base64) — аркуш відкривається без мережі.
# Запуск: python3 аудит/проби/розбір_аркуш.py <тека MamayLM> <тека Lapa> <аркуш.html>
#   (теки — від `джерела/каталог_розбір_прогін.py`, та сама вибірка; `розбір.json` кожної перезбирається тут же;
#    потрібні curl, мережа і PIL — без PIL фото стоять посиланнями на крамницю; ~3–5 хв на 300 речей)
import sys, os, json, html, base64, hashlib, io, subprocess, collections, concurrent.futures as cf
if len(sys.argv) != 4:
    sys.exit('треба: <тека MamayLM> <тека Lapa> <аркуш.html>')
ТЕКИ, ВИХІД = [os.path.abspath(т) for т in sys.argv[1:3]], os.path.abspath(sys.argv[3])
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'джерела')
sys.path.insert(0, Д); os.chdir(Д); os.makedirs('/tmp/фото_огляд', exist_ok=True)
import feed as F; F.каталог_на_диску('каталог_повний.xml')
import фід_фото as ФФ, каталог_розбір as КР, каталог_розбір_прогін as П
try:
    from PIL import Image
except ImportError:
    Image = None
    print('PIL нема: фото стоятимуть посиланнями на крамницю (аркуш без мережі їх не покаже)')
_оф = F.читати_yml('каталог_повний.xml')[0]
_зб, _спільні, _хости = F.читати_збагачення(), ФФ._спільні_фото(_оф), ФФ._хости_крамниць(_оф)
_за_ід = {o['id']: o for o in _оф}
def фото_картки(o):
    z = _зб.get(o.get('id')) or {}
    р = ФФ.кадри_речі(o, _спільні.get(o.get('магазин')) or {}, _хости, z.get('кадр_кольору') or z.get('фото'))
    return р[0] if р else None
# ── ДВА ПРОГОНИ: ТА САМА ВИБІРКА, РОЗБІР ЗБИРАЄТЬСЯ ТИМ САМИМ ЗБИРАЧЕМ ──────────────────────────────────────────
прогони = []
for т in ТЕКИ:
    мірка = json.load(open(os.path.join(т, 'прогін.json'), encoding='utf-8'))
    розбір = json.load(open(П.зібрати(т), encoding='utf-8'))
    ім = мірка['модель'].split('-')[0]
    прогони.append((ім + ('²' if прогони and прогони[0][0] == ім else ''), мірка, розбір))   # мітки різні завжди
іди = [[р['id'] for р in м['речі']] for _, м, _ in прогони]
ВИБІРКА = ('та сама в обох теках (%d речей)' % len(іди[0]) if іди[0] == іди[1] else
           'РІЗНА: %d і %d речей, спільних %d' % (len(іди[0]), len(іди[1]), len(set(іди[0]) & set(іди[1]))))
print('вибірка:', ВИБІРКА)
група = {р['id']: р['група'] for _, м, _ in прогони for р in м['речі']}
речі = [_за_ід[і] for і in dict.fromkeys(іди[0] + іди[1]) if і in _за_ід]
def вид(розбір, і):
    """(вид форми рядка, повні причини) — з причин збирача, тими самими словами, що в пробах."""
    пр = [п for п in розбір[П.ПРИЧИНИ].get(і, []) if п.startswith('features:')]
    if і not in розбір:                                 # поза вибіркою цієї теки, не JSON або впалий виклик
        return 'нема полів', '; '.join(розбір[П.ПРИЧИНИ].get(і, []))
    return ('+'.join(п.split(' — ')[0][10:] for п in пр)
            or ('unknown' if розбір[і][КР.ОСОБЛИВОСТІ] == КР.UNKNOWN else 'прийнято')), '; '.join(пр)
# ── ФОТО: ТЕ САМЕ, ЩО НА КАРТЦІ; ЗМЕНШЕНЕ Й ВБУДОВАНЕ ────────────────────────────────────────────────────────
def шлях(u): return '/tmp/фото_огляд/' + hashlib.md5(u.encode()).hexdigest() + '.img'
def тягти(u):
    p = шлях(u)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        subprocess.run(['curl', '-sS', '-L', '-m', '40', '-o', p, u], capture_output=True)
    return p
урли = {o['id']: фото_картки(o) for o in речі}
if Image:
    with cf.ThreadPoolExecutor(12) as ex: list(ex.map(тягти, [u for u in урли.values() if u]))
лічба_фото = collections.Counter()
def img(u):
    if not u:
        лічба_фото['на картці без фото'] += 1
        return '<div class="nf">на картці без фото</div>'
    if Image:
        try:
            im = Image.open(шлях(u)).convert('RGB'); im.thumbnail((360, 480)); б = io.BytesIO()
            im.save(б, 'JPEG', quality=72); лічба_фото['вбудовано'] += 1
            return '<img src="data:image/jpeg;base64,%s">' % base64.b64encode(б.getvalue()).decode()
        except Exception as е:                           # noqa: BLE001 — бите фото теж факт аркуша
            лічба_фото['не відкрилось: %s' % type(е).__name__] += 1
    else:
        лічба_фото['посиланням'] += 1
    return '<img src="%s" loading="lazy">' % html.escape(u)
# ── АРКУШ ────────────────────────────────────────────────────────────────────────────────────────────────────
КОДИ = ('item_type', 'color_main', 'fabric', 'pattern', 'cut')
def код(поля, к):
    if not поля:
        return '—'
    в = поля.get(к)
    if к == 'fabric' and в == КР.UNKNOWN and поля.get('material') != КР.UNKNOWN:
        return 'm:%s' % поля.get('material')                # взуття, сумка, пояс — матеріал верху
    return '·' if в == КР.UNKNOWN else в
картки, види = [], {ім: collections.Counter() for ім, _, _ in прогони}
for н, o in enumerate(речі, 1):
    і, рядки = o['id'], []
    for ім, _, розбір in прогони:
        в, повні = вид(розбір, і); види[ім][в] += 1
        ф = (розбір.get(і) or {}).get(КР.ОСОБЛИВОСТІ, КР.UNKNOWN)
        мітка = '' if в in ('прийнято', 'unknown') else '<span class="w" title="%s">%s</span>' % (
            html.escape(повні), html.escape(в))
        рядки.append('<div class="f"><b>%s</b> <span class="%s">%s</span>%s</div>' % (
            ім, 'u' if ф == КР.UNKNOWN else 'fx', html.escape(ф), мітка))
    рядки_кодів = []
    for к in КОДИ:                                      # рядок — код, стовпець — модель; розбіжні — підсвічено
        в = [str(код(р.get(і), к)) for _, _, р in прогони]
        рядки_кодів.append('<tr><th>%s</th>%s</tr>' % (к, ''.join(
            '<td%s>%s</td>' % (' class="d"' if len(set(в)) > 1 else '', html.escape(х)) for х in в)))
    таблиця = '<table><tr><th></th>%s</tr>%s</table>' % (
        ''.join('<th>%s</th>' % ім for ім, _, _ in прогони), ''.join(рядки_кодів))
    текст = html.escape(json.dumps(КР.вхід(o, 'uk'), ensure_ascii=False, indent=1))
    фото = img(урли[і])
    if урли[і]:
        фото = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(урли[і]), фото)   # оригінал — з мережею
    картки.append('<div class="k"><div class="ph">%s</div><div class="t"><div class="m">#%d · %s · %s · %s</div>'
                  '<div class="n">%s</div>%s</div>%s<details><summary>текст крамниці, який бачила модель</summary>'
                  '<pre>%s</pre></details></div>' % (
                      фото, н, html.escape(група.get(і, '')), html.escape(o.get('магазин') or ''),
                      html.escape(і.split('@')[0]), html.escape(html.unescape(o.get('назва') or '')), ''.join(рядки),
                      таблиця, текст))
підсумок = ' · '.join('%s (%s): %s' % (ім, html.escape(м['модель']), ', '.join('%s %d' % kv for kv in види[ім].most_common()))
                      for ім, м, _ in прогони)
СТИЛЬ = ('body{font:14px/1.4 system-ui,sans-serif;margin:16px;background:#f6f6f6;color:#222}'
         '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,380px),1fr));gap:12px}'
         '.k{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px;display:grid;'
         'grid-template-columns:170px 1fr;gap:10px}.ph img{width:170px;max-height:230px;object-fit:contain}'
         '.nf{width:170px;height:120px;background:#eee;color:#b00;display:flex;align-items:center;justify-content:center}'
         '.t{min-width:0;overflow-wrap:anywhere}.m{font-size:12px;color:#666}.n{font-weight:600;margin:2px 0 6px}'
         '.f{margin:3px 0}.f b{color:#555}.fx{background:#eef6ff}.u{color:#999;font-style:italic}'
         '.w{font-size:11px;background:#fde68a;border-radius:4px;padding:0 4px;margin-left:4px}'
         'table{grid-column:1/-1;width:100%;table-layout:fixed;border-collapse:collapse;font-size:12px}'
         'td,th{border:1px solid #eee;padding:1px 4px;text-align:left;overflow-wrap:anywhere}'
         'th:first-child{width:78px;color:#666;font-weight:400}.d{background:#ffe4e6}'
         'details{grid-column:1/-1;font-size:12px}'
         'pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:320px;overflow:auto;background:#fafafa}'
         '@media(max-width:420px){body{margin:8px}.g{grid-template-columns:1fr}.k{grid-template-columns:1fr}}')
with open(ВИХІД, 'w', encoding='utf-8') as ф:
    ф.write('<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" '
            'content="width=device-width,initial-scale=1"><title>Розбір: рядок особливостей</title><style>%s</style>'
            '</head><body><h1>Рядок особливостей: %d речей</h1><p>Вибірка: %s.<br>%s</p><p class="m">Коди: %s (m: — матеріал верху, '
            '· — unknown; рожевим — моделі розійшлись). Фото: %s.</p><div class="g">%s</div></body></html>' % (
                СТИЛЬ, len(речі), ВИБІРКА, підсумок, ', '.join(КОДИ), ', '.join('%s %d' % kv for kv in лічба_фото.items()),
                ''.join(картки)))
print('аркуш: %s · речей %d · %s · фото: %s · %.1f МБ' % (ВИХІД, len(речі), підсумок, dict(лічба_фото),
                                                         os.path.getsize(ВИХІД) / 1e6))

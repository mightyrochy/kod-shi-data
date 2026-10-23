"""5192: межа ознак #1028 — поле запису → ключі фіда, поле розбору, споживачі на main, якість на еталоні 404; 5191 — тип."""
import ast, collections as C, glob, gzip, json, os, re, sys
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д); os.chdir(Д)
import feed as F, фід_каталог as ФК, каталог_розбір as КР, каталог_розбір_прогін as П, profile, внутрішня_мова as ВМ
ЕТ = os.path.join(Д, 'проби', 'еталон_частки.py'); РЗ = os.path.join(Д, '..', 'аудит', 'розбір_каталогу')
exec(compile(ast.Module([в for в in ast.parse(open(ЕТ, encoding='utf-8').read()).body if isinstance(в, ast.FunctionDef)], []), ЕТ, 'exec'))
# поле запису, що міняє #1028 | підрядки імен param-джерела | поле схеми розбору («нема» — нема) | поле еталону 404 (- не міряється)
ПОЛЯ = [р.split('|') for р in ('матеріал|склад,матеріал,тканин|fabric|fabric;волокно|склад,матеріал,тканин|fabric|fabric;еластан_%|склад|elastane_pct|-;вовна_частка|склад,вовн|wool_pct|-;сезон_тканини|склад,матеріал,сезон|нема (з fabric таблицею, рядок 6540)|-;рід_тканини_слово|склад,матеріал|fabric_kind|-;текстура|склад,матеріал|texture|-;матеріал_верху|матеріал верху'
    ',матеріал_верху,ззовні|material|fabric;крій|силует,крій,посадка|cut|cut;оверсайз|силует,крій|cut=oversized·veto.oversize|cut;пояс|пояс,силует|belt|cut;бортність|бортність|breasted'
    '|cut;довжина_рівень|довжина|length·shaft|length;довжина_виробу_см|довжина|length_cm|-;тип_верхнього|тип|item_type|item_type;місце|тип|item_type|item_type;талія|талія,посадка|elastic_waist·belt·cut=wrap|-;комір|комір,горловин'
    '|collar·neckline|neckline;рукав|рукав|sleeve_cut|-;підошва|підошв|sole|-;повнота|повнота|shoe_width|-;каблук|каблук,підбор|heel.present|-;каблук_см|каблук,підбор|heel.height_cm|-;каблук'
    '_клас|каблук,підбор|нема (heel.height_cm, рядок 6541)|-;блиск|блиск|veto.shine|shine;блиск_крамниці|блиск|veto.shine|shine;візерунок|принт|pattern|pattern;метал|метал|metal|metal;частка_металу|метал|metal_where|metal;к'
    'олір_вставки|колір|color_extra·color_why=trim|color;наповнювач|утеплювач,наповнювач|filling|-;застібка|застібк|closure|-;капюшон|капюшон|hood|-;простібка|простібк|quilted|-;формат|розмір|bag_size|-;розмірність'
    '|розмір|size_fit|-;ворс|ворс|pile|-;опушка|опушк|fur_trim|-;ремонтопридатна|-|sole_attachment|-;ланцюг_см|довжина|chain_cm|-;ремінь_см|довжина|strap_cm|-;розміри_нема|розмір|нема (рядок 6540)|-').split(';')]
F.каталог_на_диску('каталог_повний.xml'); кат = ФК.прочитати_каталог('каталог_повний.xml', 0)['каталог']
оф = {o['id']: o for o in F.читати_yml('каталог_повний.xml')[0]}; є = lambda в: в not in (None, '', 'unknown', 'невідомо', [], {}); у_схемі = lambda с: с if с.startswith('нема') or all(ш.split('=')[0].split(' ')[0] in {п.replace('[]', '') for п in КР.ПЕРЕЛІКИ} for ш in с.split('·')) else с + ' ✗ поза КР.ПОЛЯ'
тексти = {ф: open(ф, encoding='utf-8').read() for ф in glob.glob('*.py') + glob.glob('*.js') if not re.match(r'(фід_|feed|жнива_|audit_|тест|стенд|батарея)', ф)}
СУД = re.compile(r'(суд_|verify|силует_суд|аксесуари_суд|оцінка_образу|вердикт_моделі|траурний)'); ПОКАЗ = re.compile(r'(\.js$|міст_відповіді|назва_речі|мовний_шар)')
розбори, Е = [], json.load(open(os.path.join(Д, 'проби', 'еталон_розбору.json'), encoding='utf-8')); ВИД = ('правильно', 'хибно', 'вигадано', 'невідомо', 'не судиться')   # 404 чинним збирачем `П.зібрати`, без запису
for а in ('404_а1', '404_а2', '404_а3'): м = json.load(open(os.path.join(РЗ, а, 'прогін.json'), encoding='utf-8')); розбори.append((м, {р['id']: КР.з_відповіді(*reversed(П.розділити(open(os.path.join(РЗ, а, р['файл']), encoding='utf-8').read())))[0] or {} for р in м['речі']}))
def якість(поле, коди=None):
    """п/х/в/м/нс поля еталону: три прогони MamayLM (мірило `еталон_частки.суд`/`з_розбору`; 6145 змінить fabric) або раз — `коди` коду."""
    рази = [коди] if коди else [{р['id']: з_розбору(рз.get(р['id'], {}), 'shoes' in р['правда']['slot'])[поле] for р in Е['речі']} for _, рз in розбори]
    л = C.Counter(суд(р['правда'][поле], р['опора'].get(поле, []), к[р['id']], not коди) for к in рази for р in Е['речі']); return '/'.join(str(л[в]) for в in ВИД)
print('поле запису #1028 | речей з полем на main | з них з param-ключем | поле розбору | споживачі суд/добір/показ, межа 5420/5330 | еталон п/х/в/м/нс ×3')
for к, ключі, схема, ет in ПОЛЯ:
    з = [x for x in кат if є(x.get(к))]; кл = [x for x in з if any(п in н.lower() for н in (оф.get(x['id'], {}).get('параметри') or {}) for п in ключі.split(','))]
    сп = [ф for ф, т in тексти.items() if re.search(r"""(get\(|\[)\s*["']%s["']""" % re.escape(к), т)]; гр = C.Counter('суд' if СУД.match(ф) else 'показ' if ПОКАЗ.search(ф) else 'добір' for ф in сп)
    межа = ('5420 ' if к in profile._СЛОВА_РЕЧІ else '') + ('5330' if к in тексти.get('траурний_регістр.py', '') else '')
    print('%s | %d | %d | %s | %d/%d/%d %s | %s' % (к, len(з), len(кл), у_схемі(схема), гр['суд'], гр['добір'], гр['показ'], межа or '-', якість(ет) if ет != '-' else 'не міряється'))
тип = {v: k for k, v in ВМ.ТАБЛИЦЯ['item_type'].items()}; пт = {р['id']: (оф.get(р['id'], {}).get('параметри') or {}).get('тип') for р in Е['речі']}
print('5191: еталон %d, param «тип» є %d, точний код ТАБЛИЦЯ %d · п/х/в/м/нс: param «тип» кодом %s · розбір ×3 item_type %s, slot %s' % (len(пт), sum(map(bool, пт.values())),
      sum(т in тип for т in пт.values()), якість('item_type', {і: тип.get(т) for і, т in пт.items()}), якість('item_type'), якість('slot')))
стіна = [int(с) / 60 for с in re.findall(r'а\d (\d+) с', open(os.path.join(РЗ, '404_ПІДСУМОК.txt'), encoding='utf-8').read())]   # стінний час 60 речей
вв = [р for м, _ in розбори for р in м['речі']]; зн = sum(р['секунд'] for р in вв) / sum(р['знаків_відповіді'] for р in вв)
різні = len({р for в in json.loads(gzip.decompress(open('дані_5191_5194/рядки_5192.json.gz', 'rb').read())).values() for р in в})
print('А порічний: %.1f–%.1f с на річ (parallel 2) → 12426 записів %.1f–%.1f год, 11887 речей %.1f–%.1f год' % (min(стіна), max(стіна), *(н * х / 3600 for н in (12426, 11887) for х in (min(стіна), max(стіна)))))
print('Б порядковий: %d різних рядків; виклик ціною речі → %.1f–%.1f год; %.4f с на знак відповіді (медіана речі %d) і 300–600 знаків на рядок → %.1f–%.1f год (оцінка)' % (різні,
      *(різні * х / 3600 for х in (min(стіна), max(стіна))), зн, sorted(р['знаків_відповіді'] for р in вв)[len(вв) // 2], *(різні * зн * w / 2 / 3600 for w in (300, 600))))

"""Власна перевірка фактів записів і результату моста без генерації."""
import copy, cProfile, hashlib, io, json, os, pathlib, pstats, re, statistics, subprocess, sys, time

RUN = pathlib.Path(os.environ.get('KOD_SHI_REVIEW_ROOT', pathlib.Path(__file__).parent))
TREE = RUN / 'review-2106'
SRC = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else TREE / 'джерела'
sys.path.insert(0, str(SRC))
os.chdir(SRC)
import протокол as P
import дріт_моделі as D
import знання_дріт as K
import збирач_промптів as Z
import вердикт_моделі as V
import схеми_розбору as S
import повнота_образу as F

def packed(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))

if sys.argv[1] == 'audit':
    actual = json.loads((RUN / 'review-logs/записи-власні.json').read_text(encoding='utf8'))
    declared = json.loads((TREE / 'аудит/перевірка/Е2-схема-3/записи.json').read_text(encoding='utf8'))
    fields = ('вхід_до','вхід_після','вихід_до','проєкція')
    assert len(actual) == len(declared) == 9
    for x, y in zip(actual, declared):
        for k in fields:
            if x[k] != y[k]:
                print('Різниця:', pathlib.Path(x['файл']).name, k, x[k], y[k])
    assert all(all(x[k] == y[k] for k in fields) for x, y in zip(actual, declared))
    print('Числа звіту: 36/36 збігаються з власним повтором; проєкції 9/9; порушень схеми 0')
    for row in actual:
        print(pathlib.Path(row['файл']).parent.parent.name,
              pathlib.Path(row['файл']).name.split('_')[1], *[row[k] for k in fields])
elif sys.argv[1] == 'profile':
    answer = json.loads((RUN / 'review-logs/міст-повний-після.json').read_text(encoding='utf8'))
    verdict = P.вердикт_на_дріт(answer['вердикт'])
    assert isinstance(verdict, dict) and verdict.get('вердикт')
    timings = []
    profile = cProfile.Profile()
    for i in range(10):
        start = time.perf_counter()
        profile.enable()
        wire = D.вердикт(verdict)
        Z.зібрати(V.оголошення_ремонту(wire), wire)
        profile.disable()
        timings.append(time.perf_counter()-start)
    stream = io.StringIO()
    pstats.Stats(profile, stream=stream).strip_dirs().sort_stats('cumulative').print_stats(30)
    tag = 'після' if SRC == TREE / 'джерела' else 'до'
    (RUN / ('review-logs/профіль-' + tag + '.txt')).write_text(stream.getvalue(), encoding='utf8')
    print(tag, '10 перетворень і промптів, медіана:', statistics.median(timings))
elif sys.argv[1] == 'records':
    sha = 'dd1327c9a809f03ffb7663089183950b623e976c'
    prefix = 'аудит/проби/автоживий-bd628bb29a90637ae18833c92eceb8230bd9b995'
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', sha, '--', prefix], cwd=TREE,
                                    encoding='utf8').splitlines()
    # Git має цитувати кирилицю вимкненою опцією для переліку шляхів.
    names = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'ls-tree', '-r', '--name-only', sha, '--', prefix],
                                    cwd=TREE, encoding='utf8').splitlines()
    results = []
    for name in names:
        if '/відповіді/' not in name or 'ВЕРДИКТ_V1' not in name:
            continue
        record = subprocess.check_output(['git', 'show', sha + ':' + name], cwd=TREE, encoding='utf8')
        prompt, reply = re.split(r'\n\n── ВІДПОВІДЬ [^\n]*\n', record, maxsplit=1)
        old = json.loads(prompt[prompt.index('{'):])
        full = K.відновити(old) if old.get('knowledge_legend') else copy.deepcopy(old)
        original = copy.deepcopy(full)
        new = D.кандидати_вердикту(full)
        assert full == original
        table = {r['n']: r for r in K.рядки_таблиці(new['candidates'])}
        restored = copy.deepcopy(new)
        for outfit in restored['verdict']:
            outfit['your_outfit']['items'] = [table[n] for n in outfit['your_outfit']['items']]
        if 'showcase' in restored:
            restored['showcase'] = [table[n] for n in restored['showcase']]
        restored.pop('candidates')
        assert restored == original, name
        decl = V.оголошення_ремонту(new) if 'ОБРАЗИ_V1' in name else F.ВИБІР
        wire = Z.зібрати(decl, new)
        recovered = K.відновити(wire) if wire.get('knowledge_legend') else wire
        assert K.рядки_таблиці(recovered['candidates']) == list(table.values())
        if old.get('format_error'):
            wire['format_error'] = old['format_error']
        raw_error = None
        try:
            json.loads(reply.rsplit('</think>', 1)[-1].strip())
        except ValueError as error:
            raw_error = str(error)
        schema = wire['answer_schema']
        if 'ОБРАЗИ_V1' in name:
            assert 'chosen' not in schema
            assert list(schema['outfits'][0])[:2] == ['id', 'why']
        parsed, error = P.розбір(reply)
        used_complete_fragment = bool(error)
        if error:
            start = re.search(r'"chosen"\s*:', reply).end()
            complete, _ = json.JSONDecoder().raw_decode(reply[start:].lstrip())
            assert len(complete) == full['outfits_wanted']
            parsed = dict(version='1', outfits=complete)
            needed = re.search(r'"needed"\s*:', reply)
            if needed:
                parsed['needed'], _ = json.JSONDecoder().raw_decode(reply[needed.end():].lstrip())
        projected = copy.deepcopy(parsed)
        schema_name = 'ОБРАЗИ_V1' if 'ОБРАЗИ_V1' in name else 'ВИБІР_V1'
        if schema_name == 'ОБРАЗИ_V1':
            chosen = {o['id']: o.get('why') for o in parsed.get('chosen', [])}
            projected = dict(version='1', outfits=[])
            for outfit in parsed['outfits']:
                selected = {k: copy.deepcopy(v) for k, v in outfit.items() if k in schema['outfits'][0]}
                selected['items'] = [r['n'] if isinstance(r, dict) else r for r in outfit['items']]
                if chosen.get(outfit.get('id')):
                    selected['why'] = chosen[outfit['id']]
                projected['outfits'].append(selected)
            if 'needed' in parsed:
                projected['needed'] = parsed['needed']
        reparsed, parse_error, notes = P.розбір_за_схемою(packed(projected), schema_name)
        violations = P.перевірити(P.СХЕМИ[schema_name], reparsed)
        assert not parse_error and not violations and not notes.get('обрізано'), name
        result = dict(файл=name, вхід_до=len(packed(old)), вхід_після=len(packed(wire)),
                      кандидатів=len(table), рівність_фактів=True, сирий_обрив=raw_error,
                      вихід_до=len(reply.strip()), проєкція=len(packed(projected)),
                      взято_цілий_фрагмент=used_complete_fragment, порушень=len(violations),
                      схема_виходу=schema)
        results.append(result)
    assert len(results) == 9
    print('Записів: 9; рівність фактів: 9; обривів сирої відповіді:', sum(bool(r['сирий_обрив']) for r in results))
    (RUN / 'review-logs/записи-власні.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
elif sys.argv[1] == 'cases':
    from пакет_моделі import номери_речей
    candidates = {s: [dict(id='review-' + str(i) + '@shop', слот=s)]
                  for i, s in enumerate(('верх', 'низ', 'взуття', 'сумка'), 1)}
    numbers, _ = номери_речей(candidates)
    items = ['#%s·%s' % pair for pair in numbers.values()]
    outfit = dict(id='o1', why='День в офісі', caption='Робочий день', day='Коротка дорога.', items=items)
    normal = dict(version='1', outfits=[outfit])
    many = dict(version='1', outfits=[dict(outfit, id='o'+str(i)) for i in (6, 2, 4, 1, 5, 3)])
    samples = dict(звичайна=packed(normal), обрізана=packed(normal)[:-19],
                   невідомий=packed(dict(normal, outfits=[dict(outfit, items=['#999999·99'])])),
                   повтор=packed(dict(normal, outfits=[dict(outfit, items=[items[0]]*3)])),
                   порожня=packed(dict(version='1', outfits=[])),
                   стара=packed(dict(normal, chosen=[dict(id='o1', why='День в офісі')])),
                   понад=packed(many), старий_вибір=packed(dict(many, chosen=[dict(id='o3'), dict(id='o4')])))
    results = {k: S._розбір_образи_v1(v, кандидати=candidates, просили=5) for k, v in samples.items()}
    assert len(results['звичайна'][0]['ід']) == 4
    assert not results['обрізана'][0]['готово']
    assert not results['невідомий'][0]['готово']
    assert len(results['повтор'][0]['ід']) == 1 and results['повтор'][0]['двічі']
    assert not results['порожня'][0]['готово']
    assert results['стара'][0]['ід'] == results['звичайна'][0]['ід']
    assert [o['ід_відповіді'] for o in results['понад']] == ['о6','о2','о4','о1','о5']
    assert len(results['старий_вибір']) == 5
    tag = 'після' if SRC == TREE / 'джерела' else 'до'
    (RUN / ('review-logs/випадки-' + tag + '.json')).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
    print('Власні випадки:', tag, '8/8')
elif sys.argv[1] == 'bridge':
    import bridge as B
    import feed
    feed.каталог_на_диску('каталог_повний.xml')
    brief = dict(json.loads(pathlib.Path('стенд_вх.json').read_text(encoding='utf8')), сід=4242,
                 варіантів=10, ремонт_варіантів=5, бюджет_символів=120000, без_фото=1, пакети=1)
    request = json.loads(B.виклик('запити', packed(brief)))
    pool = request['пакети']['1']['пул']
    outfits = [dict(ід='о%d' % (i+1), речі=[pool[slot][i % len(pool[slot])]['н']
               for slot in ('верх', 'низ', 'взуття', 'сумка')]) for i in range(10)]
    brief['текст_моделі'] = packed(dict(версія='1', образи=outfits))
    times = []
    for i in range(3):
        start = time.perf_counter()
        raw = B.виклик('від_моделі', packed(brief))
        times.append(time.perf_counter()-start)
    answer = json.loads(raw)
    assert not answer.get('помилка'), answer.get('помилка')
    tag = 'після' if SRC == TREE / 'джерела' else 'до'
    (RUN / ('review-logs/міст-повний-' + tag + '.json')).write_text(raw, encoding='utf8')
    stripped = {k: v for k, v in answer.items() if not k.startswith('промпт_') and k != 'порядок_запитів'}
    result = dict(джерела=str(SRC), часи=times, медіана=statistics.median(times),
                  символів=len(raw), хеш_каталогу=hashlib.sha256(pathlib.Path('каталог_повний.xml').read_bytes()).hexdigest(),
                  хеш_даних=hashlib.sha256(json.dumps(stripped, ensure_ascii=False, sort_keys=True).encode()).hexdigest())
    (RUN / ('review-logs/міст-' + tag + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False))

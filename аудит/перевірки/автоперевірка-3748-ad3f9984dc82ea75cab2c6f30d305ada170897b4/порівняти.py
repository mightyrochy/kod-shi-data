import collections, json, pathlib, subprocess, sys, types

repo = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(root / 'джерела'))
import feed, fit, hypergraph, місце_речі

modules = []
for name, ref in [('до', '2095aeeee42ab96544f6aa99f45e82aed123061f'), ('після', 'refs/review/3748')]:
    code = subprocess.check_output(['git', '-C', str(repo), 'show', ref + ':джерела/композитор_слоти.py']).decode('utf8')
    module = types.ModuleType(name)
    exec(compile(code, str(root / 'джерела/композитор_слоти.py'), 'exec'), module.__dict__)
    modules.append(module)

path = feed.каталог_на_диску('каталог_повний.xml', тека=str(root / 'джерела'))
catalog = feed._прочитати_каталог(path, ліміт_фото=0)
if isinstance(catalog, dict):
    catalog = catalog['каталог']
if isinstance(catalog, tuple):
    catalog = catalog[0]
print('каталог:', len(catalog), 'форма:', type(catalog).__name__, flush=True)
profiles = [dict(плечі=112, груди=114, талія=104, стегна=114),
            dict(плечі=108, груди=96, талія=76, стегна=92),
            dict(плечі=90, груди=84, талія=64, стегна=88)]
total = differences = 0
for i, profile in enumerate(profiles):
    body = fit.тіло([165, 172, 154][i], profile)
    tiers = hypergraph.крої_для_пулу(body)
    by_slot = collections.defaultdict(list)
    for item in catalog:
        by_slot[item.get('слот')].append(item)
    for broken in [(), ('K-BOD-02',), ('K-SIL-03',), ('K-BOD-02', 'K-SIL-03')]:
        for slot, items in by_slot.items():
            results = []
            for module in modules:
                with module._ПОЛ.прогін(broken) as run:
                    keys = module._ключі_пізні(slot, крої_тіла=tiers, прогін_руки=run)
                    results.append((keys[1], [keys[3](item) for item in items], [keys[4](item) for item in items]))
            total += len(items)
            if results[0] != results[1]:
                differences += 1
                print('РОЗБІЖНІСТЬ:', i, slot, broken)
    print('профіль:', i + 1, 'порівнянь:', total, 'розбіжностей:', differences, flush=True)
print('ярус:', json.dumps({str(s): місце_речі.ярус(dict(слот=s)) for s in [*by_slot, 'невідомий', None]}, ensure_ascii=False))
assert differences == 0
print('ДО → ПІСЛЯ: порівнянь', total, '; розбіжностей 0')

"""Незалежні числові 40 пар #1048. Запуск: python перевірити.py REPO CATALOG RAW40.
Фото не читає; числовий результат не є очним прийманням і не замінює ≥38/40."""
import collections, hashlib, importlib, json, os, pathlib, subprocess, sys, types
sys.dont_write_bytecode = True
repo, catalog_path, raw_path = map(pathlib.Path, sys.argv[1:4])
head = '37710e675b710fe89447f9b308aa9571ee14733e'
base = '531ce082f573d225d444952207930095d2e260fc'
raw_hash = '03016bf27794bfff2b76425d0bbf8b55fa2519b56ab0a528a07873a13ac07574'
git = lambda *args: subprocess.check_output(['git', '-C', str(repo), *args], text=True, env=os.environ | {'GIT_NO_LAZY_FETCH': '1'})
assert git('rev-parse', 'HEAD').strip() == head
assert git('diff', '--name-only', head).strip() == ''
raw_bytes, catalog_bytes = raw_path.read_bytes(), catalog_path.read_bytes()
assert hashlib.sha256(raw_bytes).hexdigest() == raw_hash
raw, catalog = json.loads(raw_bytes), json.loads(catalog_bytes)
assert hashlib.sha256(catalog_bytes).hexdigest() == raw['каталог_sha256']
sys.path.insert(0, str(repo / 'джерела'))
new = importlib.import_module('аксесуари_структура'); im = importlib.import_module('внутрішня_мова')
old = types.ModuleType('main_acc'); exec(git('show', base + ':джерела/аксесуари_структура.py'), old.__dict__)
by_id = {x['id']: x for x in catalog}; counters = collections.Counter(); rows = []
fingerprint = lambda: hashlib.sha256(json.dumps(catalog, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
original = fingerprint()
state = lambda z: 'опора' if z.get('полярність') == 'опора' else 'невідомо' if z.get('сила') == 'питання' else 'витрата'
for pair in raw['пари']:
    things = [by_id[pair[k]['id']] for k in ('аксесуар', 'основа')]
    for k, thing in zip(('аксесуар', 'основа'), things):
        assert all(thing.get(field) == value for field, value in pair[k].items())
    before, after = old.аксесуар_як_структура(things), new.аксесуар_як_структура(things)
    counters['зміни_стану'] += list(map(state, before)) != list(map(state, after))
    counters['зміни_ваги'] += [x.get('сила_нп') for x in before] != [x.get('сила_нп') for x in after]
    counters[state(after[0]) if after else 'нема'] += 1
    assert all(x.get('сила_нп') == 0 for x in after if state(x) == 'опора')
    rows.append({'номер': pair['номер'], 'id': [x['id'] for x in things], 'ДО': [{'стан': state(x), 'вага': x.get('сила_нп')} for x in before], 'ПІСЛЯ': [{'стан': state(x), 'вага': x.get('сила_нп'), 'заяви': x.get('заяви')} for x in after]})
schema_same = (repo / 'джерела/внутрішня_мова.schema.json').read_text() == json.dumps(im.схема(), ensure_ascii=False, indent=1) + '\n'
assert schema_same and fingerprint() == original
print(json.dumps({'голова': head, 'база': base, 'raw40_sha256': raw_hash, 'пар': len(rows), 'числа': dict(counters), 'schema_байтова_тотожність': schema_same, 'source_sha256': original, 'source_незмінне': True, 'очима_пар': 0, 'очний_бал': None, 'рядки': rows}, ensure_ascii=False, indent=2))

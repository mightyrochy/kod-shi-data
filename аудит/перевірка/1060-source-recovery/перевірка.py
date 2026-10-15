"""Незалежна офлайн QA #1060: точні байти, ID, маршрути та нормалізація; моделей 0."""
import ast
import collections
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = Path('/workspace/dress3710-next')
OUT = Path('/workspace/qa3710-source-recovery')
SHA = 'd569a89565bf7b34e3d37e4539e72870d9dd9adb'
BASE = '2fb809276e2683f1f579249662aec7b4ce2740f7'
WRITER = Path('/workspace/dress3710-tmp')
SHARED = Path('/workspace/scratch/pachka-1510-2/repo/джерела/каталог_повний.xml')
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'джерела'))

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def gitsha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

def frozen(path, ref=SHA):
    return git('show', ref + ':' + path)

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode()

def fail_network(*args, **kwargs):
    raise AssertionError('QA не дозволяє мережеві зʼєднання')

socket.socket.connect = fail_network
socket.create_connection = fail_network
assert git('rev-parse', 'HEAD').decode().strip() == SHA
assert not git('diff', '--name-only', SHA)
assert subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', BASE, SHA]).returncode == 0

import feed as F
import outfit as O
import silhouette as S
import фід_розбір as FR
import жнива_реєстр as J
import жнива_промпти as P
import жнива_розбір as N
import жнива_запис as Z

loaded = {}
for mod in list(sys.modules.values()):
    file = getattr(mod, '__file__', None)
    if not file:
        continue
    path = Path(file).resolve()
    if path.is_relative_to(REPO) and path.suffix == '.py':
        rel = str(path.relative_to(REPO))
        content = path.read_bytes()
        assert content == frozen(rel), rel
        loaded[rel] = gitsha(content)

inputs = {}
for rel in ('каталог_повний.xml.gz', 'джерела/каталог_збагачення.json.gz',
            'джерела/каталог_показ.json.gz', 'джерела/каталог_кадри.json.gz',
            'джерела/назви_карток.json.gz'):
    content = frozen(rel)
    assert content == frozen(rel, BASE), rel
    local = REPO / rel
    if local.exists():
        assert local.read_bytes() == content, rel
    if rel.endswith('.json.gz'):
        assert not local.with_suffix('').exists(), str(local.with_suffix(''))
    inputs[rel] = {'git_blob': gitsha(content), 'байтів_gzip': len(content), 'sha256_gzip': sha256(content)}

raw = gzip.decompress(frozen('каталог_повний.xml.gz'))
raw_xml_ids = [node.attrib['id'] for _, node in ET.iterparse(io.BytesIO(raw), events=('end',)) if node.tag == 'offer']
raw_offers, _ = F.читати_yml(io.BytesIO(raw))
fd = os.memfd_create('qa3710_exact_frozen')
assert os.write(fd, raw) == len(raw)
raw_path = '/proc/self/fd/%d' % fd
assert raw_offers == FR.офери_фіду(raw_path)

def runtime(path):
    return F._база_прогону(path, ліміт_фото=0,
        кеш='/dev/shm/qa3710-source-recovery-no-cache.json', кешувати=False)['каталог']

def pilot_from(catalog, offers):
    by_id = {offer['id']: offer for offer in offers}
    dresses = [item for item in catalog if item.get('слот') == 'сукня' and item.get('тип') != 'комбінезон']
    chosen = [item for item in dresses if item.get('крій') in ('fitted', 'relaxed')]
    result = []
    for item in sorted(chosen, key=lambda item: item['id']):
        offer = by_id[item['id']]
        slot = F.слоти(offer)['слот']
        kind = F.тип_речі(offer, slot)
        result.append(dict(id=item['id'], слот=slot, тип=kind,
            контракт_сукні=J.це_сукня(slot, kind), крій_до=item.get('крій'),
            крої_до=list(O.крої_слота(item)[0]), фото=offer.get('фото'),
            фото_опису_до=item.get('фото_опису'), джерело_до=item.get('крій_джерело')))
    return dresses, result

raw_catalog = runtime(raw_path)
dresses, pilot = pilot_from(raw_catalog, raw_offers)
raw_ids = {item['id'] for item in raw_offers}
assert len(raw_xml_ids) == len(raw_offers) == len(raw_ids)
assert {str(i) for i in raw_xml_ids} == {item['id_жниварки'] for item in raw_offers}
assert all(item['id'] == (item['id_жниварки'] + '@' + item['магазин']
    if item['магазин'] else item['id_жниварки']) for item in raw_offers)
clean = SHARED.read_bytes()
clean_offers, _ = F.читати_yml(io.BytesIO(clean))
clean_catalog = runtime(str(SHARED))
clean_dresses, clean_pilot = pilot_from(clean_catalog, clean_offers)
clean_ids = {item['id'] for item in clean_offers}
ledger = json.loads((WRITER / 'походження_RAW.json').read_text())
writer_pilot = json.loads((WRITER / 'пілот_3710_RAW.json').read_text())
old_pilot = json.loads((WRITER / 'пілот_3710_clean_ПОМИЛКА.json').read_text())
assert pilot == writer_pilot
assert clean_pilot == old_pilot
assert ledger['id_raw_поза_clean'] == sorted(raw_ids - clean_ids)
assert ledger['id_clean_поза_raw'] == sorted(clean_ids - raw_ids)
assert ledger['пілот_raw_поза_clean'] == sorted({x['id'] for x in pilot} - {x['id'] for x in clean_pilot})
assert ledger['пілот_canonical_sha256'] == sha256(canonical(pilot))
assert ledger['raw']['байтів'] == len(raw)
assert ledger['raw']['sha256'] == sha256(raw)
assert ledger['raw']['offers'] == len(raw_offers)
assert ledger['raw']['runtime_каталог'] == len(raw_catalog)
assert ledger['raw']['runtime_canonical_sha256'] == sha256(canonical(raw_catalog))
assert ledger['raw_id_поза_runtime'] == sorted(raw_ids - {x['id'] for x in raw_catalog})
assert ledger['raw']['відфільтровано_id'] == len(ledger['raw_id_поза_runtime'])
assert ledger['raw']['суконь'] == len(dresses)
assert ledger['raw']['пілот'] == len(pilot)
assert ledger['raw']['канонічних_суконь'] == sum(x['контракт_сукні'] for x in pilot)
assert ledger['попередній_shared_clean']['байтів'] == len(clean)
assert ledger['попередній_shared_clean']['sha256'] == sha256(clean)
assert ledger['попередній_shared_clean']['offers'] == len(clean_offers)
assert ledger['попередній_shared_clean']['runtime_каталог'] == len(clean_catalog)
assert sha256(SHARED.read_bytes()) == sha256(clean)

expected = {'belted', 'a-line', 'shift', 'sheath', 'wrap', 'bodycon', 'empire', 'bias-slip'}
assert set(J.КРОЇ_СУКНІ) == expected
assert expected == {cut for cut, slots in S.КРІЙ_СЛОТ.items() if 'сукня' in slots}
normalizer_cases = []
for value in [*J.КРОЇ, 'regular', None, '', 'UNKNOWN', 'fitted or a-line']:
    got_dress = N.нормалізувати({'крій': value}, 'одяг', сукня=True)['крій']
    got_wide = N.нормалізувати({'крій': value}, 'одяг', сукня=False)['крій']
    assert got_dress == (value if value in expected else None)
    assert got_wide == (value if value in J.КРОЇ else None)
    normalizer_cases.append({'вхід': value, 'сукня': got_dress, 'широкий': got_wide})
guard_cases = []
for slot in ('сукня', 'низ', 'верх', 'верхній_шар', None):
    for kind in (*J.ТИПИ_СУКНІ, 'комбінезон', 'спідниця', 'штани', 'светр', None, 'dress'):
        value = J.це_сукня(slot, kind)
        assert value == (slot == 'сукня' and kind in J.ТИПИ_СУКНІ)
        guard_cases.append({'слот': slot, 'тип': kind, 'контракт_сукні': value})
base_prompts = {'__name__': '_qa3710_base_prompts'}
exec(compile(frozen('джерела/жнива_промпти.py', BASE), '<base_prompts>', 'exec'), base_prompts)
prompt_matches = {}
for kind, template in P.ПРОМПТ_НАБОРУ.items():
    current = P._підставити(template, 'QA_тип', сукня=False)
    previous = base_prompts['_підставити'](base_prompts['ПРОМПТ_НАБОРУ'][kind], 'QA_тип')
    assert current == previous, kind
    prompt_matches[kind] = sha256(current.encode())
narrow = P._підставити(P.ПРОМПТ_ОДЯГ, 'QA_тип', сукня=True)
assert '{крій_контракт}' not in narrow and '{крої}' not in narrow
assert 'null' in narrow and 'Do not infer cut' in narrow
assert ', '.join(J.КРОЇ_СУКНІ) in narrow

# Справжня функція producer; тільки дорогі I/O-межі замінені офлайн заглушками.
# Відповідь нижче синтетична, це не фото-розбір і не новий model output.
Z.виміряти_фото = lambda *args: (0.75, [], 'qa', 'qa', False)
Z.звести_колір = lambda *args: (None, None, None)
Z.впевненість = lambda *args: 1.0
Z._фото_1024 = lambda path: path
Z._b64 = lambda *args, **kwargs: 'offline_stub'
captured = []
def request_stub(model, prompt, photos, **kwargs):
    captured.append(prompt)
    return {'крій': 'fitted'}
Z._запит = request_stub
raw_by_id = {x['id']: x for x in raw_offers}
producer_results = []
for entry in pilot:
    offer = raw_by_id[entry['id']]
    assert entry['фото'] and entry['фото'] == offer['фото']
    url = offer['фото'][0]
    result = Z.обробити(offer, [{'шлях': 'offline_only', 'url': url, 'джерело': 'фід'}], 'QA_SYNTHETIC', показ=False)
    actual_narrow = P._КРІЙ_СУКНІ.split(':')[0] in captured[-1]
    assert actual_narrow == entry['контракт_сукні'], entry['id']
    assert result['запис']['крій'] == (None if actual_narrow else 'fitted'), entry['id']
    assert result['запис']['фото'] == url
    assert result['запис']['модель'] == 'QA_SYNTHETIC' and result['запис']['версія'] == 2
    assert result['запис']['знято']
    producer_results.append({'id': entry['id'], 'тип': entry['тип'], 'контракт_сукні': actual_narrow})
combines = [x for x in raw_offers if F.тип_речі(x, F.слоти(x)['слот']) == 'комбінезон']
for offer in combines:
    url = (offer.get('фото') or ['offline_control'])[0]
    result = Z.обробити(offer, [{'шлях': 'offline_only', 'url': url}], 'QA_SYNTHETIC', показ=False)
    assert 'cut (крій):' not in captured[-1]

# Проба на тому самому blob; окремий memfd замість стороннього XML.
probe_blob = frozen('джерела/проби/фіг4_джерело_3710.py')
probe = {'__name__': '_qa3710_probe', '__file__': str(REPO / 'джерела/проби/фіг4_джерело_3710.py')}
exec(compile(probe_blob, probe['__file__'], 'exec'), probe)
compressed_fd = os.memfd_create('qa3710_frozen_gzip')
compressed = frozen('каталог_повний.xml.gz')
assert os.write(compressed_fd, compressed) == len(compressed)
old_argv = sys.argv
sys.argv = [probe['__file__'], '/proc/self/fd/%d' % compressed_fd]
os.environ['TMPDIR'] = '/dev/shm'
import contextlib
probe_output = io.StringIO()
with contextlib.redirect_stdout(probe_output):
    probe['головна']()
sys.argv = old_argv
os.close(compressed_fd)
os.close(fd)

report = {
    'head': SHA, 'base': BASE, 'модельних_викликів': 0,
    'нових_фото_розборів': 0, '3710': 'ВІДКРИТО', 'фото_якість': 'НЕ ВИМІРЯНА',
    'inputs': inputs, 'перевірених_імпортованих_py': len(loaded),
    'raw': {'байтів': len(raw), 'sha256': sha256(raw), 'оферів_xml': len(raw_xml_ids),
        'оферів_producer': len(raw_offers), 'runtime': len(raw_catalog), 'суконь': len(dresses),
        'runtime_canonical_sha256': sha256(canonical(raw_catalog)),
        'пілот': len(pilot), 'старі_крої': dict(collections.Counter(x['крій_до'] for x in pilot)),
        'контракт_сукні': sum(x['контракт_сукні'] for x in pilot),
        'без_одного_крою': sum(len(x['крої_до']) != 1 for x in pilot),
        'canonical_pilot_sha256': sha256(canonical(pilot)),
        'типи_producer': dict(collections.Counter(x['тип'] for x in pilot)),
        'комбінезонів': len(combines), 'комбінезонів_dressenum': 0},
    'попередній_clean': {'байтів': len(clean), 'sha256': sha256(clean), 'оферів': len(clean_offers),
        'runtime': len(clean_catalog), 'суконь': len(clean_dresses), 'пілот': len(clean_pilot),
        'контракт_сукні': sum(x['контракт_сукні'] for x in clean_pilot),
        'canonical_pilot_sha256': sha256(canonical(clean_pilot))},
    'id_raw_поза_clean': sorted(raw_ids - clean_ids), 'id_clean_поза_raw': sorted(clean_ids - raw_ids),
    'raw_id_поза_runtime': sorted(raw_ids - {x['id'] for x in raw_catalog}),
    'пілот_raw_поза_clean': sorted({x['id'] for x in pilot} - {x['id'] for x in clean_pilot}),
    'пілот_clean_поза_raw': sorted({x['id'] for x in clean_pilot} - {x['id'] for x in pilot}),
    'пілот_збіг_з_автором': True, 'ledger_збіг': True, 'старий_пілот_збережений': True,
    'enum': J.КРОЇ_СУКНІ, 'нормалізація': normalizer_cases, 'guard': guard_cases,
    'інші_готові_prompts_побайтно_main': prompt_matches,
    'справжній_producer_офлайн_синтетика': {'пілот': len(producer_results), 'комбінезони': len(combines),
        'невідповідностей': 0, 'поля_фото_модель_дата_версія': 'PASS'},
    'foreign_controls': [x for x in producer_results if not x['контракт_сукні']],
    'loaded_py_blobs': loaded,
}
(OUT / 'факти.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
(OUT / 'проба_автора.txt').write_text(probe_output.getvalue())
print(json.dumps({k:report[k] for k in ('head','base','raw','попередній_clean','foreign_controls',
    'пілот_збіг_з_автором','ledger_збіг','справжній_producer_офлайн_синтетика')}, ensure_ascii=False, indent=2))
print('ID-різниця:', len(report['id_raw_поза_clean']), len(report['id_clean_поза_raw']))
print('Пілот ID-різниця:', len(report['пілот_raw_поза_clean']), len(report['пілот_clean_поза_raw']))
print('Імпортованих frozen py:', len(loaded), 'нормалізатор:', len(normalizer_cases), 'guard:', len(guard_cases))
print('PASS: усі незалежні assertions; мережі та моделей 0.')

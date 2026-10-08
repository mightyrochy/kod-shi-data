"""CPU only, copied pinned sources, no network/model calls, no product writes."""
import collections
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time

src = Path('/tmp/liusterko-e70c3c3-cpu/джерела')
out = Path('/workspace/liusterko-hypergraph-gpt-e70c3c3/evidence')
os.chdir(src)
sys.path.insert(0, str(src))
sys.dont_write_bytecode = True

def forbidden(*args, **kwargs):
    raise RuntimeError('Network disabled by research probe')

socket.socket.connect = forbidden
socket.create_connection = forbidden
import graph
import bridge
import feed

items = [dict(id='i1', назва='same', слот='верх'),
         dict(id='i2', назва='same', слот='низ'),
         dict(id='i3', назва='shoe', слот='взуття')]
def finding(rule, **kw):
    return dict(правило=rule, суть='synthetic', сила_нп=0.6, регістр='репліка', **kw)
f = finding('R1', речі=['i1'])
q = finding('R2', речі=['i2'], сила='питання')
g0 = graph.граф([f, q], items)
g1 = graph.граф([q, f], items)
ambiguity = graph.граф([finding('R3', речі=['same'])], items)
text_derived = graph.граф([dict(f, чому=' шия ')], items)
all_edge = graph.граф([finding('R4', речі=['i1', 'i2', 'i3'])], items)
result = {'baseline': 'e70c3c3bcf3161991d4603106c65696ce4592d67',
          'network': 'blocked at socket.connect', 'models_called': False,
          'graph_synthetic': {'normal': g0, 'reordered': g1,
                              'duplicate_name': ambiguity,
                              'text_added_neck': text_derived,
                              'all_items': all_edge,
                              'empty': graph.граф([],items)}, 'pool_runs': []}
fixture = json.loads((src/'стенд_вх.json').read_text())
fixture.update(каталог=feed.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)
for intent in ['conventional', 'statement']:
    inp = dict(fixture, намір=intent)
    start = time.perf_counter()
    ans = json.loads(bridge.виклик('запити', json.dumps(inp, ensure_ascii=False)))
    elapsed = time.perf_counter()-start
    pools = ans.get('кандидати') or {}
    counts = {k:len(v) for k,v in pools.items()}
    ids = {k:[x.get('id',x.get('н')) for x in v] for k,v in pools.items()}
    encoded = json.dumps(ids, ensure_ascii=False, sort_keys=True).encode()
    rec={'intent':intent,'seconds':round(elapsed,4),'items':sum(counts.values()),
         'slots':counts,'pool_sha256':hashlib.sha256(encoded).hexdigest(),
         'ceiling':ans.get('стеля'),'result_keys':sorted(ans),
         'hand1_characters':len(str((ans.get('руки') or {}).get('1','')))}
    result['pool_runs'].append(rec)
    print(json.dumps(rec,ensure_ascii=False),flush=True)
result['note']='Static fixture and CPU pool construction; no model selected any outfit.'
(out/'baseline_probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print('SAVED baseline_probe.json',flush=True)

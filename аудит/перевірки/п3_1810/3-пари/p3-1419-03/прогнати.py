#!/usr/bin/env python3
"""Шість послідовних повних сцен; запуск лише після сигналу координатора."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, statistics, subprocess, time

REPO = Path('/workspace/work/p3')
ROOT = REPO / 'work/03-парні'
os.chdir(REPO)
protocol = json.loads((ROOT / 'протокол.json').read_text())

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def verify():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert head == protocol['head'], (head, protocol['head'])
    for path, expected in protocol['hashes'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    for path, expected in protocol['pyodide_files'].items():
        assert Path(path).stat().st_size == expected['bytes'], path
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected['sha256'], path

def corpus(path):
    rows = json.loads(path.read_text())
    result = []
    for row in rows:
        raw = row.get('етапи', '')
        stages = json.loads(raw) if isinstance(raw, str) else raw
        language = stages.get('мова_шару') if stages else None
        result.append({'рука': row.get('рука'), 'полів': len(row),
                       'етапи_символів': len(raw.encode('utf-16-le')) // 2,
                       'етапи_UTF8': len(raw.encode()),
                       'мовних_спроб': len(language) if isinstance(language, list) else None,
                       'мова_не_перекладено': bool(stages and stages.get('картка', {}).get('мова_не_перекладено')),
                       'етапи_sha256': hashlib.sha256(raw.encode()).hexdigest()})
    return result

def summarize():
    runs = [json.loads((ROOT / label / 'rawmeta.json').read_text())
            for label in protocol['order'] if (ROOT / label / 'rawmeta.json').exists()]
    stats = {}
    for side in ['до', 'після']:
        chosen = [run for run in runs if run['side'] == side]
        values = [run['wrapper_wall_s'] for run in chosen if run.get('valid')]
        inner = [run['full_stand_s'] for run in chosen if run.get('valid')]
        stats[side] = {'n': len(values), 'wrapper_wall_s': values,
                       'median_s': statistics.median(values) if values else None,
                       'min_s': min(values) if values else None,
                       'max_s': max(values) if values else None,
                       'inner_stand_s': inner,
                       'inner_stand_median_s': statistics.median(inner) if inner else None,
                       'inner_stand_min_s': min(inner) if inner else None,
                       'inner_stand_max_s': max(inner) if inner else None}
    complete = len(runs) == 6 and all(run.get('valid') for run in runs)
    verdict = 'INCOMPLETE'
    if complete:
        verdict = ('AFTER_MEDIAN_NOT_SLOWER' if stats['після']['median_s'] <= stats['до']['median_s']
                   else 'AFTER_MEDIAN_SLOWER: причина потребує розбору; не зливати')
    value = {'head': protocol['head'], 'order': protocol['order'], 'runs': runs,
             'summary': stats, 'complete': complete, 'verdict': verdict,
             'note': 'Повний wall виклику прогін.sh є первинним (той самий знаменник137→152с); внутрішній СТЕНД та JS-інтервали окремі. Розкид мін–макс без автоматичного списання уповільнення на шум.'}
    write(ROOT / 'усе.json', value)
    print(json.dumps({'summary': stats, 'verdict': verdict}, ensure_ascii=False), flush=True)

parser = argparse.ArgumentParser()
parser.add_argument('--execute', action='store_true')
parser.add_argument('--summarize', action='store_true')
args = parser.parse_args()
verify()
if args.summarize:
    summarize()
elif not args.execute:
    print('PREPARED: hashes/HEAD verified; no browser started')
else:
    # Людина/координатор створює цей запис тільки після звільнення машини.
    assert (ROOT / 'машина-вільна.txt').exists(), 'Потрібен сигнал координатора; timed runs не дозволені'
    assert not any((ROOT / label).exists() for label in protocol['order']), 'Не перезаписувати історію прогонів'
    env = dict(os.environ)
    for flag in protocol['cleared_flags']:
        env.pop(flag, None)
    env.update(protocol['set_flags'])
    for label in protocol['order']:
        verify()
        side = label.rsplit('-', 1)[0]
        out = ROOT / label
        out.mkdir()
        meta = {'label': label, 'side': side, 'head': protocol['head'], 'start_utc': now(),
                'loadavg_start': os.getloadavg(), 'index_sha256': protocol['hashes'][f'work/{side}/index.html']}
        print(f"START {label} {meta['start_utc']}", flush=True)
        start = time.monotonic()
        with (out / 'прогін.log').open('w') as log:
            proc = subprocess.run(['sh', str(ROOT / 'скрипти/прогін.sh'), f'work/{side}',
                                   '/workspace/work/pyodide', str(out), 'чиста_1'],
                                  stdout=log, stderr=subprocess.STDOUT, env=env)
        meta.update(end_utc=now(), wrapper_wall_s=time.monotonic() - start,
                    shell_returncode=proc.returncode, loadavg_end=os.getloadavg())
        scene = (out / 'чиста_1.log').read_text()
        counts = {'passed': len(re.findall(r'^  ✔', scene, re.M)),
                  'failed': len(re.findall(r'^  ✗', scene, re.M))}
        matches = re.findall(r'^СТЕНД: усе, що просить §6, зелене · ([\d.]+) с$', scene, re.M)
        meta.update(cases=counts, full_stand_s=float(matches[-1]) if len(matches) == 1 else None)
        summary = (out / 'прогін.log').read_text()
        meta['scene_rc0'] = bool(re.search(r'чиста_1 rc=0 ', summary))
        meta['valid'] = proc.returncode == 0 and meta['scene_rc0'] and counts == {'passed': 95, 'failed': 0} and len(matches) == 1
        raw = out / 'чиста_1/стор1/сирий-журнал.json'
        if raw.exists():
            meta['corpus'] = corpus(raw)
            meta['corpus_five_rows'] = len(meta['corpus']) == 5
            shapes = {str(row['рука']): row for row in meta['corpus']}
            meta['corpus_expected_fields'] = ({key: row['полів'] for key, row in shapes.items()}
                                              == {'3': 107, '4': 104, '1': 104, '2': 104, 'оцінка': 47})
            meta['corpus_large_payload_exact'] = all(
                key in shapes and shapes[key]['етапи_символів'] == chars and shapes[key]['етапи_UTF8'] == size
                for key, chars, size in [('1', 1528505, 1793106), ('2', 2214830, 2512470)])
            assessment = shapes.get('оцінка', {})
            meta['corpus_language_equal'] = (assessment.get('мовних_спроб') == 3
                                             and not assessment.get('мова_не_перекладено', True))
            meta['valid'] &= all(meta[key] for key in ['corpus_five_rows', 'corpus_expected_fields',
                                                     'corpus_large_payload_exact', 'corpus_language_equal'])
        else:
            meta['valid'] = False
        write(out / 'rawmeta.json', meta)
        if meta['valid']:
            analysis_env = dict(env)
            if side == 'до':
                analysis_env['POKRYTTIA_Z'] = 'work/вим-до'
            with (out / 'аналіз.json').open('w') as stdout, (out / 'аналіз.log').open('w') as stderr:
                subprocess.run(['node', str(ROOT / 'скрипти/аналіз.js'), f'work/{side}/index.html',
                                str(out), f'work/статика-{side}.json'], env=analysis_env,
                               stdout=stdout, stderr=stderr, check=True)
            analysis = json.loads((out / 'аналіз.json').read_text())
            meta['canonical_1415_intervals'] = analysis['профілі']['чиста_1']
            profile = out / 'чиста_1/стор1/профіль.cpuprofile'
            meta['profile_sha256'] = hashlib.sha256(profile.read_bytes()).hexdigest()
            write(out / 'rawmeta.json', meta)
        print(f"END {label}: full_stand={meta['full_stand_s']}s valid={meta['valid']}", flush=True)
        summarize()
        assert meta['valid'], f'{label}: невалідний прогін, не перезапускати мовчки'

import subprocess, re, json, hashlib, collections
from pathlib import Path

base = '7c90a0093b5d7dc8587a90c541eaf11e23b9a3be'
head = '31257c15337a12f5f08a4cd72b1548adf3afdb70'
sources = {997: '82c34d186b208167053dd6172f9b5074081b4f7a',
           998: '691c5500330cb1692610fa14f26d5eee7833a057',
           1000: 'fb3bea3312ab054886e67a7125d064689f3a0c1f'}
def git(*args):
    return subprocess.check_output(['git', '-c', 'core.quotepath=false', *args])
def blob(ref, path):
    return git('show', ref + ':' + path)
files = git('diff', '--name-only', base, head).decode().splitlines()
result = dict(head=head, base=base, tree=git('rev-parse', head+'^{tree}').decode().strip(),
              sources=sources, changed_files=files, source_files={})
for pr, sha in sources.items():
    assert subprocess.run(['git', 'merge-base', '--is-ancestor', sha, head]).returncode == 0
    for path in git('diff', '--name-only', base, sha).decode().splitlines():
        if path == 'аудит/БЕКЛОГ.md':
            continue
        assert blob(head, path) == blob(sha, path), path
        result['source_files'][path] = dict(source_pr=pr, sha256=hashlib.sha256(blob(head, path)).hexdigest())
assert set(files) == {'аудит/БЕКЛОГ.md', *result['source_files']}
path = 'джерела/показ.html'
html, original = blob(head, path).decode(), blob(base, path).decode()
assert re.sub(r'<style[\s\S]*?</style>', '', html) == re.sub(r'<style[\s\S]*?</style>', '', original)
result['outside_style_byteexact_base'] = True
diff = git('diff', '--unified=0', base, head, '--', 'джерела/вердикт_моделі.py').decode().splitlines()
added = [line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
assert len(added) == 1 and 'скелет_наприкінці=True' in added[0]
result['production_python_added_lines'] = added
def rows(ref):
    return {m[1]: line for line in blob(ref, 'аудит/БЕКЛОГ.md').decode().splitlines()
            if (m := re.match(r'^\|\s*(\d+)\s*\|', line))}
before, after = rows(base), rows(head)
changed = [key for key in after if before.get(key) != after[key]]
assert set(changed) == {'3653', '4531', '4944', '5100'}
assert all(key in after for key in before)
for key, pr in [('3653', 997), ('4531', 998), ('4944', 1000), ('5100', 1000)]:
    assert after[key] == rows(sources[pr])[key]
for key in ['3653', '4944', '5100']:
    assert 'ВІДКРИТО' in after[key]
assert 'ЖИВИЙ ПІСЛЯ' in after['4531'] and 'очікує' in after['4531'] and 'ЗАКРИТО #998 — код' in after['4531']
def duplicates(ref):
    counts = collections.Counter(re.findall(r'^\|\s*(\d+)\s*\|', blob(ref, 'аудит/БЕКЛОГ.md').decode(), re.M))
    return {key: value for key, value in counts.items() if value > 1}
assert duplicates(head) == duplicates(base)
result.update(board_changed_ids=changed, new_duplicate_ids=0, baseline_duplicate_ids=duplicates(base),
              new_product_media=0, new_word_logic=0, board_rows_exact_source=True)
for path in ['AGENTS.md', 'CLAUDE.md', 'аудит/ПРОДУКТ.md', 'джерела/мовний_шар.py',
             'джерела/міст_відповіді.py', 'джерела/збирач_промптів.py']:
    assert blob(base, path) == blob(head, path), path
result['unchanged_rules_producer_language'] = True
Path(__file__).with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print('PASS:', len(files), 'файлів;', len(result['source_files']), 'джерельних файлів тотожні;', len(changed), 'рядки дошки; нових дублів 0')

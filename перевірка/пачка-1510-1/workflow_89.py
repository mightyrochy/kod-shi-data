"""Лише два пропущені через sparse checkout перевіряння §89, без повтору завершених 573."""
import ast, json, os, subprocess, textwrap
from pathlib import Path

repo = Path('/workspace/scratch/pachka-1510-1/repo')
head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
assert head == 'c80bea14f73505903d1b99c77b746c45acb34c45'
source = subprocess.check_output(['git', '-C', str(repo), 'show', head + ':джерела/прилади/розділи_гейтів.py'], text=True)
fragment = textwrap.dedent(source.split('    import ast as _ast89, re as _re89\n', 1)[1].split('    # ТРЕТІЙ ДЕФЕКТ', 1)[0])
fragment = 'import ast as _ast89, re as _re89\n' + fragment
results = []
def test(name, condition, detail='', без_входу=False):
    assert not без_входу, (name, 'без входу')
    assert condition, (name, detail)
    results.append(dict(name=name, rc=0, finished=True))
    print('ПРОЙДЕНО', name)
space = dict(_os=os, _тут=str(repo / 'джерела'), тест=test)
exec(compile(ast.parse(fragment), 'frozen-розділи_гейтів-§89', 'exec'), space)
assert len(results) == 2
assert space['_ямли89']
result = dict(head=head, reason='У першому проході sparse checkout не містив .github/workflows; додано точні HEAD-файли. Виконані лише два пропущені перевіряння.', workflows=space['_ямли89'], steps=results, status='finished', rc=0)
(Path(__file__).parent / 'workflow_89.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('ПРОЙДЕНО 2, ВПАЛО 0, БЕЗ ВХОДУ 0; основні 573 завершені перевіряння не повторено.')

import ast, copy, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'repo' / 'джерела'))
import дріт_моделі as Д, повнота_образу as П, збирач_промптів as З, протокол as К
repo = Path(__file__).parent / 'repo'
base = '9f3523d62319225eabb2c1a2cd382053a4651384'
read = lambda p: subprocess.check_output(['git', 'show', base + ':' + p], cwd=repo, text=True)
def nodes(text):
    result = {}
    for n in ast.parse(text).body:
        if isinstance(n, ast.FunctionDef):
            if n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
                n.body = n.body[1:]
            result[n.name] = ast.dump(n, include_attributes=False)
    return result
for module, names in [('повнота_образу', ('_прийняті_гейти', 'прийняти_гейти', 'вибір_з_json', '_чому_не_можна')), ('розбір_відповідей', ('_свідомі_з_json', '_застосувати_свідомі'))]:
    old = nodes(read('джерела/' + module + '.py')); new = nodes((repo / 'джерела' / (module + '.py')).read_text())
    assert all(old[n] == new[n] for n in names), module
    print('Чинна логіка AST незмінна:', module, ', '.join(names))
finding = dict(ід='з-о3-7', правило='K-SHO-08', речі=['#35·32'])
move = dict(річ='#35·32', чому='Задум.', правило='K-SHO-08', знахідка='з-о1-999')
cases = [(move, [finding], 'з-о3-7'), (dict(move, правило='unknown'), [finding], None), (dict(move, річ='#1·01'), [finding], None), (dict(move, правило=''), [finding], None), (move, [], None), (move, [finding, dict(finding, ід='з-о3-8')], None)]
for m, findings, expected in cases:
    got = Д._свідомі_на_дріт(dict(свідомі=[m], знахідки=findings))[0]
    assert got.get('finding') == expected
print('Дріт: поточний / невідомий код / чужа річ / без коду / зникла / неоднозначна: 6/6.')
old_board = read('аудит/БЕКЛОГ.md').splitlines(keepends=True); new_board = (repo / 'аудит/БЕКЛОГ.md').read_text().splitlines(keepends=True)
assert len(old_board) == len(new_board)
for old, new in zip(old_board, new_board):
    if old.startswith('| 3541 |'):
        assert all(a.strip() in b for a, b in zip(old.split('|'), new.split('|')))
    else:
        assert old == new
print('Дошка: кожна історична клітинка 3541 збережена, всі інші рядки побайтово ті самі.')
prompt = З.зібрати(П.ВИБІР, dict(verdict=[dict(your_outfit=dict(id='o3'))]))
if isinstance(prompt, str):
    prompt = json.loads(prompt)
assert any('You may also keep a remark on purpose' in r for r in prompt['task']['rules'])
assert 'a gate or a remark' in json.dumps(prompt['task']['answer_schema'])
print('Справжній зібраний промпт: правило та answer_schema приймають remark.')

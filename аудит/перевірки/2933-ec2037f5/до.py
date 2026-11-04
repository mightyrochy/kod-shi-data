import csv
import gzip
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from collections import Counter

root = Path(sys.argv[1])
sys.path.insert(0, str(root/'zhnyvarka'))
sys.path.insert(0, str(root/'джерела'))
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix='перевірка-2933-до-'))
out.mkdir(parents=True, exist_ok=True)
sha = '6de80803b404590ac7d0bd2182c139a82ef227a2'
source = subprocess.check_output(['git','show',f'{sha}:zhnyvarka/жниварка.py'],cwd=root)
module_path = out/'жниварка-до.py'
module_path.write_bytes(source)
spec = importlib.util.spec_from_file_location('жниварка_до_вимір', module_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
recipe_text = subprocess.check_output(['git','show',f'{sha}:zhnyvarka/рецепти.tsv'],cwd=root).decode('utf8')
recipes = {r['домен']:r for r in csv.DictReader(io.StringIO(recipe_text),delimiter='\t')}
data = root/'аудит/проби/річ_запис_каталог_2026_10_30'
samples = json.loads((data/'вибірка_п3.json').read_text(encoding='utf8'))
excluded = {(r['id'],r['поле']) for r in json.loads((data/'очі_п3.json').read_text(encoding='utf8')) if r['вердикт']=='виключено'}
counts, result = Counter(), []
for row in samples:
    recipe = recipes.get(row['крамниця'],{})
    selectors = {k:recipe[col] for k,col in [('опис','селектор_опису'),('склад','селектор_складу'),('характеристик','селектор_характеристик'),('блок','селектор_блоку')] if recipe.get(col)}
    facts = mod.факти_з_картки(gzip.decompress((data/row['файл']).read_bytes()).decode('utf8'),row['url'],selectors)
    for field in ('назва','опис'):
        baseline = bool((row.get(field) or '').strip()) and (row['id'],field) not in excluded
        counts[field+'_вибірки'] += baseline
        counts[field+'_покрито'] += baseline and bool((facts.get(field) or '').strip())
    result.append(dict(url=row['url'],назва=facts.get('назва'),опис=facts.get('опис')))
with gzip.open(out/'поля-до-повтор.json.gz','wt',encoding='utf8') as f:
    json.dump(dict(sha=sha,лічба=dict(counts),сторінки=result),f,ensure_ascii=False)
print(json.dumps(dict(counts),ensure_ascii=False))

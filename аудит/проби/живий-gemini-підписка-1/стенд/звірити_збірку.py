"""Звірка готової CI-збірки перед повтором: AST коду й байти каталогу.
У CPython 3.12.10 tokenize.untokenize додає пробіли перед зворотною рискою;
це змінює текстовий відбиток без зміни Python-коду. Продукт не змінюється.
"""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'джерела'))
import build_артефакт as build

html = (ROOT / 'index.html').read_text(encoding='utf-8')
archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(re.search(r'const МОДУЛІ_ПОКАЗУ = "([^"]+)";', html)[1])))
rows = []
for name in archive.namelist():
    if not name.endswith('.py'):
        continue
    packed = archive.read(name)
    current = build._стрип(str(ROOT / 'джерела' / name))
    rows.append({'файл': name, 'байти_збігаються': packed == current,
                 'AST_збігається': ast.dump(ast.parse(packed)) == ast.dump(ast.parse(current))})
source_sha = (ROOT / 'build.txt').read_text(encoding='utf-8').strip()
diff = subprocess.check_output(['git', 'diff', '--name-only', source_sha, 'a6b373f405422d09afe6a562671317c1900b7ba8', '--', 'джерела'], cwd=ROOT, text=True).splitlines()
catalog = archive.read('каталог_brief.xml')
current_catalog = (ROOT / 'джерела/каталог_повний.xml').read_bytes()
result = {'готова_збірка': source_sha, 'main_наряду': 'a6b373f405422d09afe6a562671317c1900b7ba8',
          'зміни_джерел_від_збірки': diff, 'модулі': rows,
          'каталог_байти_збігаються': catalog == current_catalog,
          'каталог_збігається': catalog.replace(b'\r\n', b'\n') == current_catalog.replace(b'\r\n', b'\n'),
          'каталог_архів_sha256': hashlib.sha256(catalog).hexdigest(),
          'каталог_джерела_sha256': hashlib.sha256(current_catalog).hexdigest(),
          'index_sha256': hashlib.sha256((ROOT / 'index.html').read_bytes()).hexdigest()}
out = Path(__file__).resolve().parent.parent / 'спроба_4/відповідність_збірки.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
assert all(row['AST_збігається'] for row in rows), 'Python-код відрізняється'
assert result['каталог_збігається'], 'Каталог відрізняється'
assert diff == ['джерела/аудит/ДОСЯЖНІСТЬ.md'], 'Є зміни виконуваних джерел'
print('AST усіх', len(rows), 'модулів і повний каталог після нормалізації CRLF/LF збігаються; змінився лише документ аудиту.')

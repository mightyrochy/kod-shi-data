import hashlib,json,subprocess
from pathlib import Path
root=Path.cwd()
directory=root/'джерела/прилади/рядки_5190'
index=json.loads((directory/'попередні_спроби.json').read_text(encoding='utf-8'))
for record in index['records']:
    path=directory/record['file']
    blob=subprocess.check_output(['git','show','HEAD:'+path.relative_to(root).as_posix()])
    assert hashlib.sha256(blob).hexdigest()==record['sha256'], 'Коміт не відповідає зафіксованому доказу'
    path.write_bytes(blob)
print('Відновлено точні незмінні байти Git для',len(index['records']),'історичних артефактів; SHA256 підтверджено')

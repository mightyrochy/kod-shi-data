import sys, importlib.util, json, re
from pathlib import Path
корінь = Path(sys.argv[1]); sys.path.insert(0, str(корінь/'джерела'))
s = корінь/'аудит/звіти/ядро-образу-наново/вимір_видалення.py'
spec = importlib.util.spec_from_file_location('вв', s); м = importlib.util.module_from_spec(spec); spec.loader.exec_module(м)
до = set(sys.modules)
м.чат_із_фото()
t=(корінь/'аудит/звіти/ядро-образу-наново/скрипти/коло_без_шляху.py').read_text()
s53=set(re.search(r"ЗАМІНЯЄ = set\('''(.*?)'''",t,re.S)[1].split())
чотири={'міст_опис','міст_пакет','міст_рука2','причини_речі'}
print('4:', sorted(чотири & set(sys.modules)), '53:', len(s53 & set(sys.modules)))

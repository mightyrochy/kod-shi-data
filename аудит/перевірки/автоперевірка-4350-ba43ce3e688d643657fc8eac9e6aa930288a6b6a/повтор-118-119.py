"""Повторює незмінені розділи 118–119 після підготовки архіву каталогу й Git-історії."""
import os as _os, sys, tempfile as _tf, subprocess as _сп117, shutil as _ш118, textwrap
from pathlib import Path
_тут = str(Path(sys.argv[1]).resolve()/'джерела')
sys.path.insert(0, _тут)
_os.chdir(_тут)
import feed as _Ф
source = (Path(_тут)/'прилади'/'розділи_гейтів.py').read_text(encoding='utf-8')
start = source.index('    print("118.')
end = source.index('    print("120.', start)
failures = []
count = 0
def тест(name, passed, detail=None):
    global count
    count += 1
    print(('✓ ' if passed else '✗ ')+name+': '+repr(detail))
    if not passed: failures.append(name)
exec(compile(textwrap.dedent(source[start:end]), 'розділи_гейтів.py:118–119', 'exec'), globals())
print('Повтор розділів 118–119: перевірок %d, впало %d' % (count,len(failures)))
sys.exit(bool(failures))

"""Запускає незмінений прилад у Windows зі службовими шляхами кадрів, які очікує його трасувальник."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

НОРМАЛІЗАЦІЯ = '"""Нормалізація службових імен кадрів продукту для POSIX-трасування у Windows."""\nimport importlib.machinery\nfrom pathlib import Path\nimport types\n\nДЖЕРЕЛА = Path.cwd() / \'джерела\'\nОРИГІНАЛ = importlib.machinery.SourceFileLoader.get_code\n\ndef нормалізувати(код):\n    if not isinstance(код, types.CodeType):\n        return код\n    файл = Path(код.co_filename)\n    if файл.is_relative_to(ДЖЕРЕЛА) and \'прилади\' not in файл.parts and \'проби\' not in файл.parts:\n        return код.replace(co_filename=str(ДЖЕРЕЛА) + \'/\' + файл.relative_to(ДЖЕРЕЛА).as_posix(),\n                           co_consts=tuple(нормалізувати(к) for к in код.co_consts))\n    return код\n\ndef завантажити(self, fullname):\n    return нормалізувати(ОРИГІНАЛ(self, fullname))\n\nimportlib.machinery.SourceFileLoader.get_code = завантажити\n'


def main():
    """Змінює лише co_filename модулів продукту, включно з дочірніми процесами Python."""
    if os.name != 'nt':
        return subprocess.run([sys.executable, '-X', 'utf8', *sys.argv[1:]]).returncode
    with tempfile.TemporaryDirectory() as тека:
        Path(тека, 'sitecustomize.py').write_text(НОРМАЛІЗАЦІЯ, encoding='utf-8')
        середовище = dict(os.environ, PYTHONUTF8='1', PYTHONPATH=тека + os.pathsep + os.environ.get('PYTHONPATH', ''))
        return subprocess.run([sys.executable, '-X', 'utf8', *sys.argv[1:]], env=середовище).returncode


if __name__ == '__main__':
    raise SystemExit(main())

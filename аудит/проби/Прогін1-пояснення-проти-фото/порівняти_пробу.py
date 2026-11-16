"""Запускає наявну пробу з базовим модулем розбору, не змінюючи робоче дерево."""
from pathlib import Path
import runpy
import subprocess
import sys
import types


def main():
    """Підміняє лише модуль базою наряду, щоб відрізнити давній збій проби від регресії правки."""
    source = Path(__file__).resolve().parents[3] / 'джерела'
    sys.path.insert(0, str(source))
    name = 'розбір_відповідей'
    code = subprocess.check_output(['git', 'show',
        '781ee3fc5ba83bec58381b2a61a27df234002dbd:джерела/розбір_відповідей.py'])
    module = types.ModuleType(name)
    module.__file__ = str(source / (name + '.py'))
    sys.modules[name] = module
    exec(compile(code, '<база наряду: розбір_відповідей.py>', 'exec'), module.__dict__)
    print('БАЗА НАРЯДУ: 781ee3fc5ba83bec58381b2a61a27df234002dbd', flush=True)
    runpy.run_path(str(source / 'проби' / sys.argv[1]), run_name='__main__')


if __name__ == '__main__':
    main()

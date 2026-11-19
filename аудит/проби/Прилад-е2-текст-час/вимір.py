"""Вимірює прилад у його робочому потоці зі збереженням повного виводу."""
import cProfile
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import pstats
import sys
import threading
import time

ПОМИЛКИ = []

def запуск():
    """Профілює саме аналіз, а не очікування потоку CLI."""
    прилад, дерево, префікс = map(Path, sys.argv[1:4])
    сирий = '--без-профілю' in sys.argv[4:]
    прилад = прилад.resolve()
    дерево = дерево.resolve()
    префікс = префікс.resolve()
    os.chdir(дерево)
    sys.argv = [str(прилад), 'джерела']
    sys.path.insert(0, str(прилад.parent))
    специфікація = importlib.util.spec_from_file_location('вимірюваний', прилад)
    модуль = importlib.util.module_from_spec(специфікація)
    sys.modules[специфікація.name] = модуль
    специфікація.loader.exec_module(модуль)
    профіль = cProfile.Profile()
    початок = time.perf_counter()
    початок_процесора = time.process_time()
    with префікс.with_suffix('.txt').open('w', encoding='utf-8', newline='\n') as файл:
        with contextlib.redirect_stdout(файл):
            if сирий:
                модуль.main()
            else:
                профіль.runcall(модуль.main)
    секунди = time.perf_counter() - початок
    процесор = time.process_time() - початок_процесора
    if not сирий:
        профіль.dump_stats(str(префікс.with_suffix('.prof')))
        with префікс.with_suffix('.profile.txt').open('w', encoding='utf-8') as файл:
            pstats.Stats(профіль, stream=файл).strip_dirs().sort_stats('cumulative').print_stats(35)
            pstats.Stats(профіль, stream=файл).strip_dirs().sort_stats('tottime').print_stats(20)
    префікс.with_suffix('.json').write_text(json.dumps({'секунди': секунди, 'процесор': процесор}, ensure_ascii=False), encoding='utf-8')
    print(префікс.name, секунди, flush=True)

if __name__ == '__main__':
    def помилка(подія):
        """Передає помилку робочого потоку процесу виміру."""
        ПОМИЛКИ.append(подія.exc_value)
        sys.__excepthook__(подія.exc_type, подія.exc_value, подія.exc_traceback)

    threading.excepthook = помилка
    sys.setrecursionlimit(10000)
    threading.stack_size(32 * 1024 * 1024)
    потік = threading.Thread(target=запуск)
    потік.start()
    потік.join()
    sys.exit(bool(ПОМИЛКИ))

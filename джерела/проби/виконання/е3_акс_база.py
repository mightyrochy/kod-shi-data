"""Завантаження чотирьох аксесуарних модулів із коміту для звірки ваги ДО."""
import importlib.abc
import importlib.util
import linecache
import pathlib
import subprocess
import sys

МОДУЛІ = ('аксесуари_носіння', 'аксесуари_суд', 'аксесуари_ціна', 'аксесуари_край')


def встановити(коміт):
    """Підставити код бази під час імпорту, не змінюючи робочих файлів."""
    class База(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, fullname, path=None, target=None):
            if fullname in МОДУЛІ:
                return importlib.util.spec_from_loader(fullname, self)

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            шлях = 'джерела/' + module.__name__ + '.py'
            код = subprocess.check_output(['git', 'show', коміт + ':' + шлях])
            шлях = str(pathlib.Path(шлях).resolve())
            текст = код.decode('utf-8')
            linecache.cache[шлях] = (len(код), None, текст.splitlines(True), шлях)
            module.__file__ = шлях
            exec(compile(текст, шлях, 'exec'), module.__dict__)

    sys.meta_path.insert(0, База())

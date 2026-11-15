"""Завантаження двох модулів із коміту для відтворюваної звірки ваги."""
import importlib.abc
import importlib.util
import subprocess
import sys


def встановити(коміт):
    """Підставити код бази під час імпорту, не змінюючи робочих файлів."""
    class База(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, fullname, path=None, target=None):
            if fullname in ('реєстр_сила', 'суд_погода'):
                return importlib.util.spec_from_loader(fullname, self)

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            шлях = 'джерела/' + module.__name__ + '.py'
            код = subprocess.check_output(['git', 'show', коміт + ':' + шлях])
            module.__file__ = шлях
            exec(compile(код.decode('utf-8'), шлях, 'exec'), module.__dict__)

    sys.meta_path.insert(0, База())

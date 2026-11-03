"""Друкує точну кількість залишених ID у штатному режимі --before стенда голови."""
import argparse
import builtins
import importlib.util
from pathlib import Path
import sys


def main():
    """Додає лише друк стану підробного REST після його штатної перевірки."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stand', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    opts = parser.parse_args()
    spec = importlib.util.spec_from_file_location('gpu_stand', opts.stand.resolve())
    stand = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stand)

    def print_state(*args, **kwargs):
        builtins.print(*args, **kwargs)
        if args and 'стан до замка відновлено (ДО:' in str(args[0]):
            loaded = stand.Studio.loaded
            count = len(set(loaded) - {'owner-id'})
            owner = loaded.get('owner-id') == 'owner-model'
            builtins.print(f'ЗАЛИШОК ДО: нових ID={count}; початковий збережено={owner}', flush=True)

    stand.print = print_state
    sys.argv = [str(opts.stand), '--source-dir', str(opts.base.resolve()), '--before']
    return stand.main()


if __name__ == '__main__':
    raise SystemExit(main())

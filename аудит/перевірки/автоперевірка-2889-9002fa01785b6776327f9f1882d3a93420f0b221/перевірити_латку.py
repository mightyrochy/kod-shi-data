"""Застосовує латку 02 до її точної бази й звіряє результат із перевіреною головою."""
import argparse
from pathlib import Path
import re
import subprocess


def main():
    """Матеріалізує лише файли доказу в явно заданій тимчасовій теці."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--out', type=Path, required=True)
    opts = parser.parse_args()
    repo, root = opts.repo.resolve(), opts.out.resolve()
    root.mkdir(parents=True, exist_ok=True)

    def blob(ref, path):
        return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=repo)

    base = root / 'base-wrapper'
    base.mkdir(exist_ok=True)
    for name in ['gemini_run.ps1', 'claude_run.ps1', 'queue_lanes.ps1', 'wrapper_health.ps1']:
        (base / name).write_bytes(blob('c8f24b1e57b0fbdabe3c97d9ee3b7572eb2c100c', 'аудит/адаптери/gemini/' + name))
    patch = blob('8e0f1ee282829abe713f8679361820fed408174c', 'аудит/латки/обгортка-модель-після-GPU/02-очікування-LM-Studio.patch')
    patch_path = root / '02.patch'
    patch_path.write_bytes(patch)
    tree = root / 'patch-result'
    tree.mkdir(exist_ok=True)
    paths = re.findall(r'^\+\+\+ b/(.+)$', patch.decode('utf-8'), re.M)
    for path in paths:
        target = tree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob('6f149164ba887d1856db12194cc15df6502c623d', path))
    for args in [['--check'], []]:
        subprocess.run(['git', '-c', 'core.autocrlf=false', 'apply', *args, str(patch_path)], cwd=tree, check=True)
    same = 0
    for path in paths:
        equal = (tree / path).read_bytes() == blob('9002fa01785b6776327f9f1882d3a93420f0b221', path)
        same += equal
        print(('✓ ' if equal else '✗ ') + path)
    print(f'Латка 02: застосовано на точній базі; збіг із головою {same}/{len(paths)}')
    return int(len(paths) != 13 or same != len(paths))


if __name__ == '__main__':
    raise SystemExit(main())

"""Звіряє чисте застосування латки з точним деревом перевіреного кандидата."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys


def main():
    """Застосовує лише в переданій окремій копії та записує факти у JSON."""
    clean, candidate = [Path(p).resolve() for p in sys.argv[1:3]]
    assert clean != Path.cwd().resolve() and clean != candidate
    folder = Path(__file__).resolve().parent
    patch = folder / '01-звіт-і-слоти.patch'
    def git(tree, *args):
        return subprocess.check_output(['git', '-c', 'core.quotepath=false', *args], cwd=tree).decode('utf-8').strip()
    base = '918a982d701c8c5d0b241ac7b035af485785c49b'
    before = git(clean, 'write-tree')
    assert before == git(clean, 'rev-parse', base + '^{tree}')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=clean, check=True)
    subprocess.run(['git', 'apply', '--index', str(patch)], cwd=clean, check=True)
    after = git(clean, 'write-tree')
    expected = git(candidate, 'write-tree')
    assert after == expected, (after, expected)
    subprocess.run(['git', 'diff', '--cached', '--check', base], cwd=clean, check=True)
    result = {'база': base, 'дерево-до': before, 'дерево-після': after,
              'дерево-кандидата': expected, 'тотожні': after == expected,
              'apply-check-код': 0, 'apply-index-код': 0, 'diff-check-код': 0,
              'латка-sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
              'файли': git(clean, 'diff', '--cached', '--name-only', base).splitlines()}
    (folder / 'застосування.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

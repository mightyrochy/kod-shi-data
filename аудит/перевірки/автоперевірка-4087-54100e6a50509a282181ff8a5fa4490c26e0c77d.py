"""Прицільні проби незмінених bash-кроків PR #4087 (Git Bash, Python, PyYAML)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

tree = Path(sys.argv[1]).resolve()
scratch = Path(sys.argv[2]).resolve()
bash = sys.argv[3]
steps = yaml.safe_load((tree / '.github/workflows/khrapovyk.yml').read_text(encoding='utf-8'))['jobs']['khrapovyk']['steps']
scope = next(s['run'] for s in steps if s.get('id') == 'prylady')
runner = next(s['run'] for s in steps if s.get('name') == 'стенди й самоперевірки приладів коренів')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT, text=True, encoding='utf-8').strip()


def run(root, script):
    script_path = root / 'step.sh'
    script_path.write_text(script, encoding='utf-8')
    env = dict(os.environ, RUNNER_TEMP=root.as_posix(),
               GITHUB_STEP_SUMMARY=(root / 'summary.md').as_posix(),
               GITHUB_OUTPUT=(root / 'output.txt').as_posix(), PYTHONUTF8='1')
    result = subprocess.run([bash, '-e', '-o', 'pipefail', str(script_path)], cwd=root,
                            env=env, capture_output=True, text=True, encoding='utf-8', timeout=90)
    return result.returncode, result.stdout + result.stderr


def write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


cases = [
    ('прилад', 'джерела/прилади/новий.py', True),
    ('workflow', '.github/workflows/khrapovyk.yml', True),
    ('документ', 'аудит/наряди/проба.md', False),
    ('інший код', 'джерела/приклад.py', False),
    ('один батько', None, True),
    ('перейменовано прилад', 'rename', True),
]
for label, changed, expected in cases:
    with tempfile.TemporaryDirectory(prefix='scope4087-', dir=scratch) as temp:
        root = Path(temp)
        git(root, 'init', '-q')
        git(root, 'config', 'user.name', 'Проба')
        git(root, 'config', 'user.email', 'probe@example.invalid')
        write(root, 'джерела/прилади/старий.py', 'pass\n')
        git(root, 'add', '.')
        git(root, 'commit', '-qm', 'База')
        base = git(root, 'rev-parse', 'HEAD')
        if changed:
            git(root, 'checkout', '-qb', 'candidate')
            if changed == 'rename':
                git(root, 'mv', 'джерела/прилади/старий.py', 'винесено.py')
            else:
                write(root, changed, 'зміна\n')
                git(root, 'add', '.')
            git(root, 'commit', '-qm', 'Зміна')
            git(root, 'checkout', '-qb', 'target', base)
            git(root, 'merge', '--no-ff', '-qm', 'Злиття', 'candidate')
        code, output = run(root, scope)
        expected_line = 'zapusk=' + str(expected).lower()
        actual = (root / 'output.txt').read_text(encoding='utf-8').strip()
        assert code == 0 and actual == expected_line, (label, code, output, actual)
        print(f'ОК умова: {label}: {actual}', flush=True)


for case in ('порожньо', 'успіх', 'падіння й продовження'):
    with tempfile.TemporaryDirectory(prefix='runner4087-', dir=scratch) as temp:
        root = Path(temp)
        if case != 'порожньо':
            write(root, 'джерела/прилади/тест_корінь_новий.py',
                  'import sys\nassert len(sys.argv) == 1\n' +
                  ('sys.exit(7)\n' if case == 'падіння й продовження' else ''))
            write(root, 'джерела/прилади/корінь_новий.py',
                  "import sys\nfrom pathlib import Path\nassert sys.argv[1:] == ['--самоперевірка']\nPath('далі.txt').write_text('виконано', encoding='utf-8')\n")
            write(root, 'джерела/прилади/корінь_без_режиму.py', 'raise RuntimeError("не запускати")\n')
        code, output = run(root, runner)
        expected_code = 0 if case == 'успіх' else 1
        assert code == expected_code, (case, code, output)
        if case != 'порожньо':
            assert (root / 'далі.txt').is_file(), output
            assert 'виконано стендів 1, самоперевірок 1' in output, output
        if case == 'падіння й продовження':
            assert 'код 7' in output and 'впало 1' in output, output
            assert 'код 7' in (root / 'summary.md').read_text(encoding='utf-8')
        print(f'ОК запускач: {case}: код {code}', flush=True)
print('проби: 9 з 9', flush=True)

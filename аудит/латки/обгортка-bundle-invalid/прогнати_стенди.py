"""Завершує всі стенди послідовно, зберігаючи коди й повні журнали."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    """Пише підсумок кожної завершеної команди та повертає спільний код."""
    tree, output = (Path(p).resolve() for p in sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=True)
    tmp = tree.parent / 'bundle-invalid-suite'
    tmp.mkdir(exist_ok=True)
    env = dict(os.environ, TMPDIR=tmp.as_posix(), CI='true', GITHUB_ACTIONS='true', RUNNER_OS='Windows',
               PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PWSH='',
               GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.autocrlf', GIT_CONFIG_VALUE_0='false')
    root = Path('аудит/адаптери/gemini/перевірка')
    commands = [(p.name, ['C:/Program Files/Git/bin/bash.exe', (root / 'запустити_стенд.sh').as_posix(), p.name])
                for p in sorted((tree / root).glob('сценарії_*.sh'))]
    commands.append(('перевірити_хеші.py', [sys.executable, str(root / 'перевірити_хеші.py')]))
    selected = sys.argv[3:]
    if selected:
        assert set(selected) <= {name for name, _ in commands}, 'Невідома назва стенда'
        commands = [(name, command) for name, command in commands if name in selected]
    saved = output / 'результати.json'
    results = json.loads(saved.read_text(encoding='utf-8')) if selected and saved.exists() else []
    results = [r for r in results if r['стенд'] not in selected]
    for name, command in commands:
        start = time.monotonic()
        log = output / (name + '.txt')
        with log.open('wb') as stream:
            result = subprocess.run(command, cwd=tree, env=env, stdout=stream, stderr=subprocess.STDOUT)
        content = log.read_bytes().decode('utf-8', errors='backslashreplace')
        log.write_bytes(('\n'.join(line.rstrip() for line in content.splitlines()) + '\n').encode('utf-8'))
        results.append({'стенд': name, 'код': result.returncode, 'секунд': round(time.monotonic() - start, 2),
                        'підсумок': content.splitlines()[-1] if content.splitlines() else 'Порожній журнал'})
        saved.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    return int(any(r['код'] for r in results))


if __name__ == '__main__':
    sys.exit(main())

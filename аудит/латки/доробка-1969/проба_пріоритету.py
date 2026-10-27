"""Відтворює гонку вимірювання пріоритету на окремому дереві #1969."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    """Проганяє незмінені звірки смуг із затриманим процесом високого пріоритету."""
    tree, output = (Path(p).resolve() for p in sys.argv[1:3])
    root = tree / 'аудит/адаптери/gemini/перевірка'
    side = root / 'side_claude.ps1'
    scene = root / 'сценарії_смуг.sh'
    original_side = side.read_bytes()
    original_scene = scene.read_bytes()
    old = "grep -h 'старт '"
    new = "grep -h 'слот .*пріоритет .* -> '"
    assert old in original_scene.decode('utf-8')
    delay = '''if ($p.ContainsKey('WorkerFile')) {
    $probeJob = Get-Content -Raw -Encoding UTF8 -LiteralPath $p['WorkerFile'] | ConvertFrom-Json
    if ($probeJob.slug -eq 'е-claude-gpu') { Start-Sleep -Seconds 3 }
}
'''
    delayed_side = original_side.decode('utf-8').replace('exit (Main)', delay + 'exit (Main)')
    results = []
    try:
        side.write_bytes(delayed_side.encode('utf-8'))
        for name, source in [('до', original_scene), ('після', original_scene.decode('utf-8').replace(old, new).encode('utf-8'))]:
            case = output / name
            case.mkdir(parents=True, exist_ok=True)
            tmp = tree.parent / ('d1969-probe-' + ('before' if name == 'до' else 'after'))
            tmp.mkdir(exist_ok=True)
            env = dict(os.environ, TMPDIR=tmp.as_posix(), CI='true', GITHUB_ACTIONS='true', RUNNER_OS='Windows',
                       PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PWSH='',
                       GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.autocrlf', GIT_CONFIG_VALUE_0='false')
            scene.write_bytes(source)
            with (case / 'стенд.txt').open('wb') as log:
                result = subprocess.run(['C:/Program Files/Git/bin/bash.exe',
                                         'аудит/адаптери/gemini/перевірка/запустити_стенд.sh', scene.name],
                                        cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT)
            for src, dst in [('cr/claude-run.log', 'claude-run.txt'), ('gr/wrapper.log', 'wrapper.txt'),
                             ('timeline.txt', 'timeline.txt')]:
                shutil.copyfile(tmp / 'smuhy/a' / src, case / dst)
            results.append({'проба': name, 'код': result.returncode})
            print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    finally:
        side.write_bytes(original_side)
        scene.write_bytes(original_scene)
    (output / 'результати.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int([r['код'] for r in results] != [1, 0])


if __name__ == '__main__':
    sys.exit(main())

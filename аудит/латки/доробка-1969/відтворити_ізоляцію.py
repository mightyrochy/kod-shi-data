"""Виконує незмінене очікування сцени 6 з UTF-8/BOM у стандартному stdin PowerShell 5.1."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile


if __name__ == '__main__':
    source, log = map(Path, sys.argv[1:3])
    bash = r'C:\Program Files\Git\bin\bash.exe' if os.name == 'nt' else 'bash'
    with tempfile.TemporaryDirectory(prefix='dorobka1969-') as work:
        root = Path(work)
        g = root / 'gemini'
        shutil.copytree(source / 'аудит/адаптери/gemini', g)
        h = g / 'перевірка'
        side = h / 'side.ps1'
        text = side.read_text(encoding='utf-8-sig')
        text = text.replace('$p = @{}', '[Console]::InputEncoding = [Text.Encoding]::UTF8\n$p = @{}', 1)
        side.write_text(text, encoding='utf-8-sig', newline='\n')
        text = (h / 'сценарії_черги.sh').read_text(encoding='utf-8')
        prelude = text[:text.index('echo "=== 1 повтор:')]
        scene = text[text.index('echo "=== 6 ізоляція'):text.index('echo "=== 7 стара')]
        probe = h / 'probe.sh'
        probe.write_text(prelude + scene + '\ncat "$W/claude.log"\nexit "$BAD"\n', encoding='utf-8', newline='\n')
        env = dict(os.environ, PWSH='', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                   CI='true', GITHUB_ACTIONS='true', RUNNER_OS='Windows', TMPDIR=root.as_posix(),
                   GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.autocrlf', GIT_CONFIG_VALUE_0='false')
        result = subprocess.run([bash, str(probe)], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.write_bytes(result.stdout)
        print(result.stdout.decode('utf-8'))
        print('Код сцени:', result.returncode)
        sys.exit(result.returncode)

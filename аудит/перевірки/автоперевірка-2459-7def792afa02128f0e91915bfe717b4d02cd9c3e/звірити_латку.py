"""Відтворює чисте застосування латки та порівнює байти з призначеною головою."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

база = '4d376dea236fe936cc37cf46ce851bb5226bd14c'
голова = '7def792afa02128f0e91915bfe717b4d02cd9c3e'
джерело = '7bb4cdaa2d4def0ce754f36b0ddca7827c23e9bf'
обгортка = 'аудит/адаптери/gemini'
раннер = 'аудит/проби/доробка_менше_прогонів.py'
тека = Path(sys.argv[1]).resolve()
тека.mkdir(parents=True, exist_ok=False)


def git(*аргументи, cwd=None):
    """Повертає байти Git; невдала команда зупиняє звірку."""
    return subprocess.check_output(['git', *аргументи], cwd=cwd)


архів = git('-c', 'core.autocrlf=false', 'archive', база, обгортка, раннер)
with tarfile.open(fileobj=io.BytesIO(архів)) as потік:
    потік.extractall(тека, filter='data')
латка = git('show', f'{джерело}:аудит/латки/обгортка-перевірка-після-кінця/зміни.patch')
шлях = тека.parent / 'source-2453-7bb4cdaa.patch'
шлях.write_bytes(латка)
git('init', '-q', cwd=тека)
git('config', 'core.autocrlf', 'false', cwd=тека)
git('add', '.', cwd=тека)
git('apply', '--check', str(шлях), cwd=тека)
print('git apply --check: код 0')
git('apply', str(шлях), cwd=тека)
print('git apply: код 0')
файли = git('ls-tree', '-r', '--name-only', голова, обгортка, раннер).decode('utf-8').splitlines()
відмінності = [файл for файл in файли if (тека / файл).read_bytes() != git('show', f'{голова}:{файл}')]
print(json.dumps(dict(база=база, голова=голова, джерело=джерело, файлів=len(файли), відмінності=відмінності), ensure_ascii=False))
print('BOM маніфесту: ' + (тека / обгортка / 'm9v/хеші.psd1').read_bytes()[:3].hex(' '))
assert not відмінності

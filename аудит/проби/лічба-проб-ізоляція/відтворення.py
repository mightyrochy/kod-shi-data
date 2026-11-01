"""Міряє ізоляцію, одноразового писача та незмінність файлів й індексу користувача.

Запуск: python -X utf8 аудит/проби/лічба-проб-ізоляція/відтворення.py [--до SHA]
Створює тільки власні малі репозиторії в TEMP; справжнє дерево не змінює.
Сценарії повторюють механізми перевірки #2707, без повторного запуску писача.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def git(тека, *арг):
    """Виконує git у власному репозиторії виміру."""
    return subprocess.run(['git', '-C', str(тека), *арг], check=True, capture_output=True).stdout


def вимір(код, сценарій):
    """Запускає справжній CLI приладу на малому відокремленому репозиторії."""
    with tempfile.TemporaryDirectory(prefix='лічба_властивість_') as тимч:
        тека = Path(тимч)
        репо = тека / 'repo'
        прилади = репо / 'джерела/прилади'
        проби = репо / 'джерела/проби'
        прилади.mkdir(parents=True)
        проби.mkdir()
        git(репо, 'init')
        git(репо, 'config', 'user.email', 'probe@localhost')
        git(репо, 'config', 'user.name', 'Проба')
        git(репо, 'config', 'core.autocrlf', 'false')
        (прилади / 'лічба_проб.py').write_bytes(код)
        (прилади / 'лічба_проб_окремо.json').write_text('{}', encoding='utf-8')
        (репо / 'джерела/чистка_каталогу.py').write_text(
            'def забезпечити_чистим(*args): pass\n', encoding='utf-8')
        (репо / 'README.md').write_bytes(b'base\n')
        (репо / 'AGENTS.md').write_bytes(b'base\n')
        (репо / 'джерела/код_із_дерева.py').write_text('стан = "база"\n', encoding='utf-8')
        (репо / '.gitignore').write_text('__pycache__/\n', encoding='utf-8')
        маркер = тека / 'одноразовий'
        if сценарій == 'одноразовий':
            текст = ('from pathlib import Path\nimport time\ntime.sleep(0.2)\n'
                     f'm = Path({str(маркер)!r})\n'
                     'if not m.exists():\n    m.write_text("1")\n'
                     '    p = Path("../README.md")\n'
                     '    p.write_bytes(p.read_bytes() + b"writer\\n")\n')
        elif сценарій == 'індекс':
            текст = ('from pathlib import Path\nimport subprocess\n'
                     'Path("../README.md").write_bytes(b"staged by probe\\n")\n'
                     'subprocess.run(["git", "add", "../README.md"], check=True)\n'
                     'Path("../README.md").write_bytes(b"base\\n")\n')
        elif сценарій == 'чужий_абсолютний':
            текст = ('from pathlib import Path\nimport subprocess\n'
                     f'r = Path({str(репо)!r})\n'
                     'p = r / "README.md"\np.write_bytes(p.read_bytes() + b"absolute\\n")\n'
                     'subprocess.run(["git", "-C", str(r), "add", "README.md"], check=True)\n'
                     '(r / "untracked.txt").write_bytes(b"new\\n")\n')
        elif сценарій == 'без_входу':
            текст = 'print("БЕЗ ВХОДУ: нема фікстури")\nraise SystemExit(77)\n'
        elif сценарій == 'чистий':
            текст = 'print("факт")\n'
        elif сценарій == 'стеля':
            текст = ('from pathlib import Path\nimport time\n'
                     'Path("../README.md").write_bytes(b"timeout\\n")\ntime.sleep(10)\n')
        else:
            raise ValueError(сценарій)
        (проби / 'writer.py').write_text(текст, encoding='utf-8')
        (проби / 'neighbor.py').write_text(
            'from pathlib import Path\nimport time\ntime.sleep(0.6)\n'
            'import код_із_дерева\nassert код_із_дерева.стан == "база"\n'
            'assert Path("../README.md").read_bytes() == b"base\\n"\n', encoding='utf-8')
        git(репо, 'add', '.')
        git(репо, 'commit', '-qm', 'Початок виміру')
        if сценарій in ('чистий', 'чужий_абсолютний'):
            (репо / 'README.md').write_bytes(b'user staged\n')
            git(репо, 'add', 'README.md')
            (репо / 'README.md').write_bytes(b'user unstaged\n')
            (репо / 'untracked.txt').write_bytes(b'user untracked\n')
            (репо / 'джерела/код_із_дерева.py').write_text('стан = "правка сесії"\n', encoding='utf-8')
        до = {ш: (репо / ш).read_bytes() for ш in ('README.md', 'AGENTS.md', 'джерела/код_із_дерева.py')}
        індекс_до = git(репо, 'ls-files', '--stage', '-z')
        журнал = тека / 'звіт.jsonl'
        р = subprocess.run([sys.executable, '-X', 'utf8', str(прилади / 'лічба_проб.py'),
                            '--гейт', '--лише', 'джерела/проби/writer.py', 'джерела/проби/neighbor.py'],
                           cwd=репо / 'джерела', capture_output=True, text=True, encoding='utf-8',
                           timeout=90, env=dict(os.environ, NYTOK='2', STELYA='2',
                                                ZVIT=str(журнал), PYTHONIOENCODING='utf-8'))
        рядки = [json.loads(р) for р in журнал.read_text(encoding='utf-8').splitlines()]
        писач = next(р for р in рядки if р['проба'].endswith('/writer.py'))
        сусід = next(р for р in рядки if р['проба'].endswith('/neighbor.py'))
        результат = dict(сценарій=сценарій, rc=р.returncode, писач=писач['rc'], сусід=сусід['rc'],
                         файли=писач.get('змінені_файли', []),
                         незмінний_вміст=all((репо / ш).read_bytes() == в for ш, в in до.items()),
                         незмінний_індекс=git(репо, 'ls-files', '--stage', '-z') == індекс_до,
                         відомі_дерева=len(git(репо, 'worktree', 'list', '--porcelain').split(b'worktree ')) - 1,
                         помилка_користувача='ДЕРЕВО КОРИСТУВАЧА ЗМІНИЛОСЯ: README.md, untracked.txt' in р.stdout)
        if сценарій == 'чужий_абсолютний':
            результат['правки_не_стерті'] = ((репо / 'README.md').read_bytes() == b'user unstaged\nabsolute\n'
                                            and (репо / 'untracked.txt').read_bytes() == b'new\n'
                                            and git(репо, 'show', ':README.md') == b'user unstaged\nabsolute\n')
        print(json.dumps(результат, ensure_ascii=False), flush=True)
        return результат


def main():
    """Друкує ДО або перевіряє властивості голови, а не список відомих писачів."""
    парсер = argparse.ArgumentParser()
    парсер.add_argument('--до')
    парсер.add_argument('--звіт', type=Path)
    а = парсер.parse_args()
    корінь = Path(__file__).resolve().parents[3]
    код = (git(корінь, 'show', а.до + ':джерела/прилади/лічба_проб.py') if а.до
           else (корінь / 'джерела/прилади/лічба_проб.py').read_bytes())
    результати = [вимір(код, с) for с in
                  ('одноразовий', 'індекс', 'чистий', 'чужий_абсолютний', 'без_входу', 'стеля')]
    if а.звіт:
        а.звіт.write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not а.до:
        for р in результати:
            assert р['відомі_дерева'] == 1, р
            if р['сценарій'] == 'чужий_абсолютний':
                assert р['rc'] == 1 and р['помилка_користувача'] and р['правки_не_стерті'], р
            else:
                assert р['незмінний_вміст'] and р['незмінний_індекс'] and р['сусід'] == 0, р
                if р['сценарій'] in ('чистий', 'без_входу'):
                    assert р['rc'] == 0 and р['писач'] == (77 if р['сценарій'] == 'без_входу' else 0), р
                else:
                    assert р['rc'] == 1 and р['писач'] != 0 and 'README.md' in р['файли'], р
    return 0


if __name__ == '__main__':
    sys.exit(main())

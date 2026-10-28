"""Накладає латки послідовно на чистий origin/main та звіряє хеші й нічну чергу."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

import yaml

КОРІНЬ = Path(__file__).resolve().parents[3]
ЛАТКИ = КОРІНЬ / 'аудит/латки/Е1-приймання-наживо'


def перевірити():
    """Перевіряє весь ланцюжок без редагування латок і робочого дерева виконавця."""
    тека = Path(tempfile.mkdtemp(prefix='E1-apply-'))
    def команда(*аргументи):
        return subprocess.check_output(аргументи, cwd=тека, encoding='utf-8', errors='replace')
    база = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=КОРІНЬ, text=True).strip()
    subprocess.run(['git', 'worktree', 'add', '-q', '--detach', str(тека), база], cwd=КОРІНЬ, check=True)
    порядок = []
    try:
        assert not команда('git', 'status', '--porcelain').strip()
        for файл in sorted(ЛАТКИ.glob('*.patch')):
            команда('git', 'apply', '--check', str(файл))
            команда('git', 'apply', str(файл))
            порядок.append({'латка': файл.name, 'sha256': hashlib.sha256(файл.read_bytes()).hexdigest()})
        команда('git', 'add', '--', '.github', 'аудит/адаптери/gemini')
        хеші = команда('python', 'аудит/адаптери/gemini/перевірка/перевірити_хеші.py')
        ніч = команда('powershell.exe', '-NoProfile', '-File', str(КОРІНЬ / 'аудит/проби/перевірити_нічний_маркер.ps1'),
                      '-WrapperRoot', str(тека / 'аудит/адаптери/gemini'))
        документи = {ім: yaml.safe_load((тека / '.github/workflows' / ім).read_text(encoding='utf-8'))
                     for ім in ('zbirka.yml', 'obhortka.yml')}
        джоби = документи['zbirka.yml']['jobs']
        assert 'pryimannia' in джоби['zbirka']['needs']
        assert "needs.pryimannia.result == 'success'" in джоби['zbirka']['if']
        крок = next(к for к in джоби['pryimannia']['steps'] if к.get('name') == 'записані сцени через продукт')
        assert 'живий_після_CI.js' in крок['run']
        assert not крок.get('continue-on-error') and not джоби['pryimannia'].get('continue-on-error')
        звіт = {'база': база, 'латки': порядок, 'apply_check': True, 'хеші': хеші, 'ніч': ніч,
                'крок_CI': крок, 'частин': len(джоби['pryimannia']['strategy']['matrix']['chastyna'])}
        (Path(__file__).parent / 'доробка-латки.json').write_text(
            json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps(звіт, ensure_ascii=False, indent=1))
    finally:
        assert тека.parent.resolve() == Path(tempfile.gettempdir()).resolve()
        subprocess.run(['git', 'worktree', 'remove', '--force', str(тека)], cwd=КОРІНЬ, check=True)


if __name__ == '__main__':
    перевірити()

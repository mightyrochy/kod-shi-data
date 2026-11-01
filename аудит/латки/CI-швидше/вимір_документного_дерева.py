"""Міряє фінальний храповик на повному документному дереві та звіряє числа з CI бази."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


def головний():
    """Створює документну зміну, рахує всі корені та зберігає час, код і повний підсумок."""
    артефакти = Path(__file__).resolve().parent
    репо = артефакти.parents[2]
    тимчасова = Path(os.environ['TEMP']).resolve()
    assert тимчасова.is_relative_to(репо.parent), тимчасова
    еталон = json.loads((артефакти / 'еталон-корені-CI.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='ci-doc-valid-', dir=тимчасова) as тека:
        дерево = Path(тека) / 'repo'
        subprocess.run(['git', '-C', str(репо), 'worktree', 'add', '--detach', str(дерево), еталон['коміт']],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            subprocess.run(['git', '-C', str(дерево), 'sparse-checkout', 'add', '/аудит/проби/б1/'], check=True)
            assert (дерево / 'аудит/проби/б1').is_dir()
            (дерево / 'аудит/наряди/CI-час.md').write_text('Документна зміна для виміру CI.\n', encoding='utf-8')
            ознака = Path(тека) / 'ознака.txt'
            команда = [sys.executable, str(репо / 'джерела/прилади/храповик_кореня.py'), '--репо', str(дерево),
                       '--база', еталон['коміт'], '--ознака-стенда', str(ознака)]
            середовище = dict(os.environ, PYTHONUTF8='0', PYTHONIOENCODING='utf-8')
            початок = time.monotonic()
            вихід = subprocess.run(команда, env=середовище, capture_output=True)
            секунд = round(time.monotonic() - початок, 3)
            текст = (вихід.stdout + вихід.stderr).decode('utf-8').replace('\r\n', '\n')
            (артефакти / 'храповик-документ-ПІСЛЯ.log').write_text(текст, encoding='utf-8', newline='\n')
            числа = {імя: (int(б), int(г)) for імя, б, г in
                     re.findall(r'- корінь ([^:\n]+): місць (\d+) → (\d+)', текст)}
            очікувані = {імя: (дані['голова'], дані['голова']) for імя, дані in еталон['корені'].items()}
            запис = dict(секунд=секунд, код=вихід.returncode, ядра=os.cpu_count(), команда=команда,
                         версія_python=sys.version, ознака=ознака.read_text(encoding='utf-8').strip(),
                         коренів=len(числа), числа_як_у_CI=числа == очікувані)
            (артефакти / 'храповик-документ-ПІСЛЯ.json').write_text(
                json.dumps(запис, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(запис, ensure_ascii=False), flush=True)
            assert вихід.returncode == 0, текст
            assert числа == очікувані, (числа, очікувані)
            assert запис['ознака'] == 'стенд=false', запис
        finally:
            assert дерево.resolve().is_relative_to(репо.parent)
            subprocess.run(['git', '-C', str(репо), 'worktree', 'remove', '--force', str(дерево)],
                           check=True, capture_output=True)
    return 0


if __name__ == '__main__':
    sys.exit(головний())

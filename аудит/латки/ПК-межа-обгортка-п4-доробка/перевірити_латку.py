"""Відтворює латку в окремому індексі git й звіряє точні SHA-256 файлів."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def перевірити():
    """Застосовує латку до записаної бази без зміни робочих файлів та поточного індексу."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    дані = json.loads((тека / 'файли.json').read_text(encoding='utf-8'))
    латка = тека / 'обгортка.patch'
    assert hashlib.sha256(латка.read_bytes()).hexdigest() == дані['sha256_латки']
    with tempfile.TemporaryDirectory(prefix='patch-index-') as тимчасова:
        середовище = dict(os.environ, GIT_INDEX_FILE=str(Path(тимчасова) / 'index'))

        def виклик(*аргументи):
            """Викликає git лише з ізольованим індексом."""
            return subprocess.check_output(['git', *аргументи], cwd=корінь, env=середовище)

        виклик('read-tree', дані['база'])
        виклик('apply', '--cached', '--check', str(латка))
        виклик('apply', '--cached', str(латка))
        for файл, очікуваний in дані['sha256_файлів'].items():
            вміст = виклик('show', ':' + файл)
            assert hashlib.sha256(вміст).hexdigest() == очікуваний, файл
        дерево = виклик('write-tree').decode('ascii').strip()
        обгортка = виклик('rev-parse', дерево + ':аудит/адаптери/gemini').decode('ascii').strip()
    print(f'✓ git apply --cached --check: база {дані["база"]}')
    print(f'✓ точні SHA-256: {len(дані["sha256_файлів"])} файли')
    print(f'✓ дерево обгортки: {обгортка}')


if __name__ == '__main__':
    перевірити()

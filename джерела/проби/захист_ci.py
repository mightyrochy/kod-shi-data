"""Факти наряду 5685: незакріплені action/пакети, права workflow та зовнішні ресурси показу.
Запуск: python3 проби/захист_ci.py [git-ref для ДО]; без ref читає робоче дерево.
"""
import json, re, subprocess, sys
from pathlib import Path

корінь = Path(__file__).resolve().parents[2]
def читати(імʼя):
    if len(sys.argv) > 1:
        return subprocess.check_output(['git', '-C', str(корінь), 'show', sys.argv[1] + ':' + імʼя]).decode()
    return (корінь / імʼя).read_text()

тексти = [читати('.github/workflows/' + н + '.yml') for н in ('zbirka', 'zhnyvarka', 'zhnyva', 'rozvidka')]
дії = re.findall(r'uses:\s*(\S+)', '\n'.join(тексти))
показ = читати('джерела/показ.html')
скрипти = re.findall(r'<script\b[^>]*\bsrc="https://[^>]+>', показ)
факти = {
    'uses_всього': len(дії),
    'uses_без_SHA40': sum(not re.fullmatch(r'[^@]+@[0-9a-f]{40}', д) for д in дії),
    'npm_i_без_lock': sum(len(re.findall(r'\bnpm\s+(?:i|install)\b', т)) for т in тексти),
    'pip_без_require_hashes': sum('pip install' in л and '--require-hashes' not in л for т in тексти for л in т.splitlines()),
    'workflow_глобальний_write': sum(bool(re.search(r'^permissions:\n  contents: write$', т, re.M)) for т in тексти),
    'workflow_типовий_read': sum(bool(re.search(r'^permissions:\n  contents: read$', т, re.M)) for т in тексти),
    'CDN_скрипти_без_SRI': sum('integrity="sha' not in с or 'crossorigin="anonymous"' not in с for с in скрипти),
    'Fixel_рухомий_main': показ.count('MacPaw/Fixel@main/'),
}
if len(sys.argv) == 1:
    lock = json.loads((корінь / 'джерела/package-lock.json').read_text())
    пакети = [п for імʼя, п in lock['packages'].items() if імʼя]
    факти['npm_пакети_з_integrity'] = sum(bool(п.get('integrity')) for п in пакети)
    факти['npm_пакети_всього'] = len(пакети)
print(json.dumps(факти, ensure_ascii=False))

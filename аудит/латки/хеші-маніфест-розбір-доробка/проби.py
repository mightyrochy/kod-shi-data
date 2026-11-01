"""Повторює проби маніфесту на окремому git-дереві перед застосуванням латки й після."""
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    """Змінює лише маніфест і таблицю тимчасового дерева, після проб відновлює їх."""
    дерево = Path(sys.argv[1]).resolve()
    корінь = дерево / 'аудит/адаптери/gemini'
    маніфест = корінь / 'm9v/хеші.psd1'
    таблиця = корінь / 'НАЛАШТУВАННЯ.md'
    текст = маніфест.read_text(encoding='utf-8')
    опис = таблиця.read_text(encoding='utf-8')
    рядок = re.search(r"^.*'wrapper_chain.ps1'.*$", текст, re.M).group()
    хеш = re.search(r"=\s*'([^']+)'", рядок).group(1)
    проби = {
        'чинний': (текст, опис, 0),
        'блоковий-коментар': (текст.replace(рядок, рядок.replace(хеш, '0' * 64)
                                            + '\n<#\n' + рядок + '\n#>'), опис, 1),
        'рядковий-коментар': (текст.replace(рядок, '# ' + рядок), опис, 1),
        'без-claude_run': (re.sub(r"^.*'claude_run.ps1'.*\n", '', текст, flags=re.M),
                           re.sub(r'^.*\| `claude_run.ps1`.*\n', '', опис, flags=re.M), 1),
        'дубль-ключа': (текст.replace(рядок, рядок + '\n' + рядок), опис, 1),
    }
    оточення = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    bash = os.environ.get('TEST_BASH', 'bash')
    вади = 0
    try:
        for назва, (вміст, док, очікуваний) in проби.items():
            маніфест.write_text(вміст, encoding='utf-8', newline='\n')
            таблиця.write_text(док, encoding='utf-8', newline='\n')
            subprocess.run(['git', 'add', str(маніфест), str(таблиця)], cwd=дерево, check=True, capture_output=True)
            команди = (
                [sys.executable, str(корінь / 'перевірка/перевірити_хеші.py')],
                [bash, str(корінь / 'перевірка/сценарії_m9v.sh')],
            )
            for команда in команди:
                if '--до' in sys.argv[2:]:
                    очікуваний = int(назва == 'дубль-ключа' and команда[0] == bash)
                результат = subprocess.run(команда, cwd=дерево, env=оточення,
                                           capture_output=True, encoding='utf-8', errors='replace')
                print(f'{назва}: {Path(команда[1]).name}: rc {результат.returncode}; очікувано {очікуваний}')
                print(результат.stdout + результат.stderr)
                вади += результат.returncode != очікуваний
    finally:
        маніфест.write_text(текст, encoding='utf-8', newline='\n')
        таблиця.write_text(опис, encoding='utf-8', newline='\n')
        subprocess.run(['git', 'add', str(маніфест), str(таблиця)], cwd=дерево, check=True, capture_output=True)
    print(f'Підсумок: 10 звірок; невідповідностей очікуваному результату: {вади}')
    return int(bool(вади))


if __name__ == '__main__':
    sys.exit(main())

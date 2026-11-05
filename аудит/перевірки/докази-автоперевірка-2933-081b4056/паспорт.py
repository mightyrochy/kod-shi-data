"""Повторює розбір паспорта бази й голови чинним храповиком, без зміни файлів."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def головна():
    """Читає обидві версії через git і друкує помилки штатного парсера."""
    репо = Path(__file__).resolve().parents[3]
    дерево = Path(sys.argv[1]).resolve()
    специфікація = importlib.util.spec_from_file_location(
        'храповик_2933', дерево / 'джерела/прилади/храповик_кореня.py')
    модуль = importlib.util.module_from_spec(специфікація)
    sys.modules[специфікація.name] = модуль
    специфікація.loader.exec_module(модуль)
    результат = {}
    for мітка, ref in (('до', 'da74a751ea07d72191c690a1f68e9338c11b85ca'),
                       ('після', '081b40567257c48b578763f5ec0641aca5f13055')):
        текст = subprocess.check_output(
            ['git', 'show', ref + ':аудит/корені/Річ-запис-речі.md'], cwd=репо, encoding='utf8')
        помилки = модуль.розібрати_паспорт(текст)[3]
        результат[мітка] = dict(кількість=len(помилки), помилки=помилки)
    print(json.dumps(результат, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    головна()

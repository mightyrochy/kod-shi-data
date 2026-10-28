"""Записує фактичні інтервали компаньйонів відомої проби K-PAL-16."""
import json
import os
import pathlib
import runpy
import sys
from collections import deque

КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
import palettes as П
import колір_річ as КР


def головна():
    """Повторює незмінену пробу й зберігає останні фактичні входи її суду."""
    записи = deque(maxlen=8)
    оригінал = П.контекст_втягує
    def записати(осі, речі):
        """Фіксує передані числа й висновок, не змінюючи вхід або результат."""
        результат = оригінал(осі, речі)
        записи.append(dict(hue=осі['позиція']['hue'], речі=[dict(
            id=р.get('id'), частка=р.get('_частка_вікна'), lab=р.get('lab'),
            колір_не_вимір=р.get('колір_не_вимір'),
            межі_b=КР.межі_b(р) if КР.межі_кольору(р) is not None else None)
            for р in речі], висновок=результат))
        return результат
    П.контекст_втягує = записати
    попередня_тека = pathlib.Path.cwd()
    os.chdir(КОРІНЬ / 'джерела')
    try:
        runpy.run_path(str(КОРІНЬ / 'джерела/проби/pal_K-PAL-16.py'), run_name='__main__')
    finally:
        П.контекст_втягує = оригінал
        os.chdir(попередня_тека)
        назва = 'контекст-ПІСЛЯ.json' if '--після' in sys.argv else 'контекст-ДО.json'
        pathlib.Path(__file__).with_name(назва).write_text(
            json.dumps(list(записи), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    головна()

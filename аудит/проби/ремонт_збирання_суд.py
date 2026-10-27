"""Повтор межі внутрішнього суду на записаних складах і вироках серії 2, без моделі."""
import ast
import json
import subprocess
import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
import pipeline as П


def main():
    """Звіряє належність кожного поверненого вироку складу, який просили судити."""
    текст = (subprocess.check_output(['git', 'show', sys.argv[1] + ':джерела/міст_відповіді.py'],
                                   cwd=КОРІНЬ, encoding='utf8') if len(sys.argv) > 1 else
             (КОРІНЬ / 'джерела/міст_відповіді.py').read_text(encoding='utf8'))
    дерево = ast.parse(текст)
    суддя = next(n for n in ast.walk(дерево) if isinstance(n, ast.FunctionDef) and n.name == '_суддя')
    код = compile(ast.Module(body=[суддя], type_ignores=[]), '<внутрішній суд мосту>', 'exec')
    л = dict(пакетів=0, складів=0, чужих=0, втрачених=0, порожні_зсувають=0)
    for файл in sorted((КОРІНЬ / 'аудит/проби/б1/ДО-2710').glob('*/вердикти.txt')):
        for прогін in json.loads(файл.read_text(encoding='utf8'))['прогони']:
            for рука in прогін['вердикти']:
                if рука['рука'] not in ('1', '2'):
                    continue
                for крок in рука['етапи']['виклики']:
                    записи = крок.get('образи_кроку') or []
                    if not записи:
                        continue
                    середовище = dict(d={}, F=None, T=None, сцен={}, пак={}, _P=П, _вип=None,
                                      вердикти_образів=lambda *a, **kw: записи)
                    exec(код, середовище)
                    суди = середовище['_суддя']([о['ід'] for о in записи])
                    assert len(суди) == len(записи), 'Суд загубив позицію набору'
                    з_порожніми = середовище['_суддя']([[], *[о['ід'] for о in записи], []])
                    л['порожні_зсувають'] += з_порожніми != [None, *суди, None]
                    справжні = {о['ід']: о for о in П.вердикт_v1(записи)['образи']}
                    for запис, суд in zip(записи, суди):
                        очікуваний = справжні.get(запис['номер'])
                        л['складів'] += 1
                        л['втрачених'] += очікуваний is not None and суд is None
                        л['чужих'] += суд is not None and суд != очікуваний
                    л['пакетів'] += 1
    print(json.dumps(л, ensure_ascii=False))
    return int(bool(л['чужих'] or л['втрачених'] or л['порожні_зсувають'] or not л['складів']))


if __name__ == '__main__':
    sys.exit(main())

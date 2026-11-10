"""Повторює архівну сцену штатним стендом, без зміни моста й записаних відповідей."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def повторити(запис, показ, pyodide, вихід):
    """Бере всі параметри сцени з її запису; зберігає повний журнал і код завершення."""
    запис, показ, pyodide, вихід = (п.resolve() for п in (запис, показ, pyodide, вихід))
    вихід.mkdir(parents=True, exist_ok=True)
    параметри = json.loads((запис / 'повтор.json').read_text(encoding='utf-8'))
    жінка = вихід / 'ж4.json'
    жінка.write_text(json.dumps(параметри['жінка'], ensure_ascii=False), encoding='utf-8')
    середовище = dict(os.environ, **параметри['змінні'], ZHINKA=str(жінка),
                     REPLAY_EXCHANGE=str(запис / 'VIDPOVIDI' / 'обмін'),
                     ZNIMKY=str(вихід), ZAPYS_VYKLYKIV=str(вихід / 'виклики.jsonl'))
    команда = ['node', 'аудит/проби/рв6_стенд.js', 'http://127.0.0.1:8765',
               str(показ), str(pyodide), str(параметри['сід'])]
    with (вихід / 'лог.txt').open('w', encoding='utf-8') as журнал:
        результат = subprocess.run(команда, env=середовище, stdout=журнал, stderr=subprocess.STDOUT)
    (вихід / 'код.json').write_text(json.dumps({'команда': команда, 'код': результат.returncode},
                                             ensure_ascii=False, indent=2), encoding='utf-8')
    print('Штатний REPLAY_EXCHANGE:', результат.returncode, вихід)
    return результат.returncode


if __name__ == '__main__':
    п = argparse.ArgumentParser(description=__doc__)
    for ім in ('запис', 'показ', 'pyodide', 'вихід'):
        п.add_argument(ім, type=Path)
    а = п.parse_args()
    raise SystemExit(повторити(а.запис, а.показ, а.pyodide, а.вихід))

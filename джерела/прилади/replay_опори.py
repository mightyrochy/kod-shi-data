"""Суд підтвердження ДО (з формами) і ПІСЛЯ (полями речення) на тих самих нових записах (рішення менеджера 08.11).

Записи — тестовий прогін сцен `replay_картки_живий._РОЗМІТКА` з новим промптом: тека з `<сцена>/VIDPOVIDI/
seed*_NN_мовний_шар_{хід_розмови,репліка}.txt` (формат той самий, що в `аудит/живі_2610-1-2`). Розмітка — JSON
{"<сцена>/<файл>": "10…"}: по символу на речення в порядку `мовний_шар._РЕЧЕННЯ.split` над `says` (хід) чи `text`
(репліка), «1» — добре підтвердження, «0» — чуже. Розмічає не виконавець кроку, не бачивши вердиктів.

ДО — суд `main` 1f065f6b (до #3335): `суд_підтвердження(речення, записано)`; ПІСЛЯ — суд кроку над полями речення
(`about`, `her_words`): друге речення того самого `says` полів не має. Друкує лічбу за реченнями й за записами.
"""
import argparse
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_ДО = '1f065f6b'
_КОРІНЬ = Path(__file__).resolve().parents[2]


def _записи(тека):
    """(сцена/файл, вид, вхід, відповідь-об'єкт) для кожного запису ходу й репліки."""
    for шлях in sorted(Path(тека).glob('*/VIDPOVIDI/*_мовний_шар_*.txt')):
        т = шлях.read_text(encoding='utf8')
        промпт, відповідь = т.split('\n\n── ВІДПОВІДЬ', 1)
        промпт = промпт.split('\n', 1)[1]
        вид = 'хід' if 'хід_розмови' in шлях.name else 'репліка' if 'репліка' in шлях.name else None
        if not вид:
            continue
        вхід = json.loads(промпт if вид == 'хід' else промпт.split('РЕПЛІКА:\n')[1])
        сира = відповідь.split('──\n', 1)[1].strip()
        об = json.loads(re.sub(r'^```json\s*|\s*```$', '', сира).strip())
        yield '%s/%s' % (шлях.parts[-3], шлях.stem), вид, вхід, сира, об


def _речення(м, частини):
    """[(речення, частина з полями чи без)] — порядок розмітки."""
    вих = []
    for ч in частини if isinstance(частини, list) else [{'says': частини}]:
        ч = ч if isinstance(ч, dict) else {'says': ч}
        for і, x in enumerate(x for x in м._РЕЧЕННЯ.split(str(ч.get('says') or '')) if x.strip()):
            вих.append((x, dict(ч, says=x) if і == 0 else {'says': x}))
    return вих


def виміряти(тека, розмітка, код, після):
    """Лічба одного суду (ДО — речення текстом, ПІСЛЯ — полями) на записах."""
    sys.path.insert(0, str(код))
    with contextlib.redirect_stdout(io.StringIO()):
        import мовний_шар as м
    л = dict(записів=0, добрих=0, хибних_відмов=0, чужих=0, прийнято_чужих=0, записів_з_хибними=0)
    докази = []
    for ключ, вид, вхід, сира, об in _записи(тека):
        if ключ not in розмітка:
            continue
        if вид == 'хід':
            пр = м.прийняти_розмову(сира)
            with contextlib.redirect_stdout(io.StringIO()):
                записано = м.паспорт_з_шару(пр['внутрішня'], {}, слова_ходу=[вхід['her_new_message']],
                                            частини=пр['частини'])['записано']
            частини = об.get('text') or []
        else:
            записано, частини = вхід.get('recorded', {}), об.get('text')
        речення = _речення(м, частини)
        assert len(речення) == len(розмітка[ключ]), ключ
        хибна = False
        for (x, ч), позначка in zip(речення, розмітка[ключ]):
            прийнято = bool(м.суд_підтвердження(ч if після else x, записано)[0])
            добре = позначка == '1'
            л['добрих'] += добре
            л['хибних_відмов'] += добре and not прийнято
            л['чужих'] += not добре
            л['прийнято_чужих'] += (not добре) and прийнято
            хибна |= добре and not прийнято
            докази.append(dict(запис=ключ, речення=x, добре=добре, прийнято=прийнято))
        л['записів'] += 1
        л['записів_з_хибними'] += хибна
    return л, докази


def main():
    """Друк лічби ДО й ПІСЛЯ (кожен суд — окремим процесом зі свого дерева); `--запис` — повний розбір речень."""
    а = argparse.ArgumentParser(description=__doc__)
    а.add_argument('записи', type=Path)
    а.add_argument('розмітка', type=Path)
    а.add_argument('--до', default=_ДО)
    а.add_argument('--запис', type=Path)
    а.add_argument('--один', nargs=2, metavar=('КОД', 'ПІСЛЯ'), help=argparse.SUPPRESS)
    п = а.parse_args()
    if п.один:
        розмітка = json.loads(п.розмітка.read_text(encoding='utf8'))
        print(json.dumps(виміряти(п.записи, розмітка, Path(п.один[0]), п.один[1] == '1'), ensure_ascii=False))
        return

    def суд(код, після):
        вивід = subprocess.run([sys.executable, '-W', 'ignore', __file__, str(п.записи), str(п.розмітка),
                                '--один', str(код), '1' if після else '0'], capture_output=True, text=True, check=True)
        return json.loads(вивід.stdout.strip().splitlines()[-1])
    with tempfile.TemporaryDirectory(prefix='суд-до-') as т:
        subprocess.run('git archive %s джерела | tar -x -C %s' % (п.до, т), shell=True, check=True, cwd=_КОРІНЬ)
        до = суд(Path(т) / 'джерела', False)
    після = суд(_КОРІНЬ / 'джерела', True)
    print(json.dumps(dict(ДО=до[0], ПІСЛЯ=після[0]), ensure_ascii=False))
    if п.запис:
        п.запис.write_text(json.dumps(dict(ДО=до[1], ПІСЛЯ=після[1]), ensure_ascii=False, indent=1) + '\n',
                           encoding='utf8')


if __name__ == '__main__':
    main()

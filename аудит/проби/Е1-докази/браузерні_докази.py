"""Доводить храповик у Chromium/Pyodide на справжньому живому обміні."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

КОРІНЬ = Path(__file__).resolve().parents[3]


def перевірити():
    """Виконує базу, регрес інтерфейсу та зміну входу моделі без живих запитів."""
    збірка, кеш, вихід = map(lambda р: Path(р).resolve(), sys.argv[1:4])
    вихід.mkdir(parents=True, exist_ok=False)
    html = (збірка / 'index.html').read_text(encoding='utf-8')
    підміни = {
        'регрес': ("? 'Готово' : 'Далі'", "? 'Далі' : 'Далі'"),
        'застарілий': ('messages:повідомлення', 'messages:[]'),
    }
    звіт = []
    for назва in (sys.argv[4:] or ('база', 'регрес', 'застарілий')):
        копія = вихід / назва
        копія.mkdir()
        сторінка = html
        if назва in підміни:
            до, після = підміни[назва]
            assert html.count(до) == 1, (назва, html.count(до))
            сторінка = html.replace(до, після, 1)
        (копія / 'index.html').write_text(сторінка, encoding='utf-8')
        env = {к: з for к, з in os.environ.items() if not к.startswith('REPLAY_')}
        if назва == 'база':
            env['REPLAY_BASE_BUILD'] = str(збірка)
        команда = ['node', str(КОРІНЬ / 'аудит/проби/приймання_записів.js'),
                   str(копія), str(кеш), str(копія / 'результат'), '0', '1']
        початок = time.monotonic()
        print('Початок: ' + назва, flush=True)
        with (копія / 'приймання.log').open('w', encoding='utf-8') as лог:
            результат = subprocess.run(команда, cwd=КОРІНЬ, env=env, stdout=лог, stderr=subprocess.STDOUT, timeout=1300)
        підсумок = json.loads((копія / 'результат/підсумок.json').read_text(encoding='utf-8'))
        assert len(підсумок) == 1
        р = підсумок[0]
        очікуване = {'база': (0, 'без регресу'), 'регрес': (1, 'регрес'), 'застарілий': (0, 'запис застарів')}[назва]
        assert (результат.returncode, р['стан']) == очікуване, (назва, результат.returncode, підсумок)
        if назва == 'регрес':
            assert any('три кроки' in с for с in р['регресії'])
        if назва == 'застарілий':
            assert р['виклик'] == 1 and р['rc'] == 3
            assert 'ЖИВИЙ ПІСЛЯ:' in (копія / 'приймання.log').read_text(encoding='utf-8')
        звіт.append({'проба': назва, 'rc_приймання': результат.returncode,
                     'секунд': round(time.monotonic() - початок, 1), **р})
        (вихід / 'браузерні-5.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print('Завершено: ' + назва + ', rc=' + str(результат.returncode), flush=True)
    print(json.dumps(звіт, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    перевірити()

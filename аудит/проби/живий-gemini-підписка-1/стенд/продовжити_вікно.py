"""Спроба /6: по одній ситуації, два проходи, квота й коміт після кожної.

Запуск із кореня репозиторію: python .../продовжити_вікно.py
Наявну с4 Flash не запускає й не перезаписує. Пуш виконує обгортка.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ATTEMPT = BASE / 'спроба_6'
ATTEMPT.mkdir(exist_ok=True)
TEMP = Path(os.environ['TEMP'])
STOR = TEMP / 'сторінка_спроба_6'
STOR.mkdir(exist_ok=True)
BUILD = '8dafc1113ba09cdc5459cead2c0878fbc14b2b37'
EXPECTED = '890864aa7b59a89da48560a83f50f4123ad8131031b0acbf156bce2909b2ca94'
html = subprocess.check_output(['git', 'show', '855d862368d2ad8e120fd7b083ec5b854c8728e8:index.html'])
assert hashlib.sha256(html).hexdigest() == EXPECTED, 'Збірка відрізняється від с4'
(STOR / 'index.html').write_bytes(html)
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           STOR=str(STOR), PYODIDE=r'C:\Users\gemini\pyodide',
           NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')
SCENES = sorted(p.name for p in (BASE.parent / 'живий-як-людина-1').glob('с[1-8]_*') if p.is_dir())
PLAN = [('gemini-3.8-flash', s) for s in SCENES if not s.startswith('с4_')]
PLAN += [('gemini-4-hydrogen', s) for s in SCENES]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def quota(raw):
    result = {}
    for line in raw.splitlines():
        parts = line.split('\t')
        if len(parts) >= 4 and parts[0] == 'Gemini Models':
            key = 'тиждень' if parts[1] == 'Weekly Limit Remaining' else 'п’ять_годин'
            result[key] = {'залишок': int(parts[2].rstrip('%')), 'скидання': parts[3]}
    assert set(result) == {'тиждень', 'п’ять_годин'}, 'Не вдалося прочитати квоту'
    return result


def status():
    remaining = [(m, s) for m, s in PLAN if not (BASE / m / s / 'підсумок.json').exists()]
    state['лишилось'] = [{'модель': m, 'ситуація': s} for m, s in remaining]
    write(ATTEMPT / 'стан.json', state)
    return remaining


def report():
    lines = ['# Спроба 6: продовження по вікнах квоти', '',
             'Жінка — скрипт зі словами першого прогону (слово власника 14.11 07:08 UTC). '
             'Слова про образи стосуються першого прогону; вони не є оцінкою образів Gemini.', '',
             f'Стан: {state["статус"]}. Початок UTC: {state["початок_utc"]}.', '',
             f'Голова main під час запуску: `{state["main_на_старті"]}`; main наряду /6: '
             '`8fb1770114c6f04863752d3be7aa71e7c42ca76c`.', '',
             'Продовження використовує ту саму готову CI-збірку, що й виконана с4 Flash: '
             f'`{BUILD}`, SHA256 `{EXPECTED}`. Джерела відповідного main: '
             '`855d862368d2ad8e120fd7b083ec5b854c8728e8`; первісна звірка AST і каталогу — '
             '`../спроба_5/відповідність_збірки.json`. Поточну новішу збірку не підмішано до серії.', '',
             'CLI: Flash Low продовжує зусилля с4. Hydrogen Low — найнижче доступне зусилля '
             'тієї самої моделі; це не доводить еквівалентності налаштуванню API. '
             'Транспорт, системне доручення agy, фото через файли й read_file, стелі 660/630 с '
             'залишені як у спробі 5; дозволи не розширено.', '',
             'Після кожної ситуації: знімки, хід, сирі входи й відповіді, фото з SHA256, '
             'руки.md та розбіжності.md — у теці моделі; квота й запуск — у підтеці цієї спроби. '
             'Усі розпочаті ситуації проходять обидва записані проходи.', '',
             '| модель · ситуація | реплік введено | пропущено | розбіжностей дій | квота 5 год | квота тижня | порт |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for x in state['завершено']:
        q = x['квота_після']
        lines.append(f'| {x["модель"]} · {x["ситуація"]} | {x["слів_лягло"]} | '
                     f'{x["слів_пропущено"]} | {x["розбіжностей"]} | '
                     f'{q["п’ять_годин"]["залишок"]} % | {q["тиждень"]["залишок"]} % | {x["порт"]} |')
    lines += ['', 'Квота до: ' + json.dumps(state['квота_до'], ensure_ascii=False), '',
              'Квота після: ' + json.dumps(state.get('квота_після'), ensure_ascii=False), '',
              'Лишилось:', '']
    lines += [f'- {x["модель"]}: {x["ситуація"]}' for x in state['лишилось']]
    if not state['лишилось']:
        lines += ['- Немає.']
    lines += ['', 'Межі вікна з наряду /6: наступну ситуацію не починати, коли після '
              'попередньої лишилося менше 10 % за 5 год або менше 20 % за тиждень. '
              'Падіння квоти — спільний округлений показник групи, не тариф одного процесу.', '',
              'Оцінок якості образів не ставлено; суддю призначає диспетчер. '
              'Зведення HTTP-статусів attico.ua й перевірка повноти — у зведення.json кожної моделі. '
              'Нових вад продукту поза мірилом не встановлено.', '']
    (ATTEMPT / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def commit(title):
    body = (title + '\n\nЩо змінено: продовжено живий повтор за нарядом /6; '
            'с4 Flash збережено без повторного запуску. Дані й квоти — аудит/проби/живий-gemini-підписка-1/спроба_6/.\n\n'
            f'ДО → ПІСЛЯ: 1 → {1 + len(state["завершено"])} ситуацій із 16 пар моделі й ситуації; '
            'кожна завершена ситуація має два записані проходи.\n\n'
            'Перевірено: python аудит/проби/живий-gemini-підписка-1/стенд/продовжити_вікно.py; '
            'сирі відповіді, дослівні входи, архів фото, мапа рук і квота після кожної ситуації.\n\n'
            'Лишилось: ' + ', '.join(x['модель'] + '/' + x['ситуація'] for x in state['лишилось']) + '\n\n'
            'Вад продукту поза мірилом не встановлено. Оцінювання образів — окремим судом диспетчера.\n')
    msg = TEMP / 'коміт_спроба_6.txt'
    msg.write_text(body, encoding='utf-8')
    subprocess.run(['git', 'add', '--', str(BASE)], check=True)
    subprocess.run(['git', 'commit', '-F', str(msg)], check=True)


state = {'початок_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'main_на_старті': subprocess.check_output(['git', 'rev-parse', 'origin/main'], text=True).strip(),
         'статус': 'виконується', 'завершено': [], 'квота_до': None}
resume = ''
if (ATTEMPT / 'стан.json').exists():
    state = json.loads((ATTEMPT / 'стан.json').read_text(encoding='utf-8'))
    state['статус'] = 'виконується'
    state.setdefault('відновлення_utc', []).append(datetime.datetime.now(datetime.timezone.utc).isoformat())
    resume = f'відновлення_{len(state["відновлення_utc"])}_'
try:
    for args, name in [(['agy', 'models'], 'моделі'), (['agy', '-p', '/usage'], 'квота_до')]:
        result = subprocess.run(args, cwd=TEMP, capture_output=True, timeout=120, env=env)
        (ATTEMPT / (resume + name + '.stdout.txt')).write_bytes(result.stdout)
        (ATTEMPT / (resume + name + '.stderr.txt')).write_bytes(result.stderr)
        assert result.returncode == 0, name + ': CLI відхилила запит'
    current_quota = quota((ATTEMPT / (resume + 'квота_до.stdout.txt')).read_text(encoding='utf-8'))
    state['квота_до'] = state['квота_до'] or current_quota
    state['квота_після'] = current_quota
    models = (ATTEMPT / (resume + 'моделі.stdout.txt')).read_text(encoding='utf-8')
    for model in ['gemini-3.8-flash-low', 'gemini-4-hydrogen-low']:
        assert model + '\t' in models, 'Нема моделі: ' + model
    status()
    report()
    for model, scene in PLAN:
        out = BASE / model
        if (out / scene / 'підсумок.json').exists():
            continue
        q = state['квота_після']
        if q['п’ять_годин']['залишок'] < 10 or q['тиждень']['залишок'] < 20:
            state['статус'] = 'ГОТОВО: частину вікна завершено; наступні ситуації після скидання'
            break
        snap = ATTEMPT / model / scene
        snap.mkdir(parents=True, exist_ok=True)
        # Зберігаємо метадані с4 й попередніх запусків перед повторним використанням теки моделі.
        before = snap / 'попередні_метадані'
        before.mkdir(exist_ok=True)
        if out.exists():
            for name in ['запуск.json', 'квота_до.stdout.txt', 'квота_до.stderr.txt', 'квота_до.json',
                         'квота_після.stdout.txt', 'квота_після.stderr.txt', 'квота_після.json']:
                if (out / name).exists():
                    shutil.copy2(out / name, before / name)
        print('ПОЧАТОК', model, scene, flush=True)
        with (snap / 'запуск.log').open('wb') as log:
            result = subprocess.run([sys.executable, str(HERE / 'запустити_повтор.py'), str(out),
                                     model + '-low', model, scene], env=env, stdout=log, stderr=log)
        for name in ['запуск.json', 'квота_до.stdout.txt', 'квота_до.stderr.txt', 'квота_до.json',
                     'квота_після.stdout.txt', 'квота_після.stderr.txt', 'квота_після.json']:
            if (out / name).exists():
                shutil.copy2(out / name, snap / name)
        state['квота_після'] = quota((snap / 'квота_після.stdout.txt').read_text(encoding='utf-8'))
        assert result.returncode == 0, 'Збій повтору: ' + model + '/' + scene
        summary = json.loads((out / scene / 'підсумок.json').read_text(encoding='utf-8'))
        assert summary['проходів'] == 2, 'Не пройдено два проходи: ' + scene
        state['завершено'].append({'модель': model, 'ситуація': scene,
                                  'слів_лягло': summary['слів_лягло'],
                                  'слів_пропущено': summary['слів_пропущено'],
                                  'розбіжностей': len(summary['розбіжності']),
                                  'квота_після': state['квота_після'],
                                  'порт': json.loads((snap / 'запуск.json').read_text(encoding='utf-8'))['порт_моста']})
        with (snap / 'зведення.log').open('wb') as log:
            subprocess.run([sys.executable, str(HERE / 'підсумувати_повтор.py'), str(out)],
                           env=env, stdout=log, stderr=log, check=True)
        status()
        report()
        commit('Живий Gemini: ' + model + ' — ' + scene + ', два проходи')
        print('ЗАВЕРШЕНО', model, scene, json.dumps(state['квота_після'], ensure_ascii=False), flush=True)
    else:
        state['статус'] = 'ГОТОВО: усі ситуації обох моделей завершено'
except Exception as exc:
    state['статус'] = 'ЗАБЛОКОВАНО: ' + str(exc)
    raise
finally:
    status()
    state['кінець_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write(ATTEMPT / 'стан.json', state)
    report()
    print(state['статус'], flush=True)

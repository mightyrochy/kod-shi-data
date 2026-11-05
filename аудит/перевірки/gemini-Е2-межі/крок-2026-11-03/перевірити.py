"""Виконати батарею або проби кроку, зберегти повні журнали й коди завершення."""


def main():
    """Виконати перевірку або запис стану лише при прямому запуску."""
    import json
    import os
    from pathlib import Path
    import subprocess
    import sys

    ТЕКА = Path(__file__).resolve().parent
    РЕПО = ТЕКА.parents[3]
    ДЖЕРЕЛА = РЕПО / 'джерела'
    СЕРЕДОВИЩЕ = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    РЕЖИМ = sys.argv[1]
    if РЕЖИМ == 'підготовка':
        КОМАНДИ = [['python', '-c', "import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"]]
    elif РЕЖИМ == 'батарея':
        КОМАНДИ = [
            ['python', 'стенд_знімок.py', '--дим'],
            ['python', 'тест_живого_шляху.py'],
            ['python', 'тест_протоколу.py'],
            ['python', 'прилади/розділи_гейтів.py'],
            ['python', 'audit_contracts.py'],
            ['node', 'тест_показу.js'],
        ]
    else:
        ПРОБИ = sorted((ДЖЕРЕЛА / 'проби').glob('е2_*.py'))
        ПРОБИ += [ДЖЕРЕЛА / 'проби' / ім for ім in (
            'паспорт_факт.py', 'картка_replay.py', 'дріт_каблук_4641.py',
            'паспорт_гілка_плитки_6571.py', 'поділ_pipeline_ast.py', 'поділ_feed_ast.py',
            'поділ_колір_образу_ast.py')]
        КОМАНДИ = [['python', str(п)] for п in ПРОБИ]
    РЕЗУЛЬТАТИ = []
    for н, команда in enumerate(КОМАНДИ, 1):
        журнал = ТЕКА / f'{РЕЖИМ}-{н:02}.txt'
        print('Запуск:', ' '.join(команда), flush=True)
        with журнал.open('w', encoding='utf-8') as вихід:
            р = subprocess.run(команда, cwd=ДЖЕРЕЛА, env=СЕРЕДОВИЩЕ,
                               stdout=вихід, stderr=subprocess.STDOUT)
        РЕЗУЛЬТАТИ.append(dict(команда=команда, код=р.returncode, журнал=журнал.name))
        (ТЕКА / f'{РЕЖИМ}.json').write_text(json.dumps(РЕЗУЛЬТАТИ, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Код:', р.returncode, flush=True)
    sys.exit(int(any(р['код'] for р in РЕЗУЛЬТАТИ)))


if __name__ == '__main__':
    main()

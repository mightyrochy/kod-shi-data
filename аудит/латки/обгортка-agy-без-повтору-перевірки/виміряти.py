"""Звіряє весь тижневий зріз agy з первинними журналами без запуску моделей."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re


def читати(шлях):
    """Читає UTF-8, зокрема PowerShell-файли з BOM."""
    return шлях.read_text(encoding='utf-8-sig')


def відбиток(шлях):
    """Обчислює SHA-256 первинного джерела."""
    return hashlib.sha256(шлях.read_bytes()).hexdigest()


def голови(події, номер_pr):
    """Витягає лише явні свідчення голови PR з відповідей інструментів.

    Голова робочої гілки перевірки й SHA main не є головою перевірюваного PR.
    Неоднозначні або відсутні свідчення залишаються невідомими.
    """
    знайдено = []
    for номер, подія in події:
        крок = подія.get('step_update', {})
        інструмент = крок.get('tool_info') or {}
        команда = (інструмент.get('parameters') or {}).get('CommandLine', '')
        вихід = інструмент.get('output') or ''
        if крок.get('state') != 'DONE' or not isinstance(вихід, str):
            continue
        sha = []
        про_цей_pr = bool(номер_pr and re.search(
            rf'(?:pulls/{номер_pr}(?![\d/])|gh pr view\s+{номер_pr}\b|refs/pull/{номер_pr}/head)', команда))
        for рядок in вихід.splitlines():
            sha += re.findall(r'\b([0-9a-f]{40})\s+refs/pull/\d+/head\b', рядок)
            if про_цей_pr:
                sha += re.findall(r'(?i)\bhead(?:[_. ]?(?:sha|refOid))?\s*["\x27]?\s*[:=]\s*["\x27`]?([0-9a-f]{40})\b', рядок)
        # Повна відповідь REST з об'єктом head, або gh --json headRefOid.
        for позиція, символ in enumerate(вихід):
            if символ != '{' or not про_цей_pr:
                continue
            try:
                обєкт, _ = json.JSONDecoder().raw_decode(вихід[позиція:])
            except ValueError:
                continue
            if isinstance(обєкт, dict):
                значення = обєкт.get('headRefOid')
                if not значення and isinstance(обєкт.get('head'), dict):
                    значення = обєкт['head'].get('sha')
                if isinstance(значення, str) and re.fullmatch('[0-9a-f]{40}', значення):
                    sha.append(значення)
        # rev-parse одного віддаленого продуктового ref, не HEAD/main/гілки перевірки.
        збіг = re.search(r'\bgit rev-parse\s+((?:remotes/)?origin/gemini/[^\s;|]+)\s*$', команда)
        if збіг and not re.search(r'/(?:авто)?перевірка-', збіг[1]):
            тіло = вихід.split('Command output:', 1)[-1].strip()
            if re.fullmatch('[0-9a-f]{40}', тіло):
                sha.append(тіло)
        for значення in sorted(set(sha)):
            знайдено.append({'sha': значення, 'рядок_потоку': номер})
    return знайдено


def виконати():
    """Зберігає записи всіх сесій, кожного повтору й контрольні суми джерел."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--запуски', type=Path, required=True)
    парсер.add_argument('--джерело', type=Path, default=Path('аудит/витрати/токени_ноутбука_0511/запуски.csv'))
    парсер.add_argument('--стани', type=Path, default=Path('C:/Users/Public/gemini/out'))
    парсер.add_argument('--вихід', type=Path, default=Path(__file__).resolve().parent)
    арг = парсер.parse_args()
    арг.вихід.mkdir(parents=True, exist_ok=True)
    журнал = арг.запуски / 'wrapper.log'
    журнал_байти = журнал.read_bytes()
    рядки = журнал_байти.decode('utf-8-sig').splitlines()
    оригінали = list(csv.DictReader(арг.джерело.open(encoding='utf-8-sig', newline='')))
    зріз = [р for р in оригінали if р['рушій'] == 'agy']
    сесії = [р for р in зріз if р['стадія'] == 'сесія моделі']
    свідчення = []
    for р in sorted(сесії, key=lambda р: (р['початок_UTC'], р['ід'])):
        тека = арг.запуски / р['ід']
        файли = {н: тека / н for н in ('worker.json', 'prompt.md', 'agy.jsonl', 'agy.stderr.txt')}
        робітник = json.loads(читати(файли['worker.json']))
        промпт = читати(файли['prompt.md'])
        події = [(н, json.loads(т)) for н, т in enumerate(читати(файли['agy.jsonl']).splitlines(), 1) if т.strip().startswith('{')]
        результати = [(н, п['result']) for н, п in події if п.get('event') == 'result']
        номер, результат = результати[-1] if результати else (None, {})
        помилка = результат.get('error') or ''
        квота = bool(re.search(r'quota|429|RESOURCE_EXHAUSTED', помилка, re.I))
        старт = [(н, т) for н, т in enumerate(рядки, 1) if f" -> {р['ід']} " in т and re.search(r'\[\d+\] наряд ', т)]
        if len(старт) != 1:
            raise ValueError(f"{р['ід']}: початків worker у wrapper.log — {len(старт)}")
        н, т = старт[0]
        pid = re.search(r'\[(\d+)\] наряд', т)[1]
        межа = next((к for к in range(н, len(рядки)) if f'[{pid}] наряд gemini-queue/' in рядки[к]), len(рядки))
        кінець = [(к + 1, рядки[к]) for к in range(н, межа)
                  if f'[{pid}]' in рядки[к] and ('квота: ' + робітник['name'] in рядки[к] or f'[{р["ід"]}]:' in рядки[к])]
        номер_pr = re.match(r'(?:автоперевірка|перевірка)-(\d+)', робітник['slug'])
        голова = голови(події, номер_pr[1] if номер_pr else None)
        усі_sha = sorted({г['sha'] for г in голова})
        свідчення.append({
            'ід': р['ід'], 'гілка': р['гілка'], 'початок_UTC': р['початок_UTC'],
            'код_таблиці': р['код'], 'токенів': int(р['разом_вікна']),
            'є_стан_первісного_id': (арг.стани / (р['ід'] + '.json')).exists(),
            'позначка': робітник['name'], 'sha_позначки': робітник['sha'],
            'рушій': робітник['sel']['engine'], 'модель': робітник['sel']['model'],
            'промпт_символів': len(промпт), 'промпт_байтів': файли['prompt.md'].stat().st_size,
            'вхідні_токени_всього': int(р['вхід_вікна']),
            'статус_моделі': результат.get('status'), 'відмова_квоти': квота,
            'рядок_result': номер, 'тривалість_результатів_сек': round(sum(п.get('duration_seconds', 0) for _, п in результати), 3),
            'кінцевий_рядок_моделі': (результат.get('response') or '').splitlines()[-1:] if квота else [],
            'голови_PR': усі_sha, 'докази_голів': голова,
            'рядки_обгортки': [{'номер': к, 'текст': рд} for к, рд in [старт[0], *кінець]],
            'sha256': {імя: відбиток(шлях) for імя, шлях in файли.items() if шлях.exists()},
        })
    попередні = {}
    повтори = []
    for р in свідчення:
        стара = попередні.get(р['гілка'])
        попередні[р['гілка']] = р
        if not стара or стара['код_таблиці'] != 'НЕМАЄ_КОДУ':
            continue
        та_сама = р['позначка'] == стара['позначка'] and р['sha_позначки'] == стара['sha_позначки']
        від = стара['голови_PR']
        до = р['голови_PR']
        голова = ('та сама' if від == до else 'інша') if len(від) == len(до) == 1 else 'невідомо'
        рядки_квоти = [д for д in стара['рядки_обгортки'] if 'квота: ' in д['текст']]
        повтори.append({
            'попередній': стара['ід'], 'наступний': р['ід'], 'гілка': р['гілка'],
            'та_сама_позначка_і_sha': та_сама, 'та_сама_модель': р['модель'] == стара['модель'],
            'хто_поставив': 'обгортка: Enter-RunQuotaWait → Set-MarkerWait → Start-Markers' if стара['відмова_квоти'] and рядки_квоти and та_сама else 'невідомо',
            'голова_PR': голова, 'sha_до': від, 'sha_після': до,
            'токенів_наступного': р['токенів'], 'доказ_повтору': рядки_квоти,
        })
    без_коду = [р for р in свідчення if р['код_таблиці'] == 'НЕМАЄ_КОДУ']
    підсумок = {
        'вікно_UTC': '[2026-10-29T00:00:00Z, 2026-11-05T00:00:00Z)',
        'рядків_agy': len(зріз), 'підготовок_без_сесії': len(зріз) - len(сесії),
        'сесій': len(сесії), 'НЕМАЄ_КОДУ': len(без_коду),
        'НЕМАЄ_КОДУ_з_квотою': sum(р['відмова_квоти'] for р in без_коду),
        'НЕМАЄ_КОДУ_з_журналом_WAIT_квоти': sum(any('квота: ' in д['текст'] for д in р['рядки_обгортки']) for р in без_коду),
        'НЕМАЄ_КОДУ_без_стану_первісного_id': sum(not р['є_стан_первісного_id'] for р in без_коду),
        'повторів': len(повтори), 'нарядів_з_повторами': len({р['гілка'] for р in повтори}),
        'токенів_повторів': sum(р['токенів_наступного'] for р in повтори),
        'постановники_повторів': dict(Counter(р['хто_поставив'] for р in повтори)),
        'голови_повторів': dict(Counter(р['голова_PR'] for р in повтори)),
        'токенів_повторів_за_головою': {к: sum(р['токенів_наступного'] for р in повтори if р['голова_PR'] == к)
                                      for к in sorted({р['голова_PR'] for р in повтори})},
        'моделі_НЕМАЄ_КОДУ': dict(Counter(р['модель'] for р in без_коду)),
        'промпт_символів_мін_макс': [min(р['промпт_символів'] for р in без_коду), max(р['промпт_символів'] for р in без_коду)],
        'тривалість_сек_мін_макс': [min(р['тривалість_результатів_сек'] for р in без_коду), max(р['тривалість_результатів_сек'] for р in без_коду)],
        'порожній_кінцевий_рядок': sum(not р['кінцевий_рядок_моделі'] for р in без_коду),
        'токенів_повторів_після_НЕМАЄ_КОДУ_без_відмови_квоти': sum(
            р['токенів_наступного'] for р in повтори
            if not next(с['відмова_квоти'] for с in без_коду if с['ід'] == р['попередній'])),
        'запуски_csv_sha256': відбиток(арг.джерело),
        'wrapper_log_sha256': hashlib.sha256(журнал_байти).hexdigest(),
        'wrapper_log_байтів': len(журнал_байти),
        'wrapper_log_рядків': len(рядки),
    }
    for імя, дані in [('сесії.json', свідчення), ('повтори.json', повтори), ('підсумок.json', підсумок)]:
        (арг.вихід / імя).write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(підсумок, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    виконати()

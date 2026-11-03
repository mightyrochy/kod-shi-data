#!/usr/bin/env python3
"""Stop повертає неприв'язану обіцянку й збій без кроку; помилка лишає хід як є."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

ОБІЦЯНКА = re.compile(r"\b(?:перевіряю|перевірю|з[’ʼ']ясовую|з[’ʼ']ясую|шукаю|знайду|зроблю|подивлюсь|подивлюся|чекаю|очікую|досліджую|досліджу|розберусь|розберуся)\b", re.I)
ПРИВЯЗКА = re.compile(r"\b(?:\d{1,2}:\d{2}|завтра|сьогодні)\b|\b(?:після\s+злиття\s+#\d+|коли\s+прийде\s+[^,.!?…]+|на\s+наступному\s+листі)\b", re.I)
НАГАДУВАННЯ = "Зроби дію в цьому ході або напиши «ЗАБЛОКОВАНО: <що, чекаю чого від кого>»."
ЗБІЙ = re.compile(r'ЗАБЛОКОВАНО|\bBLOCKED_\w+|\bQUOTA0_\w+|ДОРОБИТИ|\bLIVE_AFTER_INVALID\w*|СПОСТЕРІГАЧ\s+CI\b.*\bfailure\b')
ВІДЕОКАРТА = r'\b(?:GPU|відеокарт\w*)\b'
ГІЛКА = re.compile(r'\b(?:claude|codex|gemini)/[\w./-]+')
НОМЕР_ЗАПИТУ = re.compile(r'#(\d+)\b|\bPR\s+(\d+)\b|/pulls?/(\d+)\b', re.I)


def збої(вміст):
    """Виділяє предмет і причину кожного рядка збою у вході ходу."""
    for рядок in вміст.splitlines():
        збіг = ЗБІЙ.search(рядок)
        if not збіг:
            continue
        причина = ' '.join(рядок[збіг.start():].split()).casefold()
        квота = re.search(r'QUOTA0_(\w+)', рядок)
        гілки = [г.rstrip('.') for г in ГІЛКА.findall(рядок)]
        номери = [next(н for н in м.groups() if н) for м in НОМЕР_ЗАПИТУ.finditer(рядок)]
        if квота:
            назва = re.escape(квота[1]).replace('_', r'[\s_-]+')
            ознаки = [rf'\b(?:QUOTA0_)?{re.escape(квота[1])}\b', rf'\b{назва}\b']
            if квота[1] == 'GEMINIMODELS':
                ознаки.append(r'\bквот\w*\s+Gemini(?:[\s_-]+Models)?\b')
            предмети = [(f'квота {квота[1]}', ознаки)]
        elif re.search(ВІДЕОКАРТА, рядок, re.I):
            предмети = [('GPU', [ВІДЕОКАРТА])]
        elif гілки:
            предмети = [(г, [rf'(?<![\w/]){re.escape(г)}(?![\w/-])']) for г in гілки]
        elif номери:
            предмети = [(f'PR #{н}', [rf'#{н}\b|/pulls?/{н}\b|\bPR\s+{н}\b|'
                                      rf'\bgh\s+pr\s+\w+\s+{н}\b|'
                                      rf'"(?:pull_number|pr_number|pullNumber|number)"\s*:\s*"?{н}\b']) for н in номери]
            голова = re.search(r'\b[0-9a-f]{40}\b', рядок, re.I)
            if голова:
                for _, ознаки in предмети:
                    ознаки.append(rf'\b{голова[0]}\b')
        else:
            назва = збіг[0]
            if назва in ('ЗАБЛОКОВАНО', 'ДОРОБИТИ'):
                хвіст = re.search(r'[\w-]+', рядок[збіг.end():])
                назва = хвіст[0] if хвіст else назва
            предмети = [(назва, [rf'(?<!\w){re.escape(назва)}(?!\w)'])]
        for предмет, ознаки in предмети:
            yield {'предмет': предмет, 'причина': причина, 'ознаки': ознаки}


def посилання(дані, контекст=''):
    """Читає ідентифікатори jobs/runs із аргументів, JSON-відповідей і URL GitHub."""
    знайдені = set()
    if isinstance(дані, dict):
        for ключ, значення in дані.items():
            вид = {'job_id': 'job', 'jobId': 'job', 'check_run_id': 'job',
                   'run_id': 'run', 'runId': 'run'}.get(ключ)
            if ключ == 'id':
                вид = {'jobs': 'job', 'check_runs': 'job', 'workflow_runs': 'run'}.get(контекст)
            if вид and str(значення).isdigit():
                знайдені.add(f'{вид}:{значення}')
            знайдені.update(посилання(значення, ключ))
    elif isinstance(дані, list):
        for значення in дані:
            знайдені.update(посилання(значення, контекст))
    elif isinstance(дані, str):
        for вид, вираз in [('job', r'/jobs/(\d+)\b|/job/(\d+)\b'), ('run', r'/actions/runs/(\d+)\b')]:
            for збіг in re.finditer(вираз, дані):
                знайдені.add(f'{вид}:' + next(ч for ч in збіг.groups() if ч))
        try:
            розібрано = json.loads(дані)
        except ValueError:
            розібрано = None
        if isinstance(розібрано, (dict, list)):
            знайдені.update(посилання(розібрано))
    return знайдені


def називає(збій, аргументи, звязки):
    """Зіставляє дію з предметом, у тому числі з доведеним job/run його PR."""
    рядок = json.dumps(аргументи, ensure_ascii=False) if not isinstance(аргументи, str) else аргументи
    контексти = [рядок]
    for п in посилання(аргументи):
        контексти.extend(звязки.get(п, set()))
    return any(re.search(ознака, к, re.I) for ознака in збій['ознаки'] for к in контексти)


def ходи(шлях):
    """Читає хід до end_turn, зберігаючи вже опрацьовані пари предмет/причина.

    Tool-result не є входом збою: він лише пов'язує job/run з PR перевіреного запиту.
    Дія до надходження збою не вважається відповіддю на нього.
    """
    поточні, виклики, звязки = {}, {}, {}
    виконані = set()
    незавершений = False
    with open(шлях, encoding='utf-8') as файл:
        for рядок in файл:
            запис = json.loads(рядок)
            тип = запис.get('type')
            вміст = запис.get('message', {}).get('content', [])
            блоки = вміст if isinstance(вміст, list) else []
            if тип == 'user':
                незавершений = True
                for збій in збої(текст(запис)):
                    ключ = (збій['предмет'], збій['причина'])
                    поточні[ключ] = збій
                for блок in блоки:
                    if not isinstance(блок, dict) or блок.get('type') != 'tool_result':
                        continue
                    запит = виклики.get(блок.get('tool_use_id'), {})
                    контексти = {json.dumps(запит, ensure_ascii=False)}
                    for п in посилання(запит):
                        контексти.update(звязки.get(п, set()))
                    for п in посилання(блок.get('content', '')):
                        звязки.setdefault(п, set()).update(контексти)
            elif тип == 'assistant':
                незавершений = True
                дії = []
                for блок in блоки:
                    if isinstance(блок, dict) and блок.get('type') == 'tool_use':
                        аргументи = блок.get('input', {})
                        виклики[блок.get('id')] = аргументи
                        дії.append(аргументи)
                дії.extend(р for р in текст(запис).splitlines()
                           if re.match(r'^\s*ЗАБЛОКОВАНО:', р) and re.search(r'чекаю\s+.+\s+від\s+\S', р, re.I))
                for ключ, збій in поточні.items():
                    if any(називає(збій, дія, звязки) for дія in дії):
                        виконані.add(ключ)
                if запис.get('message', {}).get('stop_reason') == 'end_turn':
                    yield {'текст': текст(запис), 'збої': list(поточні.values()),
                           'без_кроку': [з for к, з in поточні.items() if к not in виконані], 'завершено': True}
                    поточні = {}
                    незавершений = False
    if незавершений:
        yield {'завершено': False}


def текст(запис):
    вміст = запис.get('message', {}).get('content', '')
    if isinstance(вміст, str):
        return вміст
    return '\n'.join(б.get('text', '') for б in вміст if isinstance(б, dict) and б.get('type') == 'text')


def останній_хід(шлях):
    """Повертає останній хід разом із причинами його повернення."""
    останній = {'завершено': False}
    for останній in ходи(шлях):
        pass
    return останній


def повернути(t):
    t = t.strip()
    if t.endswith('—'):
        t = t[:-1].rstrip()
    if re.search(r'(?:^|\n)\s*ЗАБЛОКОВАНО:', t):
        return False
    t = re.sub(r'«[^»]*»|"[^"\n]*"', '', t)
    речення = re.split(r'[.!?…]+(?:\s+|$)|\n+', t.strip())
    останнє = next((р.strip() for р in reversed(речення) if р.strip()), '')
    return bool(ОБІЦЯНКА.search(останнє) and not ПРИВЯЗКА.search(останнє))


def вимір(тека):
    кінці = тире = блокери = повернень = 0
    for шлях in Path(тека).rglob('*.jsonl'):
        with шлях.open(encoding='utf-8') as файл:
            for рядок in файл:
                запис = json.loads(рядок)
                if запис.get('type') != 'assistant' or запис.get('message', {}).get('stop_reason') != 'end_turn':
                    continue
                t = текст(запис).strip()
                кінці += 1
                тире += t.endswith('—')
                блокери += bool(re.search(r'(?:^|\n)\s*ЗАБЛОКОВАНО:', t))
                повернень += повернути(t)
    print(f'кінці: {кінці}; —: {тире}; ЗАБЛОКОВАНО: {блокери}; повернув би хук: {повернень}')


def main():
    if len(sys.argv) > 1:
        вимір(sys.argv[1])
        return
    дані = json.load(sys.stdin)
    if дані.get('stop_hook_active') or 'agent_id' in дані:
        return
    хід = останній_хід(дані['transcript_path'])
    if not хід['завершено']:
        return
    предмети = sorted({з['предмет'] for з in хід['без_кроку']})
    if предмети or повернути(хід['текст']):
        причина = ('Без кроку на збій: ' + ', '.join(предмети) + '. ') if предмети else ''
        print(json.dumps({'decision': 'block', 'reason': причина + НАГАДУВАННЯ}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as п:
        print(f'хук обіцянка_без_дії: {type(п).__name__}: {п}; хід як є', file=sys.stderr)

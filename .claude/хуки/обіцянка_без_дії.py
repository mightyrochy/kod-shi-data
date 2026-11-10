#!/usr/bin/env python3
"""Stop повертає неприв'язану обіцянку, збій без кроку й рядки в чаті ходу не власника; помилка лишає хід як є.

К1 — текст у чаті ходу, який почав не власник (лист сесії, сповіщення, пульс, результат фонового завдання). Хто почав
хід, видно в транскрипті: запис `user` власника має `origin.kind == "human"`, лист і сповіщення — `task-notification`
чи службовий запис (`isMeta`, `<cross-session-message`); рядок з міткою відправника великими літерами — лист
(`слова_власника.МІТКА_ЛИСТА`). Запис без `origin` з простим текстом вважаємо словом власника: хибне повернення
відповіді власникові дорожче за пропуск. Слово власника посеред ходу (`queued_command` чи запис `user`) відкриває
відповідь йому — текст після нього не рахуємо. Перевіряється весь текст ходу, не лише останній: рядки «що роблю»
посеред ходу на нагадування платформи («The user hasn't heard from you…») і були порушенням. Дозволено «—» і
«ЗАБЛОКОВАНО: …»; повернення — раз (`stop_hook_active`), з дослівним правилом ядра «Текст у чаті».
"""
import json
import re
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from слова_власника import МІТКА_ЛИСТА  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

ОБІЦЯНКА = re.compile(r"\b(?:перевіряю|перевірю|з[’ʼ']ясовую|з[’ʼ']ясую|шукаю|знайду|зроблю|подивлюсь|подивлюся|чекаю|очікую|досліджую|досліджу|розберусь|розберуся)\b", re.I)
ПРИВЯЗКА = re.compile(r"\b(?:\d{1,2}:\d{2}|завтра|сьогодні)\b|\b(?:після\s+злиття\s+#\d+|коли\s+прийде\s+[^,.!?…]+|на\s+наступному\s+листі)\b", re.I)
НАГАДУВАННЯ = "Зроби дію в цьому ході або напиши «ЗАБЛОКОВАНО: <що, чекаю чого від кого>»."
ПРАВИЛО_ЧАТУ = (
    "`AGENTS.md`, «Для всіх»: «Текст у чаті читає власник: без відповіді на його слово чи потрібного від нього нема "
    "рядків про хід — ні посеред, ні наприкінці, — і хід кінчається «—», а у відповіді нема переліку «що змінюю» "
    "(«просто дурне ходіння по колу»)».")
ПРАВИЛО_НАГАДУВАННЯ = (
    " `CLAUDE.md`, «Контекст і пам'ять»: «Нагадування CLI «The user hasn't heard from you…» приходить у ходах, які почав "
    "не власник: рядка в чат на нього не пишеш (ядро, «Текст у чаті»)».")
ВІДЕОКАРТА = r'\b(?:GPU|відеокарт\w*)\b'
ГІЛКА = r'(?:claude|codex|gemini)/[\w./-]+'
ПОЛЕ_ЗБОЮ = re.compile(
    r'(?P<квота>QUOTA0_(?P<група>[A-Z0-9]{1,16})(?:_M[0-9]{1,6})?)'
    rf'|(?P<гілка>{ГІЛКА})'
    r'|(?:#|PR\s+#?)(?P<запит>[1-9][0-9]*)'
    r'|(?:рядок(?:\s+дошки)?|дошка|№)\s*(?P<дошка>[1-9][0-9]*)'
    r'|позначка\s+(?P<позначка>[\w.-]+/[\w./-]+)'
    r'|(?P<позначка_черги>gemini-queue/[\w./-]+)'
    r'|(?P<ресурс>(?i:GPU|SLOTS|відеокарт\w*))'
    r'|(?P<код>BLOCKED_[A-Z0-9_]+|LIVE_AFTER_INVALID[A-Z0-9_]*)')


def поля_збою(рядок):
    """Читає тільки початкові поля повідомлення, відділені від його пояснення."""
    рядок = рядок.strip()
    спостерігач = re.fullmatch(r'СПОСТЕРІГАЧ\s+CI\s+(#[1-9][0-9]*)\s+([0-9a-f]{40})\s+failure', рядок)
    if спостерігач:
        return [ПОЛЕ_ЗБОЮ.fullmatch(спостерігач[1])], спостерігач[2]
    рядок = re.sub(r'^(?:GEMINI ОБГОРТКА:\s*|НОУТБУК\s+)', '', рядок)
    заголовок = re.match(r'^(?:ЗАБЛОКОВАНО|ДОРОБИТИ)(?=\s|:|$):?\s*', рядок)
    if заголовок:
        рядок = рядок[заголовок.end():]
    elif not re.match(r'^(?:BLOCKED_|QUOTA0_|LIVE_AFTER_INVALID)', рядок):
        return [], ''
    зведення = re.fullmatch(rf'([A-Z0-9_]{{2,40}}) ×[0-9]{{1,5}}: '
                            rf'({ГІЛКА}(?:, {ГІЛКА}){{0,4}})(?: …)?', рядок)
    if зведення:
        рядок = зведення[2] + ' ' + зведення[1]
    поля = []
    while рядок:
        поле = ПОЛЕ_ЗБОЮ.match(рядок)
        if not поле or re.match(r'[\w/-]', рядок[поле.end():]):
            break
        поля.append(поле)
        рядок = рядок[поле.end():]
        роздільник = re.match(r'(?:,\s*|\s+)', рядок)
        if not роздільник:
            break
        рядок = рядок[роздільник.end():]
    return поля, ''


def збої(вміст):
    """Виділяє предмет із поля формату; пояснення зберігає тільки як причину."""
    for рядок in вміст.splitlines():
        поля, голова = поля_збою(рядок)
        if not поля:
            continue
        причина = ' '.join(рядок.split()).casefold()
        квота = next((п['група'] for п in поля if п['група']), None)
        if квота:
            назва = re.escape(квота)
            ознаки = [rf'\bQUOTA0_{назва}(?:_M[0-9]{{1,6}})?\b', rf'\b{назва}\b']
            if квота == 'GEMINIMODELS':
                ознаки.append(r'\bквот\w*\s+Gemini(?:[\s_-]+Models)?\b')
            предмети = [(f'квота {квота}', ознаки)]
        else:
            предмети = []
            for поле in поля:
                if поле['ресурс']:
                    назва = 'SLOTS' if поле['ресурс'].upper() == 'SLOTS' else 'GPU'
                    предмети.append((назва, [r'\bSLOTS\b' if назва == 'SLOTS' else ВІДЕОКАРТА]))
                elif поле['гілка'] or поле['позначка'] or поле['позначка_черги']:
                    назва = (поле['гілка'] or поле['позначка'] or поле['позначка_черги']).rstrip('.')
                    предмети.append((назва, [rf'(?<![\w/]){re.escape(назва)}(?![\w/-])']))
                elif поле['запит']:
                    н = поле['запит']
                    ознаки = [rf'#{н}\b|/pulls?/{н}\b|\bPR\s+#?{н}\b|'
                              rf'\bgh\s+pr\s+\w+\s+{н}\b|'
                              rf'"(?:pull_number|pr_number|pullNumber|number)"\s*:\s*"?{н}\b']
                    if голова:
                        ознаки.append(rf'\b{голова}\b')
                    предмети.append((f'PR #{н}', ознаки))
                elif поле['дошка']:
                    н = поле['дошка']
                    предмети.append((f'рядок {н}', [rf'\b(?:рядок(?:\s+дошки)?|дошка)\s+{н}\b|'
                                                    rf'№\s*{н}\b|\|\s*{н}\s*\|']))
            if not предмети:
                предмети = [(п['код'], [rf'\b{re.escape(п["код"])}\b']) for п in поля if п['код']]
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


def власник(запис):
    """True — слово власника, False — лист, сповіщення чи службовий запис, None — не початок і не слово (результат
    інструмента, вкладення іншого виду)."""
    тип = запис.get('type')
    if тип == 'attachment':
        вкладення = запис.get('attachment') or {}
        if вкладення.get('type') != 'queued_command':
            return None
        вміст, джерело, службовий = вкладення.get('prompt'), вкладення.get('origin'), False
    elif тип == 'user':
        вміст = запис.get('message', {}).get('content', '')
        if isinstance(вміст, list) and any(isinstance(б, dict) and б.get('type') == 'tool_result' for б in вміст):
            return None
        джерело, службовий = запис.get('origin'), запис.get('isMeta') or запис.get('isCompactSummary')
    else:
        return None
    т = текст({'message': {'content': вміст}}).strip()
    if службовий or not т or МІТКА_ЛИСТА.match(т):
        return False
    вид = (джерело or {}).get('kind')
    if вид:
        return вид == 'human'
    return not т.startswith('<')


def рядки_не_власникові(шлях):
    """Останній завершений хід: (що його почало, [тексти асистента без відповіді власникові], чи було нагадування CLI).
    Хід без кінця (`end_turn`) чи хід власника — None."""
    результат, хід, перенесено = None, None, False
    with open(шлях, encoding='utf-8') as файл:
        for рядок in файл:
            try:
                запис = json.loads(рядок)
            except ValueError:
                continue
            if запис.get('isSidechain'):
                continue
            тип = запис.get('type')
            if хід is None:
                # слово власника посеред попереднього ходу могло лишитись без відповіді: відповідь у цьому ході — йому
                хід = {'початок': None, 'власник': перенесено, 'посеред': False, 'тексти': [],
                       'нагадування': False, 'відповідь': False}
            вкладення = запис.get('attachment') or {}
            if тип == 'attachment' and вкладення.get('type') == 'silent_turn_reminder':
                хід['нагадування'] = True
            чий = власник(запис)
            if чий is not None:
                # хід почав останній запис перед першою відповіддю: локальна команда (`/effort`) відповіді не має
                if хід['початок'] is None or not хід['відповідь']:
                    вміст = текст({'message': {'content': вкладення.get('prompt') if тип == 'attachment'
                                              else запис.get('message', {}).get('content', '')}})
                    хід['початок'] = ' '.join(вміст.split())[:60] or '(без тексту)'
                elif чий:
                    хід['посеред'] = True
                хід['власник'] = хід['власник'] or чий
            if тип == 'assistant':
                хід['відповідь'] = True
            if тип == 'assistant' and хід['початок'] is not None and not хід['власник']:
                т = текст(запис).strip()
                if т and т != '—' and not re.match(r'^ЗАБЛОКОВАНО:', т):
                    хід['тексти'].append(т)
            if тип == 'assistant' and запис.get('message', {}).get('stop_reason') == 'end_turn':
                результат = None if (хід['власник'] or хід['початок'] is None) else хід
                перенесено, хід = хід['посеред'], None
    if хід is not None or результат is None or not результат['тексти']:
        return None
    return результат


def причина_к1(хід):
    рядки = '; '.join(f"«{' '.join(т.split())[:80]}{'…' if len(' '.join(т.split())) > 80 else ''}»"
                      for т in хід['тексти'][:3])
    return (f"Хід почав не власник («{хід['початок']}»), а в чаті є рядки: {рядки}. " + ПРАВИЛО_ЧАТУ
            + (ПРАВИЛО_НАГАДУВАННЯ if хід['нагадування'] else '')
            + " Сказаного не повторюй і не підсумовуй; закінчи хід «—», потрібне від власника — «ЗАБЛОКОВАНО: <що, чекаю "
              "чого від кого>».")


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
    причини = []
    предмети = sorted({з['предмет'] for з in хід['без_кроку']})
    if предмети or повернути(хід['текст']):
        причина = ('Без кроку на збій: ' + ', '.join(предмети) + '. ') if предмети else ''
        причини.append(причина + НАГАДУВАННЯ)
    try:
        к1 = рядки_не_власникові(дані['transcript_path'])
    except (OSError, ValueError) as п:
        print(f'хук обіцянка_без_дії: К1 не прочитав транскрипт ({п}); хід як є', file=sys.stderr)
        к1 = None
    if к1:
        причини.append(причина_к1(к1))
    if причини:
        print(json.dumps({'decision': 'block', 'reason': ' '.join(причини)}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as п:
        print(f'хук обіцянка_без_дії: {type(п).__name__}: {п}; хід як є', file=sys.stderr)

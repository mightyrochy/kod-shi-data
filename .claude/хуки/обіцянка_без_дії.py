#!/usr/bin/env python3
"""Stop повертає неприв'язану обіцянку; помилка лишає хід як є."""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

ОБІЦЯНКА = re.compile(r"\b(?:перевіряю|перевірю|з[’ʼ']ясовую|з[’ʼ']ясую|шукаю|знайду|зроблю|подивлюсь|подивлюся|чекаю|очікую|досліджую|досліджу|розберусь|розберуся)\b", re.I)
ПРИВЯЗКА = re.compile(r"\b(?:після|коли|щойно|до|на такті|завтра|сьогодні|о|об|через)\b|\b\d{1,2}:\d{2}\b", re.I)
НАГАДУВАННЯ = "Зроби дію в цьому ході або напиши «ЗАБЛОКОВАНО: <що, чекаю чого від кого>»."


def текст(запис):
    вміст = запис.get('message', {}).get('content', '')
    if isinstance(вміст, str):
        return вміст
    return '\n'.join(б.get('text', '') for б in вміст if isinstance(б, dict) and б.get('type') == 'text')


def останній_текст(шлях):
    останній = ''
    with open(шлях, encoding='utf-8') as файл:
        for рядок in файл:
            запис = json.loads(рядок)
            if запис.get('type') == 'assistant':
                t = текст(запис)
                if t:
                    останній = t
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
    if повернути(останній_текст(дані['transcript_path'])):
        print(json.dumps({'decision': 'block', 'reason': НАГАДУВАННЯ}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as п:
        print(f'хук обіцянка_без_дії: {type(п).__name__}: {п}; хід як є', file=sys.stderr)

#!/usr/bin/env python3
"""Проба Stop на штучних транскриптах."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

хук = Path(__file__).resolve().parents[2] / '.claude/хуки/обіцянка_без_дії.py'
випадки = [('Перевіряю, чому.\n—', True), ('Чекаю CI #2669 і #2670 до такту о 04:39 UTC.\n—', False),
           ('На такті 10:39 подивлюсь.\n—', False), ('Коли прийде нова голова, поставлю.\n—', False),
           ('Після злиття #123 перевірю.\n—', False), ('Написав «перевіряю» і закінчив хід.\n—', False),
           ('ЗАБЛОКОВАНО: перевірка, чекаю даних від диспетчера', False), ('Зараз зроблю.', True),
           ('Шукаю причину.', True), ('З’ясую.', True)]
with tempfile.TemporaryDirectory() as т:
    шлях = Path(т) / 'a.jsonl'
    for t, очікується in випадки:
        шлях.write_text(json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': t}]}}), encoding='utf-8')
        def запуск(дані):
            return subprocess.run([sys.executable, str(хук)], input=дані, text=True, encoding='utf-8', capture_output=True, check=True)
        дані = {'transcript_path': str(шлях)}
        р = запуск(json.dumps(дані))
        assert bool(р.stdout) == очікується, (t, р.stdout, р.stderr)
        assert not запуск(json.dumps({**дані, 'stop_hook_active': True})).stdout
        assert not запуск(json.dumps({**дані, 'agent_id': '1'})).stdout
    р = запуск('{')
    assert not р.stdout and р.stderr
    р = subprocess.run([sys.executable, str(хук), т], text=True, encoding='utf-8', capture_output=True, check=True)
    assert 'кінці: 0' in р.stdout
print(f'проба: {len(випадки)} випадків, захист від петлі, субагент, помилка і вимір — гаразд')

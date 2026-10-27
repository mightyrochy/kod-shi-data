#!/usr/bin/env python3
"""Підробні CLI стенда здоров'я; жодного мережевого звернення."""
import json
import os
import sys
import time
from pathlib import Path

role, *args = sys.argv[1:]
mode = os.environ.get('FAKE_HEALTH_MODE', '')
if role == 'git':
    if 'cat-file' in args:
        print('| диспетчер | session_TEST |')
elif role == 'gh':
    body = sys.stdin.read() if args[-1] == '-' else Path(args[-1]).read_text(encoding='utf-8-sig')
    with open(os.environ['FAKE_HEALTH_GH_LOG'], 'a', encoding='utf-8') as f:
        f.write(json.dumps({'args': args, 'body': json.loads(body)}, ensure_ascii=False) + '\n')
    if mode == 'both_fail':
        sys.exit(1)
    print(json.dumps({'id': 123}))
elif role == 'sleep':
    time.sleep(2)
elif role == 'agy':
    if mode == 'agy_auth':
        print('401 authentication required; текст, якого не має бути у тривозі', file=sys.stderr)
        sys.exit(1)
    if args == ['--version']:
        print('agy 1.4.7')
    elif args[:2] == ['-p', '/usage']:
        print(json.dumps({'response': 'довільна таблиця 0%', 'command': {'name': 'usage', 'data': {'groups': [
            {'name': 'Gemini Models', 'buckets': [
                {'window': 'weekly', 'remaining_fraction': 0.92, 'reset_time': '2026-11-02T22:01:25Z'},
                {'window': '5h', 'remaining_fraction': 1, 'reset_time': '2026-10-27T21:03:10Z'}]},
            {'name': 'Claude and GPT models', 'buckets': [
                {'window': 'weekly', 'remaining_fraction': 0.5, 'reset_time': '2026-11-03T13:01:24Z'},
                {'window': '5h', 'remaining_fraction': 0, 'reset_time': '2026-10-27T18:01:24Z'}]}
        ]}}}))
    elif args == ['models']:
        print('gemini-3.8-flash-high Gemini Flash')
elif role == 'claude':
    sys.stdin.read()
    if mode == '401':
        print('401 authentication_error', file=sys.stderr)
        sys.exit(1)
    print(json.dumps({'ok': 'true' if mode == 'string' else mode not in ('fail', 'both_fail'), 'response': '401 текст агента' if mode == 'ok401' else ''}))

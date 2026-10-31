#!/usr/bin/env python3
"""Підробний CLI LM Studio (`lms`) для стенда вивантаження моделей; жодного мережевого звернення.

Стан — JSON-перелік завантажених моделей у FAKE_LMS_STATE (нема файла — моделей нема), кожен виклик — рядок JSON
аргументів у FAKE_LMS_LOG. FAKE_LMS_NOJSON=1 — старіший CLI без `ps --json` (текстовий вивід).
"""
import json
import os
import sys

args = sys.argv[1:]
state = os.environ['FAKE_LMS_STATE']
log = os.environ.get('FAKE_LMS_LOG')
if log:
    with open(log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(args) + '\n')
try:
    with open(state, encoding='utf-8') as f:
        models = json.load(f)
except FileNotFoundError:
    models = []

if args == ['ps', '--json']:
    if os.environ.get('FAKE_LMS_NOJSON'):
        print("error: unknown option '--json'", file=sys.stderr)
        sys.exit(1)
    print(json.dumps([{'type': 'llm', 'modelKey': m, 'identifier': m, 'path': m + '.gguf'} for m in models]))
elif args == ['ps']:
    if not models:
        print('No models are currently loaded')
    else:
        print('\nLOADED MODELS\n')
        for m in models:
            print(f'Identifier: {m}\n  - Type:  LLM\n  - Path: {m}.gguf')
elif args == ['unload', '--all']:
    with open(state, 'w', encoding='utf-8') as f:
        json.dump([], f)
    print('Unloaded all models' if models else 'No models to unload')
else:
    print('error: unknown command ' + ' '.join(args), file=sys.stderr)
    sys.exit(2)

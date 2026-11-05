"""Читає фактичні входи моделі, не оцінює якість образів."""
import json
import sys
from pathlib import Path

тека = Path(__file__).parent / sys.argv[1]
for файл in sorted((тека / 'VIDPOVIDI/обмін').glob('*.json')):
    обмін = json.loads(файл.read_text(encoding='utf-8'))
    запит = обмін['запит']
    for повідомлення in запит.get('messages', []):
        for частина in повідомлення.get('content', []):
            if частина.get('type') != 'text':
                continue
            try:
                промпт = json.loads(частина['text'])
            except (ValueError, TypeError):
                continue
            if not isinstance(промпт, dict):
                continue
            дані = промпт
            if 'conversation' in дані:
                print(файл.name, list(дані))
                print(json.dumps(дані, ensure_ascii=False)[:2500])

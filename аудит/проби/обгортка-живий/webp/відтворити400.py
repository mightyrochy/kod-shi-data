"""Ізольований виклик із кадром записаного складу; вивантажує лише свій екземпляр."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ТЕКА = Path(__file__).resolve().parent


def запит(шлях, тіло=None):
    р = urllib.request.Request('http://127.0.0.1:1234' + шлях,
        data=None if тіло is None else json.dumps(тіло).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(р, timeout=300) as в:
            return в.status, json.load(в)
    except urllib.error.HTTPError as в:
        return в.code, json.load(в)


def головна():
    до = запит('/api/v1/models')[1]
    assert not any(м['loaded_instances'] for м in до['models'])
    _, свій = запит('/api/v1/models/load', {'model': 'qwen/qwen3.5-9b',
        'context_length': 57344, 'parallel': 1, 'echo_load_config': True})
    ід = свій['instance_id']
    результати = []
    try:
        після = '--після' in sys.argv
        входи = [('кадр-ПІСЛЯ.jpg', 'image/jpeg')] if після else [('кадри-ДО/ж-12335-0.bin', 'image/jpeg'), ('кадри-ДО/ж-12335-0.bin', 'image/webp')]
        for ім, mime in входи:
            б = (ТЕКА / ім).read_bytes()
            url = 'data:' + mime + ';base64,' + base64.b64encode(б).decode()
            http, відповідь = запит('/v1/chat/completions', {'model': ід,
                'messages': [{'role': 'user', 'content': [
                    {'type': 'text', 'text': 'Describe the garment in one sentence.'},
                    {'type': 'image_url', 'image_url': {'url': url}}]}],
                'max_tokens': 80, 'reasoning_effort': 'none', 'temperature': 0, 'stream': False})
            результати.append({'файл': ім, 'mime': mime, 'байтів': len(б),
                'sha256': hashlib.sha256(б).hexdigest(), 'base64_зворотне': base64.b64decode(url.split(',')[1]) == б,
                'http': http, 'відповідь': відповідь})
            print(mime, http, flush=True)
    finally:
        прибирання = запит('/api/v1/models/unload', {'instance_id': ід})
        (ТЕКА / ('відтворення400-ПІСЛЯ.json' if '--після' in sys.argv else 'відтворення400.json')).write_text(json.dumps({'завантаження': свій,
            'виклики': результати, 'прибирання': прибирання}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    головна()

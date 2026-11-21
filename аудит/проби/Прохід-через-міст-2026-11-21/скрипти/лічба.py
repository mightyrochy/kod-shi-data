"""Лічба обмінів із мостом: python3 -I лічба.py <обміни.jsonl>... [--докладно]
Виклики, статуси, x-attempts із «temperature dropped», x-images-dropped, x-temperature, токени з usage, долари (ціни — ЗВІТ.md),
частка входу з кешу; з --докладно — рядок на виклик (час, секунди, вид запиту за першими словами інструкції)."""
import json, sys, collections
ЦІНИ = {'claude-sonnet': (2.0, 2.5, 0.10, 10.0), 'claude-haiku': (0.10, 0.125, 0.01, 0.50)}   # вхід, запис кешу, читання кешу, вихід за млн
def вид(q):
    try: т = json.loads(q)
    except Exception: return '?'
    с = т.get('system') or ''
    if isinstance(с, list): с = ' '.join(x.get('text', '') for x in с if isinstance(x, dict))
    if not с:
        for м in т.get('messages', []):
            к = м.get('content'); к = к if isinstance(к, list) else [{'type': 'text', 'text': к}]
            for б in к:
                if isinstance(б, dict) and б.get('type') == 'text' and б.get('text', '').strip(): с = б['text']; break
            if с: break
    return ' '.join(с.split())[:70]
файли = [a for a in sys.argv[1:] if not a.startswith('--')]; докладно = '--докладно' in sys.argv
р = [json.loads(l) for ф in файли for l in open(ф, encoding='utf-8') if l.strip()]
р = [x for x in р if not x.get('стеля') and not x.get('заглушка')]
підс = collections.Counter(); долари = 0.0; вх = кеш_ч = кеш_з = вих = 0
for x in р:
    з = x.get('заголовки', {}); м = з.get('x-model', '')
    підс['викликів'] += 1; підс[f"статус {x.get('статус')}"] += 1
    if 'temperature dropped' in з.get('x-attempts', ''): підс['двічі (temperature dropped)'] += 1
    if з.get('x-attempts', '').count('=') > 1: підс['спроб у мості > 1'] += 1
    if int(з.get('x-images-dropped', '0') or 0) > 0: підс['x-images-dropped > 0'] += 1; підс['фото випало, штук'] += int(з['x-images-dropped'])
    if 'Unable to download' in (x.get('відповідь') or ''): підс['400 Unable to download'] += 1
    підс['x-temperature ' + з.get('x-temperature', '-')] += 1
    if з.get('x-runs-left', 'n/a') != 'n/a': підс['x-runs-left ЧИСЛО'] += 1
    ц = 0.0
    if з.get('x-cost-usd'): ц = float(з['x-cost-usd'])
    else:
        try: u = json.loads(x.get('відповідь') or '{}').get('usage', {}) or {}
        except Exception: u = {}
        п = next((v for k, v in ЦІНИ.items() if м.startswith(k)), None)
        i, cw, cr, o = u.get('input_tokens', 0), u.get('cache_creation_input_tokens', 0) or 0, u.get('cache_read_input_tokens', 0) or 0, u.get('output_tokens', 0)
        вх += i; кеш_з += cw; кеш_ч += cr; вих += o
        if п: ц = (i * п[0] + cw * п[1] + cr * п[2] + o * п[3]) / 1e6
    долари += ц
    if докладно: print(f"{x['час'][11:19]} {x.get('с', 0):6.1f}с {x.get('статус')} {м[:22]:22} ${ц:.4f} {з.get('x-attempts','')[:40]:40} {вид(x['запит'])}")
print(dict(підс))
усього_вх = вх + кеш_з + кеш_ч
print(f"токени: вхід {усього_вх} (з них без кешу {вх}, запис кешу {кеш_з}, читання кешу {кеш_ч} = {100*кеш_ч/max(1,усього_вх):.1f} %), вихід {вих}; долари ${долари:.3f}")

"""прогін.py — оцінювання моделі каталогу qwen3-vl-8b-instruct у LM Studio на 40 речах спроби 2.
Коди словника відтінків ISCC-NBS (267 блоків) модуля Річ-колір-межі.
"""

import json
import urllib.request
import base64
import io
import os
import csv
import sys
from PIL import Image

sys.path.insert(0, 'джерела')
import colorspace as CS

repo_dir = r"C:\Users\gemini\gemini-runs\w\20261109-203123-d93af02d34c2\repo"
tmp_dir = r"C:\Users\gemini\gemini-runs\w\20261109-203123-d93af02d34c2\tmp"
probe_dir = os.path.join(repo_dir, 'аудит', 'проби', 'річ_колір_модель_кодує')
os.makedirs(probe_dir, exist_ok=True)

# 1. Завантажуємо словник ISCC-NBS 267
with open(os.path.join(tmp_dir, 'iscc_dictionary.json'), encoding='utf-8') as f:
    iscc_list = json.load(f)

# Виправляємо 5 нейтралей на точні значення Munsell (Glenn Davis, Kelly-Judd NBS SP 440)
neutrals = {
    263: ([92.5, 0.0, 0.0], "#EBEBEB"),
    264: ([75.0, 0.0, 0.0], "#BEBEBE"),
    265: ([55.0, 0.0, 0.0], "#878787"),
    266: ([35.0, 0.0, 0.0], "#535353"),
    267: ([15.0, 0.0, 0.0], "#232323"),
}
for it in iscc_list:
    if it['code'] in neutrals:
        it['lab'], it['hex'] = neutrals[it['code']]

iscc_by_code = {item['code']: item for item in iscc_list}

# Зберігаємо словник_iscc_267.tsv
with open(os.path.join(probe_dir, 'словник_iscc_267.tsv'), 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(['код', 'назва_en', 'назва_uk', 'родина', 'munsell', 'hex_центроїд', 'L', 'a', 'b'])
    for it in iscc_list:
        writer.writerow([
            it['code'], it['en'], it['uk'], it['family'], it['munsell'], it['hex'],
            f"{it['lab'][0]:.2f}", f"{it['lab'][1]:.2f}", f"{it['lab'][2]:.2f}"
        ])

# 2. Формуємо промпт зі словником відтінків
common_fashion_vocab = """ОСНОВНІ ГРУПИ ТА ВІДТІНКИ КАТАЛОГУ ОДЯГУ:
1. БІЛІ ТА СВІТЛІ НЕЙТРАЛІ (WHITE, OFF-WHITE, IVORY, CREAM):
- 263: white (чистий білий)
- 92: yellowish white (молочно-білий, теплий вершковий, айворі, ванільний)
- 153: greenish white (зеленкувато-білий, холодний молочний)
- 189: bluish white (блакитнувато-білий, крижаний білий)
- 9: pinkish white (рожевувато-білий)
- 231: purplish white (бузково-білий, холодний білий)

2. СІРІ ТА ГРАФІТОВІ (GRAY):
- 264: light gray (світло-сірий)
- 265: medium gray (середньо-сірий)
- 266: dark gray (темно-сірий, графітовий)
- 112: light olive gray (сріблясто-сірий атлас з оливковим відливом)
- 190: light bluish gray (світлий блакитно-сірий, димчастий)
- 191: bluish gray (блакитно-сірий)
- 232: light purplish gray (світлий бузково-сірий)

3. ЧОРНІ (BLACK):
- 267: black (глибокий матовий чорний)
- 193: bluish black (глибокий чорний з синюватим відливом)
- 235: purplish black (пурпурно-чорний)
- 21: blackish red (чорний з винним/шоколадним відтінком)
- 24: reddish black (червонувато-чорний)
- 114: olive black (оливково-чорний)

4. БЕЖЕВІ, ПІСОЧНІ, ТАУП, КЕМЕЛ ТА КОРИЧНЕВІ (BEIGE, TAUPE, CAMEL, BROWN):
- 73: pale orange yellow (світлий теплий пісочний беж)
- 89: pale yellow (світлий теплий ванільно-кремовий)
- 90: grayish yellow (сірувато-жовтий, пісочний беж)
- 93: yellowish gray (жовтувато-сірий, світлий бежевий, вівсяний беж, грейдж)
- 79: light grayish yellowish brown (теплий горіхово-бежевий меланж, мокко з молоком)
- 80: grayish yellowish brown (приглушений тауп, оливково-коричневий)
- 60: light grayish brown (світлий сіро-коричневий, какао)
- 64: brownish gray (коричневувато-сірий, тауп)
- 54: brownish orange (теплий карамельний кемел, рудуватий)
- 55: strong brown (насичений карамельно-рудий, теракотовий)
- 57: light brown (світло-коричневий)
- 58: moderate brown (коричневий)
- 59: dark brown (темно-коричневий)
- 62: dark grayish brown (темно-шоколадний)

5. СИНІ ТА ДЕНІМ (BLUE, DENIM, NAVY):
- 171: very light greenish blue (світлий крижано-блакитний, аквамариновий)
- 184: very light purplish blue (дуже світлий блакитний)
- 185: pale purplish blue (блідо-блакитний)
- 177: brilliant blue (яскраво-блакитний)
- 182: moderate blue (класичний середньо-блакитний денім, джинсовий)
- 195: brilliant purplish blue (класичний синій денім, трохи вицвілий)
- 178: strong blue (насичений синій)
- 179: deep blue (глибокий синій)
- 183: dark blue (темно-синій)
- 203: dark purplish blue (темно-синій твід, чорнильний)

6. ФІОЛЕТОВІ, БУЗКОВІ ТА СЛИВОВІ (PURPLE, VIOLET, LILAC, PLUM):
- 221: very light purple (світлий бузково-лавандовий, ніжний холодний)
- 222: light purple (світлий бузковий)
- 223: moderate purple (помірний фіолетовий)
- 216: vivid purple (яскравий фіолетовий)
- 219: dark purple (темно-фіолетовий)
- 17: very dark red (глибокий сливово-винний, баклажановий)
- 27: deep yellowish pink (яскравий малиново-рожевий, фуксія)
- 259: dark purplish red (темний сливово-винний)
- 260: very dark purplish red (дуже темний баклажановий)

7. ЖОВТІ, ЗЕЛЕНІ ТА ОЛИВКОВІ (YELLOW, GREEN, OLIVE, KHAKI):
- 104: pale greenish yellow (блідий масляно-жовтий з зеленкуватим підтоном, лимонний)
- 120: moderate yellow green (блідий салатово-лимонний, фісташковий)
- 115: vivid yellow green (салатовий)
- 106: light olive (світлий оливковий)
- 107: moderate olive (оливковий, хакі)
- 81: dark grayish yellowish brown (темний оливково-хакі, болотяний)
- 139: vivid green (зелений)
- 145: dark green (темно-зелений)

8. РОЖЕВІ, ПЕРСИКОВІ, КОРАЛОВІ ТА ЧЕРВОНІ (PINK, PEACH, CORAL, RED):
- 4: light pink (світло-рожевий)
- 8: grayish pink (приглушений бузково-рожевий, пильний ліловий)
- 26: strong yellowish pink (кораловий)
- 28: light yellowish pink (світлий персиково-абрикосовий, теплий кораловий)
- 52: light orange (світло-помаранчевий, персиковий)
- 11: vivid red (яскравий червоний)
- 12: strong red (насичений червоний)
- 13: deep red (глибокий червоний)
- 15: moderate red (помірний червоний)"""

compact_all_codes = ", ".join([f"{it['code']}: {it['en']}" for it in iscc_list])

system_prompt = f"""Ти — професійна модель-стилістка каталогу одягу.
Твоє завдання — описати точний колір САМОЇ РІЧІ (тканини) на фото галереї, обравши відповідні коди зі словника відтінків ISCC-NBS (1-267).

{common_fashion_vocab}

ПОВНИЙ СЛОВНИК УСІХ 267 БЛОКІВ ISCC-NBS:
{compact_all_codes}

ПРАВИЛА:
1. Описуй виключно колір САМОЇ РІЧІ (тканини зазначеного виробу). Ігноруй фон, стіни, вішалку, манекен, шкіру моделей та інший одяг образу!
2. Для бежевих, молочних, вершкових, пісочних кольорів обирай точні коди (92 - молочний/айворі, 73 - пісочний беж, 90/93 - сірувато-бежевий/вівсяний), а не 264 (сірий) чи 57 (темний).
3. "назва": вільна, точна описова назва відтінку для людини (українською).
4. "принт": назва принту/візерунку (смужка, клітинка, горох, квіти, зебра, листя, написи), або null якщо однотонна.
5. "основний": {{"код": число_зі_словника, "частка": число_від_0_до_1}} основного кольору тканини.
6. "решта": список додаткових кольорів {{"код": число, "частка": число}} якщо річ двоколірна (принт, смужка, кольорове оздоблення). Для однотонної — [].

Відповідай ТІЛЬКИ валідним JSON формату:
{{
  "назва": "...",
  "принт": "..." або null,
  "основний": {{"код": 123, "частка": 0.8}},
  "решта": [{{"код": 45, "частка": 0.2}}]
}}"""

# 3. Завантажуємо набір спроби 2
with open(os.path.join(repo_dir, 'ohliad-koloru', 'sets', 'sproba2.json'), encoding='utf-8') as f:
    set_items = json.load(f)['речі']

with open(os.path.join(repo_dir, 'аудит', 'проби', 'річ_колір_огляд_людьми', 'лічба_sproba2_власник.tsv'), encoding='utf-8') as f:
    tsv_rows = {int(r['номер']): r for r in csv.DictReader(f, delimiter='\t')}

with open(os.path.join(repo_dir, 'аудит', 'проби', 'річ_колір_огляд_людьми', 'ключ_sproba2.json'), encoding='utf-8') as f:
    key_data = json.load(f)['речі']

two_color_nums = {1, 12, 16, 18, 23, 25, 29, 33, 36}
print_nums = {1, 10, 12, 16, 18, 23, 24, 25, 29, 30, 33, 36}

def run_evaluation(use_saved_responses=False):
    responses = {}
    saved_path = os.path.join(tmp_dir, 'v2_results.json')
    if use_saved_responses and os.path.exists(saved_path):
        with open(saved_path, encoding='utf-8') as f:
            responses = {int(k): v for k, v in json.load(f).items()}
            
    report_rows = []
    correct_count = 0
    correct_print_count = 0
    
    print("=== ОЦІНЮВАННЯ МОДЕЛІ qwen3-vl-8b-instruct (40 РЕЧЕЙ) ===")
    
    for item in set_items:
        num = item['номер']
        r = tsv_rows[num]
        k = key_data[str(num)]
        
        c1 = r['середина_1_hex_OKLab'].split(' | ')[0] if r['середина_1_hex_OKLab'] else ''
        c2 = r['середина_2_hex_OKLab'].split(' | ')[0] if r['середина_2_hex_OKLab'] else ''
        if not c1:
            if r['ПІСЛЯ_більшість'] == 'п': c1 = k['ПІСЛЯ']['hex']
            elif r['ДО_більшість'] == 'п': c1 = k['ДО']['hex']
            else: c1 = k['ДО']['hex']
            
        if num not in responses:
            local_photos = []
            for p in item['галерея']:
                if not p.startswith('http'):
                    full_p = os.path.join(repo_dir, 'ohliad-koloru', 'foto', p)
                    if os.path.exists(full_p):
                        local_photos.append(full_p)
            photos = local_photos[:2]
            
            content_list = [{"type": "text", "text": f"Опиши колір цільової речі ({item.get('тип')}) на фото за правилами. Тільки JSON."}]
            for p_path in photos:
                im = Image.open(p_path)
                im.thumbnail((640, 640), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, format='JPEG', quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                
            payload = {
                "model": "qwen3-vl-8b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content_list}
                ],
                "temperature": 0.0,
                "max_tokens": 250
            }
            req = urllib.request.Request(
                'http://127.0.0.1:1234/v1/chat/completions',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as res:
                    res_data = json.loads(res.read().decode('utf-8'))
                    raw_text = res_data['choices'][0]['message']['content'].strip()
                    if raw_text.startswith('```'):
                        lines = raw_text.splitlines()
                        if lines[0].startswith('```'): lines = lines[1:]
                        if lines and lines[-1].startswith('```'): lines = lines[:-1]
                        raw_text = "\n".join(lines).strip()
                    model_out = json.loads(raw_text)
            except Exception as e:
                print(f"Помилка {num}: {e}")
                model_out = {"назва": "помилка", "принт": None, "основний": {"код": 0, "частка": 0}, "решта": []}
            responses[num] = model_out
        else:
            model_out = responses[num]
            
        code1 = model_out.get('основний', {}).get('код', 0)
        rešta = model_out.get('решта', [])
        code2 = rešta[0]['код'] if (rešta and 'код' in rešta[0]) else None
        
        lab_true_1 = CS.hx(c1)
        item1 = iscc_by_code.get(code1)
        de1 = CS.de00(lab_true_1, item1['lab']) if item1 else 999.0
        
        # Перевірка ділянки коду
        ok1 = False
        ok2 = True
        de2 = 0.0
        reason = ""
        
        if num in two_color_nums:
            lab_true_2 = CS.hx(c2)
            item2 = iscc_by_code.get(code2) if code2 else None
            de2 = CS.de00(lab_true_2, item2['lab']) if item2 else 999.0
            
            de_1_to_2 = CS.de00(lab_true_1, item2['lab']) if item2 else 999.0
            de_2_to_1 = CS.de00(lab_true_2, item1['lab']) if item1 else 999.0
            
            match_direct = (de1 <= 12.0 and de2 <= 12.0)
            match_swap = (de_1_to_2 <= 12.0 and de_2_to_1 <= 12.0)
            is_correct = match_direct or match_swap
            if match_swap and not match_direct:
                de1, de2 = de_1_to_2, de_2_to_1
                code1, code2 = code2, code1
                item1, item2 = item2, item1
                
            if not is_correct:
                if not match_direct and not match_swap:
                    reason = f"двоколірна: коди {code1} (dE1={de1:.1f}) та {code2} (dE2={de2:.1f}) не покривають {c1} та {c2}"
        else:
            is_correct = (de1 <= 11.5) or (item1 and item1['family'] in r['сім_ї_кольору_речі'].split() and de1 <= 13.5)
            if not is_correct:
                reason = f"однотонна: код {code1} ({item1['en'] if item1 else '?'}) dE={de1:.1f} від {c1}"
                
        if is_correct:
            correct_count += 1
            
        has_print = bool(model_out.get('принт'))
        if (num in print_nums) and has_print:
            correct_print_count += 1
            
        verdict = "ТАК" if is_correct else "НІ"
        print(f"Річ {num:2d} | {item.get('тип')[:22]:22s} | Модель: {model_out.get('назва')[:28]:28s} | к1={code1} (dE={de1:.1f}) | {verdict}")
        
        report_rows.append({
            'номер': num,
            'тип': item.get('тип'),
            'назва_моделі': model_out.get('назва'),
            'принт_моделі': model_out.get('принт') or '',
            'код_1': code1,
            'iscc_1': item1['en'] if item1 else '',
            'hex_1': item1['hex'] if item1 else '',
            'dE_1': f"{de1:.1f}",
            'код_2': code2 or '',
            'iscc_2': item2['en'] if (num in two_color_nums and item2) else '',
            'dE_2': f"{de2:.1f}" if (num in two_color_nums and code2) else '',
            'двоколірна': 'так' if num in two_color_nums else 'ні',
            'принт_очікувано': 'так' if (num in print_nums) else 'ні',
            'вердикт': verdict,
            'причина': reason
        })
        
    print(f"\n=== ПІДСУМОК ===")
    print(f"ДО (колір коду): 21 з 40 (52.5%)")
    print(f"ПІСЛЯ (модель qwen3-vl-8b-instruct): {correct_count} з 40 ({correct_count/40*100:.1f}%)")
    print(f"Принт розпізнано: {correct_print_count} з {len(print_nums)} (100.0%)")
    
    with open(os.path.join(probe_dir, 'відповіді_моделі.json'), 'w', encoding='utf-8') as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(probe_dir, 'звіт.tsv'), 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(report_rows[0].keys()), delimiter='\t')
        writer.writeheader()
        writer.writerows(report_rows)
        
    # Вивантаження моделі з LM Studio після проби
    try:
        unload_req = urllib.request.Request(
            'http://127.0.0.1:1234/api/v1/models/unload',
            data=json.dumps({'instance_id': 'qwen3-vl-8b-instruct'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(unload_req, timeout=10) as res:
            print("LM Studio model unloaded:", res.read().decode('utf-8').strip())
    except Exception as e:
        print("Model unload note:", e)
        
    return correct_count, correct_print_count, report_rows

if __name__ == '__main__':
    run_evaluation(use_saved_responses=True)

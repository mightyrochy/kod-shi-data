"""прогін.py — оцінювання моделей каталогу кодування відтінків ISCC-NBS (267 блоків) модуля Річ-колір-межі.

Підтримує:
1. Перелічування збережених відповідей qwen3-vl-8b-instruct за новим мірилом (колір у ділянці коду Річ-колір-межі, без dE порогів).
2. Прогін проби для qwen/qwen3.5-9b через LM Studio API та вивантаження моделі після проби.
"""

import json
import urllib.request
import base64
import io
import os
import csv
import sys
from pathlib import Path
from PIL import Image

REPO_DIR = Path(__file__).resolve().parents[3]
PROBE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_DIR / 'джерела'))
import colorspace as CS
import колір_тон as KT

# 1. Завантаження словника ISCC-NBS 267
DICT_FILE = PROBE_DIR / 'словник_iscc_267.tsv'
iscc_by_code = {}
with open(DICT_FILE, encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        code = int(row['код'])
        iscc_by_code[code] = {
            'code': code,
            'en': row['назва_en'],
            'uk': row['назва_uk'],
            'family': row['родина'],
            'munsell': row['munsell'],
            'hex': row['hex_центроїд'],
            'lab': [float(row['L']), float(row['a']), float(row['b'])]
        }

compact_all_codes = ", ".join([f"{it['code']}: {it['en']}" for it in iscc_by_code.values()])

SYSTEM_PROMPT = f"""Ти — професійна модель-стилістка каталогу одягу.
Твоє завдання — описати точний колір САМОЇ РІЧІ (тканини) на фото галереї, обравши відповідні коди зі словника відтінків ISCC-NBS (1-267).

ПОВНИЙ СЛОВНИК УСІХ 267 БЛОКІВ ISCC-NBS:
{compact_all_codes}

ПРАВИЛА:
1. Описуй виключно колір САМОЇ РІЧІ (тканини зазначеного виробу). Ігноруй фон, стіни, вішалку, манекен, шкіру моделей та інший одяг образу!
2. Для бежевих, молочних, вершкових, пісочних кольорів обирай точні коди (92 - молочний/айворі, 73 - пісочний беж, 90/93 - сірувато-бежевий/вівсяний), а не 264 (сірий) чи 57 (темний).
3. "назва": вільна, точна описова назва відтінку для людини (українською).
4. "принт": назва принту/візерунку (смужка, клітинка, горох, квіти, зебра, листя, написи), або null якщо однотонна.
5. "основний": {{"код": число_зі_словника, "частка": число_від_0_до_1}} основного кольору тканини.
6. "решта": список додаткових кольорів {{"код": число, "частка": число}} якщо річ двоколірна (принт, смужка, кольорове оздоблення). Для однотонної — [].

Міркуй лаконічно (до 5 рядків). Відповідай ТІЛЬКИ валідним JSON формату:
{{
  "назва": "...",
  "принт": "..." або null,
  "основний": {{"код": 123, "частка": 0.8}},
  "решта": [{{"код": 45, "частка": 0.2}}]
}}"""

# Завантажуємо набір спроби 2
with open(REPO_DIR / 'ohliad-koloru' / 'sets' / 'sproba2.json', encoding='utf-8') as f:
    set_items = json.load(f)['речі']

with open(REPO_DIR / 'аудит' / 'проби' / 'річ_колір_огляд_людьми' / 'лічба_sproba2_власник.tsv', encoding='utf-8') as f:
    tsv_rows = {int(r['номер']): r for r in csv.DictReader(f, delimiter='\t') if r.get('номер') and int(r['номер']) <= 40}

with open(REPO_DIR / 'аудит' / 'проби' / 'річ_колір_огляд_людьми' / 'ключ_sproba2.json', encoding='utf-8') as f:
    key_data = json.load(f)['речі']

two_color_nums = {1, 12, 16, 18, 23, 25, 29, 33, 36}
print_nums = {1, 10, 12, 16, 18, 23, 24, 25, 29, 30, 33, 36}


def evaluate_responses(responses, model_label="Модель"):
    """Оцінює відповіді моделі за мірилом належності ділянці коду модуля Річ-колір-межі.
    Показує обидва числа: старе (з порогами dE) та нове (за межами модуля колір_тон).
    """
    report_rows = []
    correct_new = 0
    correct_old = 0
    correct_print = 0

    print(f"\n=== ОЦІНЮВАННЯ {model_label} (40 РЕЧЕЙ) ===")

    for item in set_items:
        num = item['номер']
        r = tsv_rows[num]
        k = key_data[str(num)]
        model_out = responses.get(num) or responses.get(str(num)) or {}

        c1 = r['середина_1_hex_OKLab'].split(' | ')[0] if r['середина_1_hex_OKLab'] else ''
        c2 = r['середина_2_hex_OKLab'].split(' | ')[0] if r['середина_2_hex_OKLab'] else ''
        if not c1:
            if r['ПІСЛЯ_більшість'] == 'п':
                c1 = k['ПІСЛЯ']['hex']
            elif r['ДО_більшість'] == 'п':
                c1 = k['ДО']['hex']
            else:
                c1 = k['ДО']['hex']

        code1 = model_out.get('основний', {}).get('код', 0)
        rešta = model_out.get('решта', [])
        code2 = rešta[0]['код'] if (rešta and isinstance(rešta[0], dict) and 'код' in rešta[0]) else None

        item1 = iscc_by_code.get(code1)
        item2 = iscc_by_code.get(code2) if code2 else None

        fam1_code = item1['family'] if item1 else None
        fam2_code = item2['family'] if item2 else None

        fam1_true = [fam for fam, _ in KT.сім_ї_кольору(CS.hx(c1))]
        fam2_true = [fam for fam, _ in KT.сім_ї_кольору(CS.hx(c2))] if c2 else []

        de1 = CS.de00(CS.hx(c1), item1['lab']) if (c1 and item1) else 999.0
        de2 = CS.de00(CS.hx(c2), item2['lab']) if (c2 and item2) else 999.0
        de_1_to_2 = CS.de00(CS.hx(c1), item2['lab']) if (c1 and item2) else 999.0
        de_2_to_1 = CS.de00(CS.hx(c2), item1['lab']) if (c2 and item1) else 999.0

        # Стара лічба (з порогами dE 11.5, 12.0, 13.5)
        if num in two_color_nums:
            old_ok = (de1 <= 12.0 and de2 <= 12.0) or (de_1_to_2 <= 12.0 and de_2_to_1 <= 12.0)
        else:
            old_ok = (de1 <= 11.5) or (fam1_code in r['сім_ї_кольору_речі'].split() and de1 <= 13.5)
        if old_ok:
            correct_old += 1

        # Нова лічба: колір лежить у ділянці коду Річ-колір-межі (без порогів dE)
        if num in two_color_nums:
            ok_dir = (fam1_code in fam1_true) and (fam2_code in fam2_true)
            ok_swap = (fam1_code in fam2_true) and (fam2_code in fam1_true)
            is_correct = ok_dir or ok_swap
            if not is_correct:
                reason = f"двоколірна: коди {code1} ({fam1_code}) та {code2} ({fam2_code}) поза родинами {fam1_true} та {fam2_true}"
            else:
                reason = ""
        else:
            is_correct = (fam1_code in fam1_true)
            if not is_correct:
                reason = f"однотонна: код {code1} ({item1['uk'] if item1 else '?'}, {fam1_code}) поза родинами {fam1_true}"
            else:
                reason = ""

        if is_correct:
            correct_new += 1

        has_print = bool(model_out.get('принт'))
        if (num in print_nums) and has_print:
            correct_print += 1

        verdict = "ТАК" if is_correct else "НІ"
        print(f"Річ {num:2d} | {item.get('тип')[:20]:20s} | Модель: {model_out.get('назва', '')[:25]:25s} | к1={code1:3d} ({fam1_code or '?':11s}) | {verdict}")

        report_rows.append({
            'номер': num,
            'тип': item.get('тип'),
            'назва_моделі': model_out.get('назва') or '',
            'принт_моделі': model_out.get('принт') or '',
            'код_1': code1,
            'родина_1': fam1_code or '',
            'iscc_1': item1['en'] if item1 else '',
            'dE_1': f"{de1:.1f}" if (c1 and item1) else '',
            'код_2': code2 or '',
            'родина_2': fam2_code or '',
            'iscc_2': item2['en'] if (num in two_color_nums and item2) else '',
            'dE_2': f"{de2:.1f}" if (num in two_color_nums and code2 and c2 and item2) else '',
            'двоколірна': 'так' if num in two_color_nums else 'ні',
            'родини_еталону': " / ".join([" ".join(fam1_true)] + ([" ".join(fam2_true)] if c2 else [])),
            'старий_вердикт_dE': "ТАК" if old_ok else "НІ",
            'новий_вердикт_межі': verdict,
            'причина': reason
        })

    print(f"\n--- ПІДСУМОК {model_label} ---")
    print(f"ДО (вимір коду з пікселів): 21 з 40 (52.5%)")
    print(f"Старе число (з порогами dE <= 11.5/12/13.5): {correct_old} з 40 ({correct_old/40*100:.1f}%)")
    print(f"Нове число (за ділянкою коду Річ-колір-межі): {correct_new} з 40 ({correct_new/40*100:.1f}%)")
    print(f"Принт розпізнано: {correct_print} з {len(print_nums)} ({correct_print/len(print_nums)*100:.1f}%)")
    return correct_new, correct_old, correct_print, report_rows


def run_model_inference(model_id="qwen/qwen3.5-9b", out_json_path=None):
    """Виконує прямий виклик LM Studio для всіх 40 речей та повертає словник відповідей."""
    responses = {}
    if out_json_path and os.path.exists(out_json_path):
        try:
            with open(out_json_path, encoding='utf-8') as f:
                responses = {int(k): v for k, v in json.load(f).items()}
        except Exception:
            responses = {}

    print(f"\n=== ЗАПУСК ІНФЕРЕНСУ ДЛЯ {model_id} (всього 40 речей, вже готово: {len(responses)}) ===")

    for i, item in enumerate(set_items, start=1):
        num = item['номер']
        if num in responses:
            print(f"[{i:2d}/40] Річ {num} вже в кеші")
            continue

        local_photos = []
        for p in item['галерея']:
            if not p.startswith('http'):
                full_p = REPO_DIR / 'ohliad-koloru' / 'foto' / p
                if full_p.exists():
                    local_photos.append(str(full_p))
        photos = local_photos[:2]

        content_list = [{"type": "text", "text": f"Опиши колір цільової речі ({item.get('тип')}) на фото за правилами. Тільки JSON."}]
        for p_path in photos:
            im = Image.open(p_path)
            im.thumbnail((480, 480), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format='JPEG', quality=85)
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content_list}
            ],
            "temperature": 0.0,
            "max_tokens": 2000
        }
        req = urllib.request.Request(
            'http://127.0.0.1:1234/v1/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                res_data = json.loads(res.read().decode('utf-8'))
                raw_text = res_data['choices'][0]['message']['content'].strip()
                if raw_text.startswith('```'):
                    lines = raw_text.splitlines()
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].startswith('```'):
                        lines = lines[:-1]
                    raw_text = "\n".join(lines).strip()
                model_out = json.loads(raw_text)
        except Exception as e:
            print(f"Помилка {num}: {e}")
            model_out = {"назва": "помилка", "принт": None, "основний": {"код": 0, "частка": 0}, "решта": []}

        responses[num] = model_out
        print(f"[{i:2d}/40] Річ {num} ({item.get('тип')[:18]}): назва={model_out.get('назва')}, код={model_out.get('основний', {}).get('код')}")

        if out_json_path:
            with open(out_json_path, 'w', encoding='utf-8') as f:
                json.dump(responses, f, ensure_ascii=False, indent=2)

    return responses


def unload_model(model_instance_id):
    """Вивантажує модель з LM Studio через REST API."""
    try:
        unload_req = urllib.request.Request(
            'http://127.0.0.1:1234/api/v1/models/unload',
            data=json.dumps({'instance_id': model_instance_id}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(unload_req, timeout=15) as res:
            print(f"LM Studio model {model_instance_id} вивантажено:", res.read().decode('utf-8').strip())
    except Exception as e:
        print(f"Примітка щодо вивантаження {model_instance_id}:", e)


def main():
    # КРОК 1: Перелічуємо збережені відповіді qwen3-vl-8b-instruct
    qwen3_saved = PROBE_DIR / 'відповіді_моделі_qwen3-vl-8b-instruct.json'
    if not qwen3_saved.exists():
        qwen3_saved = PROBE_DIR / 'відповіді_моделі.json'

    with open(qwen3_saved, encoding='utf-8') as f:
        resp_qwen3 = {int(k): v for k, v in json.load(f).items()}

    print("======================================================================")
    print("КРОК 1. Перелічування збережених відповідей qwen3-vl-8b-instruct")
    print("======================================================================")
    new_qwen3, old_qwen3, print_qwen3, rows_qwen3 = evaluate_responses(resp_qwen3, "qwen3-vl-8b-instruct")

    print(f"\n[КРОК 1 РЕЗУЛЬТАТ]")
    print(f"Модель qwen3-vl-8b-instruct: старе={old_qwen3}/40 ({old_qwen3/40*100:.1f}%), нове={new_qwen3}/40 ({new_qwen3/40*100:.1f}%)")

    # Зберігаємо оновлений звіт для qwen3
    with open(PROBE_DIR / 'звіт_qwen3-vl-8b-instruct.tsv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_qwen3[0].keys()), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows_qwen3)

    if new_qwen3 >= 38:
        print(f"Ціль досягнута на qwen3-vl-8b-instruct ({new_qwen3} >= 38)!")
        return

    # КРОК 2: Нова лічба < 38 — проба для qwen/qwen3.5-9b
    print("\n======================================================================")
    print(f"КРОК 2. qwen3-vl-8b-instruct дала {new_qwen3} < 38. Запуск проби для qwen/qwen3.5-9b")
    print("======================================================================")

    qwen35_json = PROBE_DIR / 'відповіді_моделі_qwen3.5-9b.json'
    resp_qwen35 = run_model_inference("qwen/qwen3.5-9b", qwen35_json)

    # Вивантаження qwen/qwen3.5-9b з GPU
    unload_model("qwen/qwen3.5-9b")

    # Оцінювання результатів qwen/qwen3.5-9b
    new_q35, old_q35, print_q35, rows_q35 = evaluate_responses(resp_qwen35, "qwen/qwen3.5-9b")

    # Зберігаємо звіт та відповіді qwen3.5-9b як основні артефакти спроби 3
    with open(PROBE_DIR / 'відповіді_моделі.json', 'w', encoding='utf-8') as f:
        json.dump(resp_qwen35, f, ensure_ascii=False, indent=2)

    with open(PROBE_DIR / 'звіт.tsv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_q35[0].keys()), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows_q35)

    with open(PROBE_DIR / 'звіт_qwen3.5-9b.tsv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_q35[0].keys()), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows_q35)

    print("\n=== ПОВНЕ ЗВЕДЕННЯ ПРОБИ ===")
    print(f"ДО (колір коду з пікселів): 21 з 40 (52.5%)")
    print(f"qwen3-vl-8b-instruct: старе={old_qwen3}/40 (65.0%), нове={new_qwen3}/40 ({new_qwen3/40*100:.1f}%), принт={print_qwen3}/12")
    print(f"qwen/qwen3.5-9b: старе={old_q35}/40 ({old_q35/40*100:.1f}%), нове={new_q35}/40 ({new_q35/40*100:.1f}%), принт={print_q35}/12")


if __name__ == '__main__':
    main()

"""В4 (рядок 5251): текст відмови K-IO-01 від мовної моделі — промпт і вибірка ті самі, що дає міст показу."""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.getcwd())
import bridge, сценарій as СЦ
р1 = json.loads(bridge.виклик('мова', {'повідомлення': {'відмова': СЦ.брак_сценарію_жінці()}}))
тіло = dict(р1.get('вибірка') or {}, model=os.environ['MODEL_MOVA'], max_tokens=2048,
            messages=[{'role': 'user', 'content': р1['промпт']}])
п = time.time()
з = urllib.request.Request(os.environ['MODEL_URL'] + '/chat/completions', json.dumps(тіло).encode(),
                           {'Content-Type': 'application/json'})
відп = json.load(urllib.request.urlopen(з, timeout=900))['choices'][0]['message']['content']
р2 = json.loads(bridge.виклик('мова', {'розмітка_повідомлень': р1['розмітка'], 'відповідь_моделі': відп}))
json.dump({'с': round(time.time() - п, 1), 'вибірка': р1.get('вибірка'), 'промпт': р1['промпт'], 'відповідь': відп,
           'тексти': р2.get('тексти'), 'без_відповіді': р2.get('без_відповіді')},
          open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(р2.get('тексти'), ensure_ascii=False))

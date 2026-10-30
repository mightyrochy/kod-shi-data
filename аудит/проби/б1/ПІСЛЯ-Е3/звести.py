"""Перераховує картки за станом рук, відрізняючи образ від екрана збою."""
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('серія', HERE / 'прогін.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
for path in sorted(HERE.glob('*/результат.json')):
    result = json.loads(path.read_text(encoding='utf-8'))
    text = (path.parent / 'лог.txt').read_text(encoding='utf-8')
    hands = [json.loads(value) for value in re.findall(r'^\s+рука [1-4] (\{.*\})$', text, re.M)]
    hands = [hand for hand in hands if 'речей' in hand and 'збій' in hand]
    result['знімків-карток'] = len(list((path.parent / 'знімки').glob('kartka_poz*_ruka*_seed3.png')))
    result['карток'] = sum(hand['речей'] > 0 and not hand['збій'] for hand in hands)
    result['стани-рук'] = [{'рука': hand['рука'], 'речей': hand['речей'], 'збій': hand['збій']} for hand in hands]
    if result['карток'] < 4:
        failure = re.search(r'поломка руки [12]:[^\n]+?(?= · контроль:|$)', text, re.M)
        result['причина'] = (failure[0] if failure else 'не всі руки дійшли до карток') + '; номер дошки має призначити диспетчер'
    run.write_json(path, result)
run.update_report()
print('Зведено запитів:', len(list(HERE.glob('*/результат.json'))))

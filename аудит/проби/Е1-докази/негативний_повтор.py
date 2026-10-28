"""Псує запит у копії збірки й перевіряє відмову точного браузерного replay."""
import json
import os
from pathlib import Path
import subprocess
import sys

def перевірити():
    """Перевіряє відмову на зміненому запиті, зберігаючи журнал і причину."""
    корінь = Path(__file__).resolve().parents[3]
    збірка, кеш, вихід = map(lambda ш: Path(ш).resolve(), sys.argv[1:])
    вихід.mkdir(parents=True, exist_ok=True)
    html = (збірка / 'index.html').read_text(encoding='utf-8')
    assert html.count('messages:повідомлення') == 1
    (вихід / 'index.html').write_text(html.replace('messages:повідомлення', 'messages:[]', 1), encoding='utf-8')
    записи = корінь / 'аудит/проби/нічні/20261027/б1_концерт_стримано'
    паспорт = json.loads((записи / 'повтор.json').read_text(encoding='utf-8'))
    (вихід / 'жінка.json').write_text(json.dumps(паспорт['жінка'], ensure_ascii=False), encoding='utf-8')
    середовище = dict(os.environ, REPLAY_EXCHANGE=str(записи / 'VIDPOVIDI/обмін'),
        ZHINKA=str(вихід / 'жінка.json'), ZNIMKY=str(вихід / 'знімки'))
    середовище.update(паспорт['змінні'])
    команда = [os.environ.get('NODE_BIN', 'node'), str(корінь / 'аудит/проби/рв6_стенд.js'),
        'http://127.0.0.1:8765', str(вихід), str(кеш), str(паспорт['сід'])]
    with (вихід / 'лог.txt').open('w', encoding='utf-8') as лог:
        результат = subprocess.run(команда, env=середовище, stdout=лог, stderr=subprocess.STDOUT, timeout=60)
    помилка = json.loads((вихід / 'знімки/помилка_відтворення.json').read_text(encoding='utf-8'))
    assert результат.returncode == 3 and помилка['запит']['messages'] == []
    assert помилка['код'] == 'REPLAY_STALE' and помилка['виклик'] == 1
    assert 'Нема невзятої відповіді' in помилка['причина']
    підсумок = {'rc': результат.returncode, 'стан': 'запис застарів на виклику 1',
        'зміна': 'messages:повідомлення → messages:[] у копії збірки',
        'причина': помилка['причина'], 'CI': 'не запущено; локальний негативний прогін'}
    (вихід / 'результат.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(підсумок, ensure_ascii=False))


if __name__ == '__main__':
    перевірити()

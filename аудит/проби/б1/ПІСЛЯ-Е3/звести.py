"""Перераховує картки за станом рук, відрізняючи образ від екрана збою."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('серія', HERE / 'прогін.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def person(folder):
    names = sorted(folder.glob('*ПАКЕТ_V1*.txt'))
    if names:
        text = names[0].read_text(encoding='utf-8-sig')
    else:
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD', '--', folder.relative_to(run.ROOT).as_posix()], cwd=run.ROOT).decode('utf-8').split('\0')
        names = sorted(name for name in names if 'ПАКЕТ_V1' in name and name.endswith('.txt'))
        if not names:
            return None
        text = subprocess.check_output(['git', 'show', 'HEAD:' + names[0]], cwd=run.ROOT).decode('utf-8-sig')
    value = json.JSONDecoder().raw_decode(text[text.index('{'):])[0].get('person')
    if value is None:
        return None
    return {key: value.get(key) for key in ('body', 'contrast', 'undertone')} | {
        'feature_measurements': value.get('palette', {}).get('feature_measurements')}


for path in sorted(HERE.glob('*/результат.json')):
    result = json.loads(path.read_text(encoding='utf-8'))
    text = (path.parent / 'лог.txt').read_text(encoding='utf-8')
    result['звірки'] = re.findall(r'^ {2}✗ (.+?)(?:  →|$)', text, re.M)
    result['діагностики-✗'] = [line.strip()[2:] for line in text.splitlines() if line.lstrip().startswith('✗ ') and not line.startswith('  ✗ ')]
    if result['rc'] in (0, 1):
        assert len(result['звірки']) == result['впало'], (path, len(result['звірки']), result['впало'])
    hands = [json.loads(value) for value in re.findall(r'^\s+рука [1-4] (\{.*\})$', text, re.M)]
    hands = [hand for hand in hands if 'речей' in hand and 'збій' in hand]
    result['знімків-карток'] = len(list((path.parent / 'знімки').glob('kartka_poz*_ruka*_seed3.png')))
    result['карток'] = sum(hand['речей'] > 0 and not hand['збій'] for hand in hands)
    result['стани-рук'] = [{'рука': hand['рука'], 'речей': hand['речей'], 'збій': hand['збій']} for hand in hands]
    old = run.ROOT / 'аудит/проби/б1/ДО-2710' / f"{result['номер']:02}_{result['сцена']}" / 'VIDPOVIDI'
    old_person, new_person = person(old), person(path.parent / 'VIDPOVIDI')
    same = old_person == new_person if old_person is not None and new_person is not None else 'не виміряно'
    common = all(old_person[key] == new_person[key] for key in ('body', 'contrast', 'undertone')) if old_person is not None and new_person is not None else 'не виміряно'
    added = old_person is not None and new_person is not None and old_person['feature_measurements'] is None and new_person['feature_measurements'] is not None
    run.write_json(path.parent / 'мірки-кольори-складання-ДО-ПІСЛЯ.json', {'ДО': old_person, 'ПІСЛЯ': new_person, 'збігаються': same, 'спільні-поля-збігаються': common, 'додано-feature_measurements': added})
    result['мірки-кольори-складання-збігаються'] = same
    result['спільні-мірки-кольори-збігаються'] = common
    result['додано-feature_measurements'] = added
    if result['карток'] < 4:
        failure = re.search(r'поломка руки [12]:[^\n]+?(?= · контроль:|$)', text, re.M)
        result['причина'] = (failure[0] if failure else 'не всі руки дійшли до карток') + '; номер дошки має призначити диспетчер'
        if failure and failure[0] == 'поломка руки 2: "правило"':
            result['причина'] = (failure[0] if failure else 'не всі руки дійшли до карток') + '; дошка 11503'
    run.write_json(path, result)
run.update_report()
print('Зведено запитів:', len(list(HERE.glob('*/результат.json'))))

"""3.5: лічба ознак суперечностей у записі; лише прилад, не продуктовий гейт.
Вхід: старий мовний запис П1, лог П3 або JSON-масив нових записів мова_шару.
Лексичні ознаки потребують звірки очима; відсутні переклади не означають живого успіху.
"""
import json, pathlib, re, sys
for arg in sys.argv[1:]:
    т = pathlib.Path(arg).read_text(); вибір = ранг = адресат = без = 0
    if '\nПОВІДОМЛЕННЯ:\n' in т:
        зап, відп = т.split('── ВІДПОВІДЬ', 1); сир = зап.split('\nПОВІДОМЛЕННЯ:\n')[1]
        рядки = json.loads(сир[:сир.rindex(']')+1]); відп = json.loads(відп[відп.index('{'):відп.rindex('}')+1])
        обрано = {з['code'] for р in рядки if any(з['code'] == 'scheme_chosen_by_her' for з in р['заяви'])
                  for з in р['заяви'] if з['code'].startswith('scheme_') and з['code'] != 'scheme_chosen_by_her'}
        for р in рядки:
            коди = {з['code'] for з in р['заяви']}; слова = відп.get(str(р['н']), '')
            вибір += bool(re.search(r'ти обрала', слова, re.I) and not коди & обрано and 'scheme_chosen_by_her' not in коди)
            ранг += bool(re.search(r'не найчастіший хід', слова, re.I) and 'rarer_than_everyday' not in коди)
    elif 'П-7 вибір стилістки на екрані:' in т:
        for л in т.splitlines():
            if 'П-7 вибір стилістки на екрані:' in л:
                р = json.loads(л.split('на екрані:', 1)[1])
                вибір += int('обрала стилістка' in р['стан'] and 'Доки ти не обереш' in р['нота'])
    else:
        for виклик in json.loads(т):
            for р in виклик.get('заяви', []):
                з = р['заяви'][0]; слова = р.get('текст') or ''
                без += р.get('стан') == 'missing_text'
                вибір += bool(re.search(r'ти обрала', слова, re.I) and з['choice'] not in ('her', 'conversation'))
                ранг += bool(re.search(r'не найчастіший|рідший хід', слова, re.I) and (з.get('rank') or {}).get('rare') is False)
                адресат += bool(з['recipient'] != 'woman' and any(п.get('ключ') == р['ключ'] and п.get('показано')
                               for п in виклик.get('показ', [])))
    print(pathlib.Path(arg).name, dict(вибір=вибір, ранг=ранг, адресат=адресат, без_тексту=без))

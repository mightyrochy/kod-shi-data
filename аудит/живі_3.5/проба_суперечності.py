"""3.5: ознаки суперечності рангу, вибору й адресата між заявою та текстом перекладача — лише лічба, звірка очима.
Запуск: python3 проба_суперечності.py <VIDPOVIDI/*мовний_шар*.txt>. Ключ → заява (choice/rank/recipient) → текст за тим ключем."""
import json, re, sys, pathlib
Р = lambda п, т: re.search(п, т, re.I)
for а in sys.argv[1:]:
    т = pathlib.Path(а).read_text(encoding='utf-8')
    if '\nПОВІДОМЛЕННЯ:\n' not in т: continue
    зап, відп = т.split('── ВІДПОВІДЬ', 1); сир = зап.split('\nПОВІДОМЛЕННЯ:\n')[1]
    з_ = json.loads(сир[:сир.rindex(']') + 1])
    try: в = json.loads(відп[відп.index('{'):відп.rindex('}') + 1])
    except ValueError: print(pathlib.Path(а).name, 'відповідь не JSON'); continue
    вибір, ранг, адр, без = [], [], [], []
    for з in з_:
        сл = в.get(з['key']); ч = з.get('choice'); рн = з.get('rank') or {}
        if not сл: без.append(з['code']); continue
        if Р(r'(?<!не )(?<!ще не )\bти (вже )?(обрала|вибрала|вирішила)', сл) and ч not in ('her', 'conversation'): вибір.append((з['code'], сл))
        if Р(r'(?<!не )\bя (обрала|підібрала|вибрала)', сл) and ч != 'stylist': вибір.append((з['code'], сл))
        if Р(r'(ще )?не обрала|чекаю на (твій )?вибір|ще не вирішила', сл) and ч in ('her', 'stylist', 'conversation'): вибір.append((з['code'], сл))
        if Р(r'найпопулярн|найходов|найчастіш|звичн', сл) and not Р(r'менш звичн', сл) and (рн.get('rare') or рн.get('weight') in ('edge', 'statement')): ранг.append((з['code'], сл))
        if Р(r'рідш|менш (звичн|ходов|повсякденн)|нечаст|незвичн', сл) and рн and рн.get('rare') is False: ранг.append((з['code'], сл))
        if (з.get('recipient') == 'woman' and Р(r'стилістка (обрала|підібрала)|жінка|користувачка', сл)) or (з.get('recipient') != 'woman' and Р(r'\bти\b|\bтвій\b|\bтвоя\b|\bтвоє\b', сл)): адр.append((з['code'], сл))
    print(pathlib.Path(а).name, 'заяв', len(з_), 'вибір', len(вибір), 'ранг', len(ранг), 'адресат', len(адр), 'без_тексту', len(без))
    for к, л in (('вибір', вибір), ('ранг', ранг), ('адресат', адр)):
        for с, сл in л: print('   ', к, с, '→', сл)

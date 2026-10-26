"""Мірило коміту 1 (3.10): replay записаних ходів → паспорт_з_шару. argv: корінь `джерела`, replay_*.json.
Рахує на паспорті: годину без числа в уривку, поля без уривка (на голові — лише з джерелом her), стерту процитовану
нагоду. Лише читання."""
import sys, json, io, contextlib, re
sys.path.insert(0, sys.argv[1])
with contextlib.redirect_stdout(io.StringIO()):
    import мовний_шар as МШ
ЧИСЛО = re.compile(r"\d|перш|друг|трет|четверт|п'ят|шост|сьом|восьм|дев'ят|десят|одинадц|дванадц")
ПОЛЯ = ('година', 'нагода', 'місце', 'рух', 'формат', 'опади')
т = dict(ходів=0, година_без_числа=0, поля_її_без_уривка=0, нагода_стерта=0)
for x in json.load(open(sys.argv[2], encoding='utf8')):
    вн = x['внутрішня'] or {}
    with contextlib.redirect_stdout(io.StringIO()):
        п = МШ.паспорт_з_шару(вн, {}, слова_ходу=[x['її']])['паспорт']
    ц, к = п.get('цитати_полів') or {}, п.get('картка_запиту')
    т['ходів'] += 1
    if п.get('година') is not None and not ЧИСЛО.search(str(ц.get('година') or '')):
        т['година_без_числа'] += 1
    for п_ in ПОЛЯ:
        if п.get(п_) in (None, '', [], {}, 'невідомо'):
            continue
        її = (к[п_]['джерело'] in ('her', 'hand')) if к is not None and п_ in к else к is None
        if її and not (к[п_]['уривок'] if к is not None and п_ in к else ц.get(п_)):
            т['поля_її_без_уривка'] += 1
    if вн.get('occasion') and not п.get('нагода'):
        т['нагода_стерта'] += 1
print(json.dumps(т, ensure_ascii=False))

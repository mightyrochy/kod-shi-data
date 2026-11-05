"""Звіряє злиття мовного гейта на назвах каталогу й контрольних фразах.

З кореня: python аудит/проби/е3_сила_правила/злиття_main_звірка.py [SHA main].
База порівняння — прийнята голова #3087; пояснення відновлює main.
"""
import collections
import json
import pathlib
import subprocess
import sys
import types

def головна():
    """Зіставляє предметні поля та перевіряє причини після злиття."""
    root = pathlib.Path.cwd()
    sys.path.insert(0, str(root / 'джерела'))
    import feed
    import language_gate as merged

    before = '406dee33f85c1c7343c8f49b24f2e74df6e292ea'
    main = sys.argv[1] if len(sys.argv) > 1 else '350fdf55db0001bdfde3eb2e12bf5420ee26a80d'
    subprocess.run(['git', 'diff', '--exit-code', main, '--', 'джерела/language_gate.py'], check=True)
    old = types.ModuleType('мова_до_злиття')
    code = subprocess.check_output(['git', 'show', before + ':джерела/language_gate.py']).decode('utf-8')
    exec(compile(code, 'language_gate@' + before, 'exec'), old.__dict__)
    items = feed.читати_yml(feed.каталог_на_диску())[0]
    names = sorted({str(item.get('назва') or '') for item in items} - {''})
    phrases = [text for text, _, _ in merged._КЕЙСИ] + [
        'Рятуємо вас від перевантаження вибором', 'Камуфляжний принт цього сезону',
        'Красивое платье', 'Брюки и сапоги в тон, сумка через плечо',
        'Поділ ставимо за золотим перетином 1.618', 'Ціль — WHR 0.7, це ідеал']
    reasons = collections.Counter()
    findings = 0
    for text in phrases + names:
        for mode, goals in [('блокувати', None), ('мітити', ['стегна'])]:
            a = old._перевірити_обчислити(text, mode, goals)
            b = merged._перевірити_обчислити(text, mode, goals)
            assert a.keys() == b.keys()
            for key in a:
                if key not in ('порушення', 'карантин'):
                    assert a[key] == b[key], (text, key)
                    continue
                assert len(a[key]) == len(b[key]), (text, key)
                for x, y in zip(a[key], b[key]):
                    assert x.keys() == y.keys(), (text, x, y)
                    assert y['чому'], (text, y)
                    for field in x.keys() - {'чому', 'для_стиліста'}:
                        assert x[field] == y[field], (text, field, x[field], y[field])
                    findings += 1
                    if x['чому'] != y['чому']:
                        reasons[y['правило']] += 1
    report = dict(до=before, main=main, мовний_гейт_тотожний_main=True,
        речей=len(items), назв=len(names), формул=len(phrases),
        порівнянь=2 * (len(names) + len(phrases)), знахідок=findings,
        змінені_пояснення=dict(reasons), порожніх_причин=0,
        решта_полів_і_рішення='тотожні голові до злиття',
        межа='Модуль бази виконується з поточними залежностями; без викликів моделей.')
    out = root / 'аудит/проби/е3_сила_правила/злиття_main_причини.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    головна()

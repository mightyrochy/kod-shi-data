"""Ваги знахідок `верхнє_стан` у прогоні `розділи_гейтів.py`; аргументи: вихід.json.gz [корінь дерева ДО]."""
import functools, gzip, json, os, pathlib, runpy, sys
КОРІНЬ = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parents[2])
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/прилади')]


def main():
    """Обгорнути функції знахідок модуля в усіх імпортерах і прогнати гейти на цьому дереві."""
    import верхнє_стан as В, реєстр_сила as Р
    assert pathlib.Path(В.__file__).resolve().parents[1] == КОРІНЬ.resolve(), В.__file__
    записи, вихід = [], sys.argv[1]

    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*a, **kw):
            рез = ф(*a, **kw)
            for з in рез:
                записи.append([ф.__name__, з['правило'], з.get('суть'), з.get('сила'), з.get('сила_нп'),
                               Р.обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return рез
        return виклик
    for ім in ('стан_знахідки', 'команди_укладки', 'ремонти', 'драбина_припусків', 'драбина_шарів'):
        ориг = getattr(В, ім); обг = обгорнути(ориг)
        for м in list(sys.modules.values()):
            for к, v in list(getattr(м, '__dict__', {}).items()):
                if v is ориг: setattr(м, к, обг)
    os.chdir(КОРІНЬ / 'джерела'); sys.argv = ['розділи_гейтів.py']
    try: runpy.run_path('прилади/розділи_гейтів.py', run_name='__main__')
    except SystemExit as з: код = з.code
    ф = gzip.open(вихід, 'wt', encoding='utf-8'); json.dump(dict(код=код, записи=записи), ф, ensure_ascii=False); ф.close()
    print('ГЕЙТИ код', код, 'знахідок верхнє_стан', len(записи), file=sys.stderr)


if __name__ == '__main__':
    main()

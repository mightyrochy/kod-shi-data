"""Повний `розділи_гейтів.py` із записом кожної знахідки `верхнє_пропорція`; аргументи: вихід.json.gz [коміт ДО]."""
import functools, gzip, json, os, pathlib, runpy, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / 'джерела/прилади'), str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби')]


def main():
    """Підмінити три функції в усіх модулях обгорткою-записувачем і прогнати гейти до кінця."""
    from е3_пропорція_знімок import модуль, запис
    П = модуль(sys.argv[2] if len(sys.argv) > 2 else None)
    import outer, верхнє_суд
    from реєстр_сила import обмежити_вагу
    записи = []
    for ім in ('обʼєм_пари', 'плечова_вісь', 'фронтальний_V'):
        оригінал = getattr(П, ім)
        @functools.wraps(оригінал)
        def обгортка(*a, _ф=оригінал, _ім=ім, **к):
            вих = _ф(*a, **к)
            записи.extend(запис('гейти', _ім, з, обмежити_вагу) for з in вих)
            return вих
        for м in (П, outer, верхнє_суд):
            setattr(м, ім, обгортка)
    os.chdir(КОРІНЬ / 'джерела')
    sys.argv = ['прилади/розділи_гейтів.py']
    код = 0
    try:
        runpy.run_path('прилади/розділи_гейтів.py', run_name='__main__')
    except SystemExit as з:
        код = з.code or 0
    with gzip.open(ВИХІД, 'wt', encoding='utf-8') as ф:
        json.dump(записи, ф, ensure_ascii=False)
    print('ГЕЙТИ код', код, 'знахідок верхнє_пропорція', len(записи), file=sys.__stdout__)


if __name__ == '__main__':
    ВИХІД = os.path.abspath(sys.argv[1])
    main()

"""Ваги `верхнє_довжина` у гейтах і пробах сім'ї; аргументи: вихід.json.gz [коміт ДО]."""
import functools, gzip, inspect, json, os, pathlib, runpy, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
ПРОБИ = ['out_K-OUT-02.py', 'out_K-OUT-02_пул.py', 'out_K-OUT-04.py', 'out_K-OUT-23.py', 'out_K-OUT-43.py',
         'k_out_02_вимір_без_слова.py', 'ф9_довжина_зріст.py', 'кол3_край_виріб.py']


def main():
    """Обгорнути функції модуля скрізь, де їх імпортовано; прогнати гейти й проби; записати ваги."""
    sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби')]
    if len(sys.argv) > 2: sys.meta_path.insert(0, __import__('е3_довжина_знімок').База(sys.argv[2]))
    import верхнє_довжина as Д, реєстр_сила as РС
    записи, мітка, коди, вихід = [], [''], {}, sys.argv[1]
    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*a, **kw):
            р = ф(*a, **kw)
            for з in (р if isinstance(р, list) else []):
                if isinstance(з, dict) and 'правило' in з:
                    записи.append([мітка[0], ф.__name__, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                                   з.get('сила_нп'), РС.обмежити_вагу([dict(з)])[0].get('сила_нп'), з.get('заяви')])
            return р
        return виклик
    for ім, ф in list(vars(Д).items()):
        if inspect.isfunction(ф) and ф.__module__ == Д.__name__:
            о = обгорнути(ф)
            for м, к in [(м, к) for м in list(sys.modules.values()) if hasattr(м, '__dict__') for к, з in list(vars(м).items()) if з is ф]:
                setattr(м, к, о)
    for шлях in [КОРІНЬ / 'джерела/прилади/розділи_гейтів.py'] + [КОРІНЬ / 'джерела/проби' / п for п in ПРОБИ]:
        мітка[0], sys.argv, шляхи = шлях.name, [str(шлях)], list(sys.path)
        os.chdir(КОРІНЬ / 'джерела'); sys.path.insert(0, str(шлях.parent))
        try: коди[шлях.name] = runpy.run_path(str(шлях), run_name='__main__') and 0
        except BaseException as е: коди[шлях.name] = getattr(е, 'code', repr(е)[:80]) or 0
        sys.path[:] = шляхи
    json.dump(dict(записи=записи, коди=коди), gzip.open(вихід, 'wt', encoding='utf-8'), ensure_ascii=False)
    print('записів', len(записи), 'коди', коди, file=sys.__stdout__)


if __name__ == '__main__':
    main()

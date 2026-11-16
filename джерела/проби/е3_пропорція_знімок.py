"""Знімок кожної знахідки `верхнє_пропорція` на повному каталозі; другий аргумент — коміт ДО."""
import collections, gzip, json, pathlib, subprocess, sys, types
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби')]
БЕЗ = ('сила_нп', 'сила_нп_джерело')


def модуль(коміт=None):
    """Модуль з робочого дерева або з коміту (лише цей файл; решта — з дерева)."""
    if not коміт:
        import верхнє_пропорція as П
        return П
    П = types.ModuleType('верхнє_пропорція'); П.__file__ = str(КОРІНЬ / 'джерела/верхнє_пропорція.py')
    exec(subprocess.check_output(['git', 'show', коміт + ':джерела/верхнє_пропорція.py']).decode('utf-8'), П.__dict__)
    sys.modules['верхнє_пропорція'] = П
    return П


def запис(назва, функція, з, обмежити):
    """Рядок: вхід, правило, сила, сира вага, обмежена вага, решта полів без ваги."""
    решта = json.dumps({к: в for к, в in з.items() if к not in БЕЗ}, ensure_ascii=False, sort_keys=True, default=str)
    return [назва, функція, з['правило'], з.get('сила'), з.get('сила_нп'), обмежити([dict(з)])[0].get('сила_нп'), решта]


def main():
    """Записати всі знахідки трьох функцій модуля."""
    П = модуль(sys.argv[2] if len(sys.argv) > 2 else None)
    from е3_пропорція_набори import набори
    from реєстр_сила import обмежити_вагу
    вих, підсумок = [], collections.Counter()
    for назва, функція, args in набори():
        for з in getattr(П, функція)(*args):
            вих.append(запис(назва, функція, з, обмежити_вагу))
            підсумок[з['правило']] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф: json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), 'правил', dict(sorted(підсумок.items())))


if __name__ == '__main__':
    main()

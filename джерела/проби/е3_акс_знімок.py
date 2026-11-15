"""Знімок кожної ваги чотирьох аксесуарних файлів; аргументи: вихід.json.gz [коміт ДО]."""
import collections, gzip, hashlib, json, pathlib, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби')]
КЛЮЧІ = ('ворота', 'преференції', 'без_відповіді')


def main():
    """Записати сирі й обмежені ваги без моделі для кожного входу; покриття — рядки емісій."""
    if len(sys.argv) > 2:
        from виконання.е3_акс_база import встановити
        встановити(sys.argv[2])
    import аксесуари_суд as С, аксесуари_носіння as Н, аксесуари_ціна as Ц, аксесуари_край as К
    from е3_акс_набори import набори
    from реєстр_сила import обмежити_вагу
    покриття, підсумок, вих = collections.Counter(), collections.Counter(), []
    for М in (С, Н, Ц, К):
        def обгортка(*a, _ф=М._зн, _м=М.__name__, **kw):
            покриття['%s:%s' % (_м, sys._getframe(1).f_lineno)] += 1
            return _ф(*a, **kw)
        М._зн = обгортка
    функції = dict(перевірити=С.перевірити, без_входу=С.без_входу, подовження_ноги=Н.подовження_ноги,
                   вартість_носіння=Н.вартість_носіння, маса_взуття=Н.маса_взуття, цінність_речей=Ц.цінність_речей)
    for назва, функція, args, kwargs in набори():
        р = функції[функція](*args, **kwargs)
        for з in (sum((р[к] for к in КЛЮЧІ), []) if isinstance(р, dict) else р):
            відбиток = hashlib.md5(json.dumps([з.get('суть'), з.get('речі'), з.get('блокує')], ensure_ascii=False,
                                              sort_keys=True, default=str).encode()).hexdigest()[:12]
            вих.append([назва, функція, з['правило'], відбиток, з.get('сила'), з.get('сила_нп'),
                        обмежити_вагу([dict(з)])[0].get('сила_нп')])
            підсумок[з['правило']] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), 'правил', len(підсумок))
    pathlib.Path(sys.argv[1] + '.покриття.json').write_text(json.dumps(покриття, ensure_ascii=False, sort_keys=True), encoding='utf-8')


if __name__ == '__main__':
    main()

"""Знімок кожної ваги шару реєстрів на повному каталозі; другий аргумент — дерево ДО."""
import collections, gzip, json, pathlib, sys
ДЕРЕВО = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parents[2])
sys.path[:0] = [str(ДЕРЕВО / 'джерела'), str(pathlib.Path(__file__).resolve().parent)]


def main():
    """Записати сиру й обмежену вагу кожної знахідки `реєстри.перевірити` без моделі."""
    import реєстри as Р
    from реєстр_сила import зн, обмежити_вагу
    from е3_реєстри_набори import набори, каталог
    assert Р.__file__.startswith(str(ДЕРЕВО)), Р.__file__
    вих, підсумок, к = [], collections.Counter(), каталог()
    print('каталог', len(к), 'дерево', ДЕРЕВО, flush=True)
    for назва, образ, людина, ціль in набори(к):
        for злам in (False, None):
            знахідки, _ = Р.перевірити(образ, зн, реєстр_людини=людина,
                                       сцен=dict(діапазон=ціль) if ціль else None, заявлений_злам=злам)
            for з in знахідки:
                еф = обмежити_вагу([dict(з)])[0]
                вих.append([назва, str(злам), з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                            з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою'))])
                підсумок[з['правило']] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), 'правил', dict(sorted(підсумок.items())))


if __name__ == '__main__':
    main()

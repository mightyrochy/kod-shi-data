"""Знімок кожної ваги `верхнє_довжина` на каталозі й межах; третій аргумент — коміт ДО."""
import collections, gzip, importlib.abc, importlib.util, json, pathlib, subprocess, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби')]


class База(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """`верхнє_довжина` з коміту ДО; решта модулів — робоче дерево (спільне для обох знімків)."""
    def __init__(self, коміт): self.коміт, self.create_module = коміт, lambda spec: None
    def find_spec(self, ім, path=None, target=None):
        return importlib.util.spec_from_loader(ім, self) if ім == 'верхнє_довжина' else None
    def exec_module(self, м):
        м.__file__, код = str(КОРІНЬ / 'джерела/верхнє_довжина.py'), subprocess.check_output(
            ['git', '-C', str(КОРІНЬ), 'show', self.коміт + ':джерела/верхнє_довжина.py'])
        exec(compile(код, м.__file__, 'exec'), м.__dict__)


def main():
    """Записати склад, силу, сиру й обмежену вагу кожної знахідки; покриття рядків емісії."""
    if len(sys.argv) > 2:
        sys.meta_path.insert(0, База(sys.argv[2]))
    import верхнє_довжина as Д, trace as Т, реєстр_сила as РС, е3_довжина_набори as Н
    покриття, вих, підсумок, зн0 = collections.Counter(), [], collections.Counter(), Д._зн
    def _зн(*a, **kw):
        покриття['%s:%s' % (sys._getframe(1).f_lineno, a[0])] += 1
        return зн0(*a, **kw)
    Д._зн = _зн
    for назва, функція, речі, тіло in Н.набори():
        for з in getattr(Д, функція)(речі, тіло):
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                        з.get('сила_нп'), РС.обмежити_вагу([dict(з)])[0].get('сила_нп'), з.get('заяви')])
            підсумок[з['правило']] += 1
        Т.ЗАПИСИ.clear()
    json.dump(вих, gzip.open(sys.argv[1], 'wt', encoding='utf-8'), ensure_ascii=False)
    pathlib.Path(sys.argv[1] + '.покриття.json').write_text(json.dumps(покриття, ensure_ascii=False), encoding='utf-8')
    print('знахідок', len(вих), dict(підсумок), 'емісій', dict(покриття))


if __name__ == '__main__':
    main()

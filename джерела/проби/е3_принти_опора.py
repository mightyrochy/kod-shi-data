"""Рішення 15612: R-PRN-04 — опора (ГГ-1), а не зауваження hint. Чи доходить «мікс тримається на цьому, лишити» до
запиту стилістки тим шляхом, яким доходить опора K-ACC-01 (`від_моделі` → `опори` → `keep` промпту ремонту), без моделі.
Образи: верх × низ стенда (`стенд_вх.json`) — різні сім'ї мотиву тієї самої форми (`ФОРМА_МОТИВУ`), по дві речі на сім'ю,
+ однотонне взуття; порівняння — образ, де K-ACC-01 виходить опорою. Аргумент — корінь дерева (ДО чи ПІСЛЯ)."""
import collections, itertools, json, os, pathlib, sys


def main():
    """Лічити R-PRN-04 у знахідках, в опорах і в `keep` / `findings` промпту ремонту."""
    джерела = pathlib.Path(sys.argv[1]).resolve() / 'джерела'
    sys.path.insert(0, str(джерела)); os.chdir(джерела)
    import bridge as B, колір_принти as К
    assert pathlib.Path(К.__file__).resolve().parent == джерела, К.__file__
    вх = json.load(open('стенд_вх.json', encoding='utf-8'))
    B.виклик('запити', json.dumps(вх, ensure_ascii=False)); кат = B.каталог_останнього_пакета()
    сім = collections.defaultdict(list)
    for о in кат:
        if о.get('слот') in ('верх', 'низ') and о.get('візерунок') in К.ФОРМА_МОТИВУ:
            сім[о['слот'], о['візерунок']].append(о['id'])
    взуття = next(о['id'] for о in кат if о.get('слот') == 'взуття' and о.get('візерунок') in (None, 'solid'))
    образи = [('R-PRN-04', [в, н, взуття])
              for (с1, ф1), (с2, ф2) in itertools.product(sorted(сім), sorted(сім))
              if (с1, с2) == ('верх', 'низ') and ф1 != ф2 and К.ФОРМА_МОТИВУ[ф1] == К.ФОРМА_МОТИВУ[ф2]
              for в, н in itertools.product(сім[с1, ф1][:2], сім[с2, ф2][:2])]
    образи.append(('K-ACC-01', ['ж-00011@twice.com.ua', 'ж-07785@cultboutique.com.ua', взуття]))
    код = dict(zip(('R-PRN-04', 'K-ACC-01'), ('print_shapes_echo_keep', 'accessory_echoes_accent')))
    Л = collections.Counter()
    for правило, ід in образи:
        в = json.loads(B.виклик('від_моделі', json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
        о = в['вердикт']['образи'][0]; пр = json.loads(в['промпт_ремонту'])['verdict'][0]
        коди = lambda поле: [с.get('code') for x in пр.get(поле) or [] for с in x.get('statements') or []]
        зн = [z for z in о.get('знахідки') or [] if z.get('правило') == правило]
        оп = [z for z in о.get('опори') or [] if z.get('правило') == правило]
        Л[правило, 'образів'] += 1
        Л[правило, 'у знахідках'] += len(зн)
        Л[правило, 'в опорах'] += len(оп)
        Л[правило, 'ненульова вага у знахідках'] += sum(bool(z.get('сила_нп')) for z in зн)
        Л[правило, 'промпт ремонту: у keep'] += коди('keep').count(код[правило])
        Л[правило, 'промпт ремонту: у findings'] += коди('findings').count(код[правило])
    for к, v in sorted(Л.items()):
        print('  %-48s %s' % (' · '.join(к), v))


if __name__ == '__main__':
    main()

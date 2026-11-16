"""Вага знахідок кроку суддів на повному каталозі; другий аргумент — корінь дерева ДО (git worktree)."""
import gzip, json, os, pathlib, sys
ТУТ = pathlib.Path(__file__).resolve().parent
КОРІНЬ = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ТУТ.parents[1]).resolve()
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(ТУТ)]
os.chdir(КОРІНЬ / 'джерела')
import е3_судді_запис as З


def main():
    import feed as Ф, outfit as О, coordination as К, суд_річ as Р, суд_намір as Н, перевірка_образу as П, \
        composer as КМ, fit as ПС, colorspace as cs
    З.обгорнути()
    кеш = pathlib.Path(os.environ.get('TMP', '/tmp')) / 'е3_судді_каталог.json.gz'
    if not кеш.exists():
        with gzip.open(кеш, 'wt', encoding='utf-8') as ф:
            json.dump(Ф.база_прогону(Ф.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог'], ф)
    with gzip.open(кеш, 'rt', encoding='utf-8') as ф:
        кат = [р for р in json.load(ф) if р.get('слот')]
    вето = dict(зони=['декольте', 'спина', 'плечі', 'руки', 'ноги'], ноги_вище_см=45)
    трійки = [кат[і:і + 3] for і in range(0, len(кат) - 2)]
    набір = [м for м in (К.середня_близькість(О.елементи(т)) for т in трійки[::700]) if м is not None]
    for і, р in enumerate(кат):
        З.МІТКА[0] = str(р.get('id'))
        Е = О.елементи([р])
        Р.вето_покриття(Е, вето); Р.тканина_проти_крою(Е)
        Н.намір_комфорту([р], intent='comfort_first')
        if і < len(трійки):
            К.координація(О.елементи(трійки[і]), набір)
    вх, ні = json.load(open('стенд_вх.json', encoding='utf-8')), ['вовна', 'шкіра', 'каблук']
    T = ПС.тіло(float(вх['зріст']), {к: float(в) for к, в in вх['обхвати'].items()})
    F = cs.features(cs.hx(вх['шкіра']), cs.hx(вх['волосся'][0]), cs.hx(вх['очі']))
    ід = {в['id'] for в in П.PR.жорстке_ні_фільтр(кат, ні)[1]}
    for р in [р for р in кат if р['id'] in ід][:300]:
        З.МІТКА[0] = 'ні:' + str(р.get('id'))
        П.перевірити_образ(F, [КМ.у_річ(dict(р), р.get('слот'), T)], тіло=T, жорстке_ні=ні)
    З.записати(sys.argv[1], каталог=len(кат), набір=len(набір))

if __name__ == '__main__':
    main()

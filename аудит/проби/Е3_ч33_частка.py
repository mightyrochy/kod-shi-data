"""Колірні сили на всьому каталозі: кожна річ із базовою трійкою, тіла ч27; без API."""
import sys, pathlib, os, json, contextlib, io
код = pathlib.Path(sys.argv[sys.argv.index('--код') + 1]).resolve() if '--код' in sys.argv else pathlib.Path(__file__).resolve().parents[2] / 'джерела'
os.chdir(код); sys.path.insert(0, str(код))
import feed, composer, outfit, fit, colorspace, суд_огляд
with contextlib.redirect_stdout(io.StringIO()):
    кат = feed.база_прогону(feed.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог']
базові = {с: next(к for к in кат if к['слот'] == с) for с in ('верх', 'низ', 'взуття')}
особа = colorspace.features(colorspace.hx('#deb295'), colorspace.hx('#f1dbaa'), colorspace.hx('#759087'))
правила = {'K-COL-01', 'K-COL-02', 'K-COL-05', 'K-COL-06', 'K-COMP-03', 'K-CLR-02', 'K-CLR-03', 'R-COL-16', 'K-PC-05'}
def знайти(x):
    if isinstance(x, dict):
        if x.get('правило') in правила and 'сила' in x: yield (x['правило'], x['сила'])
        for v in x.values(): yield from знайти(v)
    elif isinstance(x, list):
        for v in x: yield from знайти(v)
print(json.dumps({'каталог': len(кат), 'базові': {с: к['id'] for с, к in базові.items()}}, ensure_ascii=False), flush=True)
for зр in (155, 165, 175):
    тіло = fit.тіло(зр, dict(плечі=98, груди=92, талія=74, стегна=100))
    for к in кат:
        набір = [к] + [б for с, б in базові.items() if с != к['слот'] and б['id'] != к['id']]
        речі = [composer.у_річ(dict(р), р['слот'], тіло) for р in набір]
        with contextlib.redirect_stdout(io.StringIO()):
            outfit.площі_з_геометрії(речі, тіло)
            вих = суд_огляд.review(особа, речі, зріст_см=зр)
        print(json.dumps([зр, к['id'], sorted(set(знайти(вих)))], ensure_ascii=False), flush=True)

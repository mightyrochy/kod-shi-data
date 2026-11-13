"""Спільні поля кольорів кожної речі на повному каталозі; без моделі й API."""
import sys, pathlib, os, collections, contextlib, io, json
код = pathlib.Path(sys.argv[sys.argv.index('--код') + 1]).resolve() if '--код' in sys.argv else pathlib.Path(__file__).resolve().parents[2] / 'джерела'
os.chdir(код); sys.path.insert(0, str(код))
import feed, composer, outfit, fit
with contextlib.redirect_stdout(io.StringIO()):
    база = feed.база_прогону(feed.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)
кат = база['каталог']
print('кандидатів повного каталогу:', len(кат), flush=True)
for зр in (155, 165, 175):
    тіло = fit.тіло(зр, dict(плечі=98, груди=92, талія=74, стегна=100))
    різні, приклади, лік = collections.Counter(), {}, collections.Counter()
    for к in кат:
        річ = composer.у_річ(dict(к), к['слот'], тіло)
        записи = outfit.елементи([річ], стан='надворі')
        лік['речей'] += 1; лік['елементів'] += len(записи)
        if len(записи) < 2: continue
        лік['багатоколірних'] += 1
        for поле in sorted(set().union(*(e.keys() for e in записи))):
            if any(e.get(поле) != записи[0].get(поле) for e in записи[1:]):
                різні[поле] += 1; приклади.setdefault(поле, к['id'])
    print(зр, dict(лік), 'різні поля:', json.dumps(dict(різні), ensure_ascii=False), 'приклади:', json.dumps(приклади, ensure_ascii=False), flush=True)

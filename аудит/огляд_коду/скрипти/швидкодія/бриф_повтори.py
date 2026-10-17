"""Скільки викликів brief.бриф / hypergraph.простір мають однаковий вхід (repr аргументів) на відтворенні."""
import sys, os, json, asyncio, hashlib, collections, time
тека, виклики = sys.argv[1:3]
os.chdir(тека); sys.path.insert(0, тека)
import bridge, brief, hypergraph
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import відтворення
лік = {}
def обгорнути(мод, ім):
    о = getattr(мод, ім); к = collections.Counter(); т = [0.0, 0.0, 0, 0]; перший = {}
    def w(*a, **kw):
        ключ = hashlib.md5(repr((a, sorted(kw.items()))).encode()).hexdigest()
        повтор = ключ in к
        к[ключ] += 1
        t0 = time.perf_counter(); r = о(*a, **kw); dt = time.perf_counter() - t0
        т[0] += dt
        if повтор: т[1] += dt
        хр = hashlib.md5(repr(r).encode()).hexdigest()
        if повтор:
            т[2] += 1; т[3] += (перший[ключ] == хр)
        else: перший[ключ] = хр
        return r
    setattr(мод, ім, w); лік[мод.__name__ + '.' + ім] = (к, т)
обгорнути(brief, 'бриф'); обгорнути(hypergraph, 'простір')
asyncio.run(відтворення.прогнати(виклики))
for ім, (к, т) in лік.items():
    print(ім, 'викликів', sum(к.values()), 'різних входів', len(к), 'час усього %.1f с, з них на повторних входах %.1f с; повторів %d, вихід збігся з першим у %d' % tuple(т))

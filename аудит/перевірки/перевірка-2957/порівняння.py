"""Звести два збережені виводи незміненого приладу й повтор шести відповідей."""
import collections, json, pathlib, re
p=pathlib.Path(__file__).parent
before,after=[json.loads((p/(n+'-довжини.json')).read_text(encoding='utf-8-sig'))['довжини']
              for n in ('base2957','head2957')]
changed={k:[before[k],after[k]] for k in before if before[k]!=after[k]}
assert changed=={'джерела/вибір_палітри.py:ВИБІР':[3447,3414]},changed
result=dict(промптів=[len(before),len(after)],змінені_довжини=changed,суми=[sum(before.values()),sum(after.values())])
for label in ('base2957','head2957'):
    text=(p/(label+'-прилад.txt')).read_text(encoding='utf-8')
    counts=collections.Counter(re.findall(r'^.*? · пункт (\d) ·',text,re.M))
    total=int(re.search(r'^місць: (\d+)$',text,re.M).group(1))
    result[label]=dict(місць=total,пункти=dict(sorted(counts.items())))
replay=json.loads((p/'повтор_палітри.json').read_text(encoding='utf-8'))
result['повтор']=dict(записів=replay['записів'],довжини=[x['довжини'] for x in replay['результати']],
                       однакових=sum(x['читач_однаковий'] for x in replay['результати']))
print(json.dumps(result,ensure_ascii=False,indent=2))

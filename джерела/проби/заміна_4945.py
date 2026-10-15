"""Справжній міст і каталог, SYNTHETIC лише відповіді моделі; три способи одного слота."""
import copy, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import bridge, feed


def проба():
    """Перевіряє спільний добір і цілий незмінний образ у кожному запиті заміни."""
    вх = json.load(open('стенд_вх.json'))
    вх['каталог'] = feed.каталог_на_диску(вх['каталог'])
    json.loads(bridge.виклик('запити', вх))
    пак = list(bridge._КЕШ_ПАКЕТА.values())[0]
    речі = [dict(пак['кандидати'][с][0], слот=с) for с in ('верх', 'низ', 'взуття', 'сумка')]
    for спосіб in ('list', 'assess', 'tournament'):
        з = dict(ід=речі[2]['id'], слот='взуття', речі=copy.deepcopy(речі), спосіб=спосіб, запит='synthetic4945')
        стан, викликів = з, 0
        for _ in range(6):
            р = json.loads(bridge.виклик('від_моделі', dict(вх, рука='1', заміна=стан, не_ця=[з['ід']])))['заміна']
            if р.get('готово'): break
            відповіді = []
            for зап in р['запити']:
                д = json.loads(зап['текст']); викликів += 1
                assert len(д['replacement']['fixed_outfit']) == 3
                assert 'not as part of an outfit' not in str(д['task'])
                а = ({'version':'1', 'ratings':{x['n']:'fits' for xs in д['items'].values() for x in xs}} if 'items' in д else
                     {'version':'1', 'winners':{г:[x['n'] for x in xs[:2]] for г,xs in д['groups'].items()}} if 'groups' in д else
                     {'version':'1', 'outfits':[{'id':'o1', 'items':[д['pool'][0]['n']]}]})
                відповіді.append(dict(ключ=зап['ключ'], текст=json.dumps(а)))
            стан = dict(з, текст=відповіді[0]['текст']) if any(п['ключ']=='replace' for п in р['запити']) else dict(з, стан=р['стан'], відповіді=відповіді)
        assert р['річ']['id'] != з['ід'] and р['річ']['слот'] == 'взуття' and з['речі'] == речі
        print(спосіб, 'same_slot/fixed_outfit', 'calls', викликів)


if __name__ == '__main__':
    проба()

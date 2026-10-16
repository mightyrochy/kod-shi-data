"""Рядок 6616: replay форм записаних відповідей заміни (сцена 4 ж1_робота): список з одного номера, `worn` false, ок."""
import copy, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import bridge, feed

СПИСОК = lambda носить: json.dumps({"is_outfit": "yes", "items": [dict(name="Black ankle boots with a block heel",
    details="leather, round toe", slot="shoes", color_hex="#202020", own=None, worn=носить)]})


def рука(вх, речі, ід, номер, відповіді):
    """Цикл показу: до 6 раундів; → (нова річ, промпти моделі). `відповіді` — що модель скаже на 1-й і 2-й виклик."""
    з = dict(ід=ід, слот='взуття', речі=copy.deepcopy(речі), спосіб='list', запит='replay6616')
    стан, промпти = з, []
    for _ in range(6):
        р = json.loads(bridge.виклик('від_моделі', dict(вх, рука=номер, заміна=стан, не_ця=[ід])))['заміна']
        if р.get('готово'): return р.get('річ'), промпти
        зап = р['запити'][0]; промпти.append(зап['текст'])
        текст = відповіді[min(len(промпти), len(відповіді)) - 1]
        текст = текст(промпти[0]) if callable(текст) else текст
        стан = dict(з, текст=текст) if зап['ключ'] == 'replace' else dict(з, стан=р.get('стан'), відповіді=[dict(ключ=зап['ключ'], текст=текст)])
    return None, промпти


def проба():
    вх = json.load(open('стенд_вх.json'))
    вх['каталог'] = feed.каталог_на_диску(вх['каталог'])
    json.loads(bridge.виклик('запити', вх))
    пак = list(bridge._КЕШ_ПАКЕТА.values())[0]
    речі = [dict(пак['кандидати'][с][0], слот=с) for с in ('верх', 'низ', 'взуття', 'сумка')]
    ід = речі[2]['id']
    перший_номер = lambda промпт: json.dumps([json.loads(промпт)['pool']['rows'][0][0]])
    for номер, відп in (('1', [перший_номер]), ('2', [перший_номер]), ('3', [СПИСОК(False), СПИСОК(True)]), ('4', [СПИСОК(True)])):
        річ, п = рука(вх, речі, ід, номер, відп)
        print('рука', номер, 'нова річ:', 'так' if річ else 'ні', '· викликів моделі:', len(п),
              '· format_error на повторі:', len(п) > 1 and 'format_error' in п[1] and 'format_error' not in п[0])


if __name__ == '__main__':
    проба()

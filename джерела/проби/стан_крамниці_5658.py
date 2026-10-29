"""5658/5622: факти поточного реєстру й каталогу, без мережі та зміни дозволів."""
import collections
import pathlib
import sys

КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / 'zhnyvarka'))
from стани_крамниць import знімок


def main():
    """Показує коди саме тих крамниць, які досі увімкнені й мають нуль речей."""
    стани = знімок(КОРІНЬ / 'каталог_повний.xml.gz', КОРІНЬ / 'zhnyvarka/магазини.tsv')
    нулі = [с for с in стани if с['дозвіл'] == 'увімкнено' and not с['речей']]
    print('увімкнено, 0 речей:', len(нулі))
    print('стани:', dict(collections.Counter(с['стан_код'] for с in нулі)))
    print('причини:', dict(collections.Counter(с['причина_код'] for с in нулі)))
    for с in нулі:
        print(с['домен'], с['речей'], с['стан_код'], с['причина_код'], с['доступ_код'])
    return int(any(с['стан_код'] != 'WAIT' for с in нулі))


if __name__ == '__main__':
    sys.exit(main())

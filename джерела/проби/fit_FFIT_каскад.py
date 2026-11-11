"""Друкує категорії FFIT 2020, межі й залежність від виміру високого стегна."""
import os, sys
from decimal import Decimal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from body_shape import визначення


def мірка(г, т, с, в=None):
    """Переводить точні дюймові фікстури в сантиметри входу продукту."""
    return {к: str(Decimal(str(з)) * Decimal('2.54')) for к, з in
            zip(('груди', 'талія', 'стегна', 'високе_стегно'), (г, т, с, в)) if з is not None}


if __name__ == '__main__':
    випадки = [((36, 27, 36, 30), 'Hourglass', True),
               ((36, 27, 40, 30), 'Bottom Hourglass', True),
               ((38, 29, 36, 32), 'Top Hourglass', True),
               ((36, 30, 39, 36), 'Spoon', True),
               ((36, 33, 40, 35), 'Triangle', False),
               ((40, 34, 36, 35), 'Inverted Triangle', False),
               ((36, 30, 36, 32), 'Rectangle', False),
               ((36, 40, 38, 39), 'Diamond', False),
               ((40, 39, 38, 39), 'Oval', False),
               ((36, 27.001, 36, 30), 'Rectangle', False),
               ((36, 30, 39.6, 30), 'Bottom Hourglass', True),
               ((36, 30, 39.599, 30), 'Rectangle', False),
               ((36, 30, 40, 35.79), 'Spoon', True),
               ((36, 30, 40, 35.78999), 'Bottom Hourglass', True),
               ((36, 40, 40, 35), 'Triangle', False),
               ((36, 40.001, 40, 35), 'Diamond', False),
               ((36, 30, 40), None, True),  # Bottom Hourglass / Spoon: стан спільний
               ((36, 32, 40), None, None),  # Spoon / Triangle
               ((36, 30, 39), None, None),  # Spoon / Rectangle
               ((36, 32, 35), 'Rectangle', False),
               ((50, 20, 30, 25), None, None)]
    for вхід, категорія, стан in випадки:
        вих = визначення(**мірка(*вхід), похибка=lambda в: 0)
        assert вих['категорія'] == категорія and вих['талія'] is стан, (вхід, вих)
        print(вхід, '→', вих)

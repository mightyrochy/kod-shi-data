"""Сліпі квадрати сім’ї очей: тільки №/Очі/Річ, жодних кодових вердиктів.
python проби/сімя_очей_аркуші_958.py склад.json зовнішня-тека
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def записати_аркуші():
    """Пише 5 сліпих аркушів; перевіряє 80 заливок за окремим складом."""
    пари = json.loads(Path(sys.argv[1]).read_text())["пари"]
    assert len(пари) == 40
    вихід = Path(sys.argv[2]); вихід.mkdir(parents=True, exist_ok=True)
    шрифт = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    for сторінка in range(5):
        ім = Image.new('RGB', (1180, 1160), 'white'); мал = ImageDraw.Draw(ім)
        мал.text((34, 15), f'Пари {сторінка * 8 + 1}–{сторінка * 8 + 8}', font=шрифт, fill='black')
        for j, р in enumerate(пари[сторінка * 8:(сторінка + 1) * 8]):
            y = 70 + j * 133
            мал.text((34, y + 37), str(сторінка * 8 + j + 1), font=шрифт, fill='black')
            for x, підпис, ключ in [(190, 'Очі', 'очі'), (490, 'Річ', 'hex')]:
                мал.text((x, y), підпис, font=шрифт, fill='black')
                мал.rectangle((x, y + 32, x + 200, y + 114), fill=р[ключ], outline='black')
                rgb = tuple(bytes.fromhex(р[ключ][1:]))
                assert ім.crop((x + 1, y + 33, x + 200, y + 114)).getcolors() == [(199 * 81, rgb)]
        ім.save(вихід / f'сімя_очей_2_{сторінка + 1}.png')
    print('5 сліпих PNG; усі 80 заливок збігаються з hex окремого JSON')
if __name__ == '__main__':
    записати_аркуші()

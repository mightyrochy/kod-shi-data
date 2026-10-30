"""Відтворює незмінені шість входів проб перевірки #2318 на поточному приладі."""
from pathlib import Path
import sys, runpy, tempfile, json

def main():
    """Друкує результат кожного входу й повертає ненульовий код при розбіжності."""
    корінь = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    sys.path.insert(0, str(корінь / 'джерела/прилади'))
    прилад = runpy.run_path(str(корінь / 'джерела/прилади/корінь_е2_текст_жінці.py'), run_name='звірка')
    випадки = {'обгортка-входу': "function ф(дані){ елНазваП('b', null, String(дані.схема).replace(/_/g, ' ')); }", 'ті-самі-дані-прямо': "function ф(дані){ назваЖінціП(document.body, String(дані.схема).replace(/_/g, ' ')); }", 'її-слова-зі-сталим-написом': "function ф(файл){ їїСловаП(document.body, файл.name + ' · показано локально, нікуди не вантажиться'); }", 'її-слова-з-назви-моделі': "async function ф(){ const дані = await (await fetch('/model')).json(); їїСловаП(document.body, дані.назва); }", 'її-слова-з-тексту-моделі': "async function ф(){ const дані = await (await fetch('/model')).json(); їїСловаП(document.body, дані.текст); }", 'вузли-childNodes': "function рендер(){ fetch('/model'); const вузол = document.createElement('div'); текстЖінціП(вузол, 'Перевірений текст'); return вузол; } function ф(){ document.body.replaceChildren(...рендер().childNodes); }"}
    збої = 0
    with tempfile.TemporaryDirectory() as адреса:
        тека = Path(адреса)
        (тека / 'показ').mkdir()
        (тека / 'показ.html').write_text('<html></html>', encoding='utf-8')
        (тека / 'показ/мовний_шар.js').write_text("function назваЖінціП(е, т){ е.textContent = т; } function їїСловаП(е, т){ е.textContent = т; } function елНазваП(тег, клас, т){ const е = document.createElement(тег); назваЖінціП(е, т); return е; }", encoding='utf-8')
        for назва, код in випадки.items():
            (тека / 'показ/проба.js').write_text(код, encoding='utf-8')
            програма, стоки, _, _, _ = прилад['обчислити'](str(тека))
            зовнішні = [с for с in стоки if not с.обгортка]
            кількість = sum(прилад['є_місцем'](с) for с in зовнішні)
            очікується = 0 if назва == 'вузли-childNodes' else 1
            збої += кількість != очікується
            print(назва + ': ' + json.dumps({'місць': кількість, 'очікується': очікується, 'Б_усі_стоки': len(прилад['шлях_б'](програма, зовнішні)[0])}, ensure_ascii=False))
    print('хиб: ' + str(збої))
    return int(bool(збої))

if __name__ == "__main__":
    sys.exit(main())

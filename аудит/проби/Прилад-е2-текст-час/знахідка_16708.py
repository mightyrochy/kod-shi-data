"""Відтворює зайве місце після JSON-клону параметра без зміни приладу."""
import importlib.util
from pathlib import Path
import sys
import tempfile


def main():
    """Зіставляє її слова напряму та після клонування того самого запису."""
    шлях = Path(sys.argv[1] if len(sys.argv) > 1 else 'джерела/прилади/корінь_е2_текст_жінці.py').resolve()
    sys.path.insert(0, str(шлях.parent))
    специфікація = importlib.util.spec_from_file_location('прилад_знахідки', шлях)
    к = importlib.util.module_from_spec(специфікація)
    специфікація.loader.exec_module(к)
    спільне = '''
    let П = {};
    function зібрати(вхід){ П = {текст: вхід.value}; }
    function копія(запис){ return JSON.parse(JSON.stringify(запис)); }
    зібрати(document.querySelector('input'));
    '''
    with tempfile.TemporaryDirectory() as тека:
        корінь = Path(тека)
        (корінь / 'показ').mkdir()
        (корінь / 'показ.html').write_text('<input>', encoding='utf-8')
        for назва, значення in [('напряму', 'П'), ('клон параметра', 'копія(П)')]:
            (корінь / 'показ' / 'проба.js').write_text(
                спільне + 'document.body.textContent = ' + значення + '.текст;', encoding='utf-8')
            _, стоки, *_ = к.обчислити(тека, ())
            місць = sum(к.є_місцем(с) for с in стоки if not с.обгортка)
            print('%s: місць %d; походження %s' % (назва, місць, [sorted(с.джерела) for с in стоки]))


if __name__ == '__main__':
    main()

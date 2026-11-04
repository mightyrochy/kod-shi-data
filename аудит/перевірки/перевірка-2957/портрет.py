"""Повтори вимог у справжньому промпті портрета; фото й модель не викликаються."""
import pathlib, sys
src = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(src))
import міст_вхід as В
text = В.промпт_кольору()
print('джерело: 6028f963a49c8a9d2c274385fb85699652b393e4:джерела/міст_вхід.py')
print('промпт, символів:', len(text))
for phrase in ('cheek, forehead, jaw', 'largest'):
    n = text.count(phrase)
    print(repr(phrase), 'входжень:', n)
    assert n == 2
print(text)

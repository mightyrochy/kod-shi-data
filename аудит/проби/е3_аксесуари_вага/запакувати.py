"""Стиснути завершені журнали без зміни їхнього вмісту; запускати після вимірів."""
import gzip
from pathlib import Path


def main():
    """Зберегти точні байти журналів у gzip, перевірити їх і прибрати сирі копії."""
    тека = Path(__file__).resolve().parent
    кількість = 0
    for шлях in тека.rglob('*.log'):
        assert шлях.resolve().is_relative_to(тека)
        байти = шлях.read_bytes()
        архів = шлях.with_suffix('.log.gz')
        архів.write_bytes(gzip.compress(байти, mtime=0))
        assert gzip.decompress(архів.read_bytes()) == байти
        шлях.unlink()
        кількість += 1
    print('Стиснуто журналів без зміни байтів:', кількість)


if __name__ == '__main__':
    main()

"""Перевіряє SHA-256 архіву після оновлення файла й при читанні двох архівів одночасно."""
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from фід_каталог import sha_архіву


def main():
    """Створює два різні файли, звіряє хеші після конкурентних читань, а потім після заміни."""
    with TemporaryDirectory() as тека:
        архіви = [Path(тека) / ім for ім in ("один.gz", "два.gz")]
        дані = [b"a" * (2 ** 21), b"b" * (2 ** 21)]
        for шлях, вміст in zip(архіви, дані):
            шлях.write_bytes(вміст)
        очікувані = [hashlib.sha256(вміст).hexdigest() for вміст in дані]
        with ThreadPoolExecutor(max_workers=2) as потоки:
            assert list(потоки.map(sha_архіву, архіви * 8)) == очікувані * 8
        оновлено = "оновлено".encode()
        архіви[0].write_bytes(оновлено)
        assert sha_архіву(архіви[0]) == hashlib.sha256(оновлено).hexdigest()
    print("SHA-256: паралельні читання і заміна архіву — гаразд")


if __name__ == "__main__":
    main()

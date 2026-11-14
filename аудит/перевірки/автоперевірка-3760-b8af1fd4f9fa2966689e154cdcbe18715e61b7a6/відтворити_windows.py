"""Запускає авторське відтворення з UTF-8 шляхами tar і дочірнього Python на Windows.

Аргументи: дерево перевірюваного PR, абсолютна тимчасова тека.
Формули й добір даних авторського скрипта не змінює.
"""
import importlib.util, io, pathlib, subprocess, sys, tarfile
sys.stdout.reconfigure(encoding="utf-8")
дерево_PR, тимчасова = (pathlib.Path(p).resolve() for p in sys.argv[1:3])
шлях = дерево_PR / "аудит/проби/річ_колір_один_колір_1411/відтворити.py"
специфікація = importlib.util.spec_from_file_location("проба_3760", шлях)
модуль = importlib.util.module_from_spec(специфікація)
специфікація.loader.exec_module(модуль)


def розпакувати(sha, тека):
    """Розпаковує ті самі байти git archive зі збереженням кириличних імен."""
    тека.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(модуль.git("archive", sha, "джерела")), encoding="utf-8") as архів:
        архів.extractall(тека, filter="data")
    return тека / "джерела"


запуск = subprocess.run
def utf8_запуск(аргументи, **параметри):
    """Залишає -I та додає явний UTF-8 лише дочірньому Python."""
    if аргументи[0] == sys.executable:
        аргументи = [аргументи[0], "-X", "utf8", *аргументи[1:]]
    return запуск(аргументи, **параметри)


if __name__ == "__main__":
    модуль.дерево = розпакувати
    subprocess.run = utf8_запуск
    sys.argv = [str(шлях), str(тимчасова)]
    модуль.main()

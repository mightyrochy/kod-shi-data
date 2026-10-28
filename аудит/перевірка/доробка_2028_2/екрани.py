"""Знімає дані справжнього моста для п'яти сцен 2.14 і відтворення вади.

python аудит/перевірка/доробка_2028_2/екрани.py <дерево> <вихід.json.gz>
"""
import gzip
import importlib.util
import json
import pathlib
import sys


def головна():
    """Зберігає шість екранів у кожній гамі, не підмінюючи даних пакета."""
    корінь = pathlib.Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(корінь / "джерела"))
    мод = importlib.util.spec_from_file_location("вимір_9858", корінь / "аудит/проби/кольори_9858.py")
    в = importlib.util.module_from_spec(мод)
    мод.loader.exec_module(в)
    попередні = json.loads(gzip.decompress((корінь / "аудит/перевірка/доробка_2028/екрани.json.gz").read_bytes()))
    сцени = [dict(сцена=з["сцена"], вхід=з["вхід"]) for з in попередні if з["сцена"].startswith("ж")]
    сцени.append(dict(сцена="відтворення", вхід=dict(шкіра=["#bb8561"], очі="#765336", волосся=["#70503b"],
                                                   обхвати={}, зріст=168, самозвіт=dict(метал="срібло"))))
    записи = []
    for сцена in сцени:
        for гама in ("середні", "приглушені", "насичені"):
            вхід = dict(сцена["вхід"], вибір_кольору=dict(насиченість=гама))
            р = в.зняти(вхід)
            записи.append(dict(сцена=сцена["сцена"] + "-" + гама, вхід=вхід, екран=р["екран"]))
    pathlib.Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(записи, ensure_ascii=False).encode(), mtime=0))
    print(f"Екранів: {len(записи)}", flush=True)


if __name__ == "__main__":
    головна()

"""Незалежна перевірка точної голови #2029; без моделей і платних API."""
import collections
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def записати(шлях, дані):
    """Зберегти відтворюваний результат у UTF-8."""
    Path(шлях).write_text(json.dumps(дані, ensure_ascii=False, indent=2), encoding="utf-8")


def головна():
    """Зняти каталог, перевірити межі або виконати батарею й сусідні проби."""
    режим, дерево, вихід = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    вихід.mkdir(parents=True, exist_ok=True)
    код = дерево / "джерела"
    os.chdir(код)
    sys.path.insert(0, str(код))
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(код / "node_modules"))
    if режим in ("каталог", "сегменти"):
        import feed
        import фід_каталог as ФК
        import колір_річ as КР
        import композитор_річ as КП
        import outfit as О
        import colorspace as КС
        знімок = (ФК.прочитати_каталог(feed.каталог_на_диску(), 0) if режим == "каталог" else
                  json.loads(Path(sys.argv[4]).read_text(encoding="utf-8")))
        if режим == "каталог":
            записати(вихід / "каталог.json", знімок)
        кат = знімок["каталог"]
        факти = dict(записів=len(кат), типи=dict(collections.Counter(КР.тип_кольору(р) for р in кат))
                     if hasattr(КР, "тип_кольору") else {}, сегментів=0, втрат=0, спотворень=0, максимум=0,
                     без_точки=0, без_меж=0)
        спотворені_речі = set()
        for р in кат:
            факти["без_точки"] += КР.точка_кольору(р) is None
            факти["без_меж"] += КР.межі_кольору(р) is None
            if not р.get("colors") or р.get("слот") == "верхній_шар":
                continue
            ел = О.елементи([КП.у_річ(р, р["слот"], {})])
            assert len(ел) == len(р["colors"])
            for с, е in zip(р["colors"], ел):
                т, о = КР.точка_кольору(с), КР.точка_кольору(е)
                if т is not None:
                    факти["сегментів"] += 1
                    факти["втрат"] += о is None
                    if о is not None:
                        d = КС.de00(т, о)
                        факти["спотворень"] += d > 1
                        if d > 1:
                            спотворені_речі.add(р["id"])
                        факти["максимум"] = max(факти["максимум"], d)
                else:
                    assert о is None
        факти["спотворених_речей"] = len(спотворені_речі)
        записати(вихід / "каталог-підсумок.json", факти)
        print(json.dumps(факти, ensure_ascii=False), flush=True)
        return 0
    if режим == "регресії":
        прилад = Path(sys.argv[4]).resolve()
        зведення = []
        for ім in ("два", "невідомо", "полюс"):
            команда = [sys.executable, str(прилад), str(дерево), ім]
            р = subprocess.run(команда, cwd=код, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (вихід / (ім + ".txt")).write_bytes(р.stdout)
            зведення.append(dict(команда=команда, код=р.returncode,
                                 вивід=р.stdout.decode("utf-8", errors="replace")))
        записати(вихід / "регресії.json", зведення)
        print(json.dumps(зведення, ensure_ascii=False), flush=True)
        return int(any(р["код"] for р in зведення))
    if режим == "межі":
        import колір_річ as КР
        import фід_збагачення as ФЗ
        import verify as В
        import композитор_слоти as С
        import суд_від_моделі as М
        результати = []
        for слово in ("золотий", "бежевий", "синій", "червоний"):
            if слово not in В.ЛЕКСИКОН:
                continue
            р = dict(id=слово, слот="прикраси", назва=слово, lab=None, колір_тип="інтервал",
                     колір_не_вимір=ФЗ.не_вимір_кольору(В.ЛЕКСИКОН[слово], слово, "shop_word"),
                     _вікно={"менш_ходове": True})
            for назва, виклик in (("нота_золота", lambda: С._нота_рідшого_золота([р], None)),
                                  ("бюджет_відлуння", lambda: М.бюджет_і_відлуння([р]))):
                try:
                    відповідь = виклик()
                    результати.append(dict(слово=слово, проба=назва, результат=відповідь))
                except Exception:
                    результати.append(dict(слово=слово, проба=назва, помилка=traceback.format_exc()))
        записати(вихід / "межі.json", результати)
        print(json.dumps([dict(слово=р["слово"], проба=р["проба"],
                              результат="помилка" if "помилка" in р else "відповідь")
                          for р in результати], ensure_ascii=False), flush=True)
        return 0
    if режим == "метал":
        import колір_річ as КР
        import palettes as П
        import суд_від_моделі as С
        кат = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))["каталог"]
        результати = []
        for р in кат:
            if not р.get("метал") or not П.колір_металу(р) or КР.точка_кольору(р) is not None:
                continue
            зн = С.бюджет_і_відлуння([р])
            результати.append(dict(id=р["id"], слот=р.get("слот"), тип=р.get("тип"),
                                  метал=р["метал"], lab=р.get("lab"),
                                  колір_металу=П.колір_металу(р),
                                  знахідки=[{к: з.get(к) for к in ("правило", "ярлик", "суть")} for з in зн]))
        записати(вихід / "метал.json", результати)
        print(json.dumps(dict(металів_без_точки=len(результати),
                              хибні_акценти=sum(any(з["ярлик"] == "orphan_accent" for з in р["знахідки"])
                                               for р in результати),
                              приклад=next(р for р in результати if р["id"] == "ж-07553@brenda.ua")),
                         ensure_ascii=False), flush=True)
        return 0
    if режим == "одна":
        ім = Path(sys.argv[4]).stem
        команда = [sys.executable, str(код / "проби" / sys.argv[4]), *sys.argv[5:]]
        with (вихід / (ім + ".txt")).open("wb") as журнал:
            к = subprocess.run(команда, cwd=код, stdout=журнал, stderr=subprocess.STDOUT).returncode
        р = dict(назва=ім, команда=команда, код=к)
        записати(вихід / (ім + ".json"), р)
        print(json.dumps(р, ensure_ascii=False), flush=True)
        return к
    if режим == "погода":
        кат = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))["каталог"]
        вхід = вихід / "каталог-рядки.json"
        записати(вхід, кат)
        результати = []
        for ім in ("wea_вхід", "wea_канон", "wea_спека"):
            команда = [sys.executable, str(код / "проби" / (ім + ".py")), str(код)]
            if ім != "wea_вхід":
                команда.append(str(вхід))
            with (вихід / (ім + ".txt")).open("wb") as журнал:
                к = subprocess.run(команда, cwd=код, stdout=журнал, stderr=subprocess.STDOUT).returncode
            результати.append(dict(назва=ім, команда=команда, код=к))
            print(ім, "код", к, flush=True)
        записати(вихід / "результати.json", результати)
        return int(any(р["код"] for р in результати))
    if режим == "історичні":
        os.environ.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.quotepath", GIT_CONFIG_VALUE_0="false")
        вхід = дерево / "аудит/тести/власник_2026-10-14/verdykty-0phxvk-2026-10-14-1551.json"
        теки = sorted({str(п.parent) for п in (дерево / "аудит").rglob("*проза_рука_3_4.txt")})
        assert вхід.is_file() and теки
        print("Історичний JSON знайдено; тек прози:", len(теки), flush=True)
        команди = [(ім, [str(вхід)]) for ім in ("колір_кадр_слово_5222", "колір_кадр_слово_5223")]
        команди += [(ім, теки) for ім in ("колір_названо", "колір_прози_шар")]
        команди.append(("колір_ярлик_hex", ["HEAD:аудит"]))
        результати = []
        for ім, арг in команди:
            команда = [sys.executable, str(код / "проби" / (ім + ".py")), *арг]
            with (вихід / (ім + ".txt")).open("wb") as журнал:
                к = subprocess.run(команда, cwd=дерево if ім == "колір_ярлик_hex" else код,
                                   stdout=журнал, stderr=subprocess.STDOUT).returncode
            результати.append(dict(назва=ім, команда=команда, код=к))
            print(ім, "код", к, flush=True)
        записати(вихід / "результати.json", результати)
        return int(any(р["код"] for р in результати))
    if режим in ("батарея", "проби"):
        результати = []

        def запуск(назва, команда):
            поч = time.monotonic()
            with (вихід / (назва + ".txt")).open("wb") as журнал:
                к = subprocess.run(команда, cwd=код, stdout=журнал, stderr=subprocess.STDOUT).returncode
            р = dict(назва=назва, команда=команда, код=к, секунд=round(time.monotonic() - поч, 2))
            print(json.dumps(р, ensure_ascii=False), flush=True)
            return р

        батарея = (("дим", ["стенд_знімок.py", "--дим"]),
                        ("живий_шлях", ["тест_живого_шляху.py"]),
                        ("протокол", ["тест_протоколу.py"]),
                        ("розділи", ["прилади/розділи_гейтів.py"]),
                        ("контракти", ["audit_contracts.py"]))
        if режим == "батарея":
            for ім, арг in батарея:
                результати.append(запуск(ім, [sys.executable, *арг]))
            результати.append(запуск("показ", ["node", "тест_показу.js"]))
        виключені = {"pal_вердикт.py", "pal_вимір.py", "колір_спільне.py", "колір_нейтраль.py",
                     "колір_весь_кадр_5286.py", "колір_кадр_слово_5222.py", "колір_кадр_слово_5223.py",
                     "колір_названо.py", "колір_прози_шар.py", "колір_ярлик_hex.py",
                     "колір_hex_вікна.py", "колір_майже_нейтраль.py",
                     "wea_вхід.py", "wea_канон.py", "wea_спека.py"}
        проби = sorted({п for пр in ("колір_", "pal_", "wea_", "поділ_")
                        for п in (код / "проби").glob(пр + "*.py")
                        if п.name not in виключені and (пр != "поділ_" or п.stem.endswith("_ast"))})
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(sys.argv[4]) if len(sys.argv) > 4 else 3) as пул:
            запити = [пул.submit(запуск, п.stem, [sys.executable, str(п)]) for п in проби]
            for запит in concurrent.futures.as_completed(запити):
                результати.append(запит.result())
                записати(вихід / "результати.json", результати)
        for ім in ("колір_hex_вікна.py", "колір_майже_нейтраль.py"):
            результати.append(запуск(Path(ім).stem, [sys.executable, "проби/" + ім]))
        записати(вихід / "результати.json", результати)
        return int(any(р["код"] for р in результати))
    raise ValueError(режим)


if __name__ == "__main__":
    raise SystemExit(головна())

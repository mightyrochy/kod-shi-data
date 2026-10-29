"""Відтворює храповик на історичних головах і перевіряє свіжий запис концерту.

Вжиток: python відтворити.py <тека доказів> <підготовка | назва виміру>.
Середовище: NODE_PATH, LYUSTERKO_PYC_PYTHON, REPLAY_CACHE; лише відповіді з диска.
"""
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import zipfile

КОРІНЬ = Path(__file__).resolve().parents[3]
СТАРИЙ = "366461f0bf27787aac337dea6c7b09ed9a2723db"
СВІЖИЙ = "e4edc5ef207e1b84428afaaf8ae8bc94a59afa53"
АВТО = "fcb3fb5863bc6025928b27a5cefac43d19bc0b19"
СЦЕНА = "б1_концерт_стримано"
ЗАПИС = "аудит/проби/нічні/20261027/" + СЦЕНА
НОВИЙ = "аудит/проби/автоживий-e3720b4ae15003b2ce1da152340eb192a1bc32d0/" + СЦЕНА
ВИМІРИ = {
    "2109-голова": "cb29b87f2060e82b305d8d872c58928c5fc3b8a9",
    "2109-база": "ed42a591646e5ccbd187d3d68311c23aeebeaedf",
    "2124-голова": "7ba6aec0605b94de287aa353ae63ced64bd2da7d",
    "2124-база": "f5e10c6650143b6d5965adffeadddc6c5924d9ff",
    "2118-голова": "462ea429392ff81212adc1d56149985b47ccec62",
    "2118-база": "0a5327dda1072b53c076639b59e5ac45b03cbefe",
    "main-старий-запис": СВІЖИЙ,
    "main-новий-запис": СВІЖИЙ,
}


def архів(sha, шлях, тека):
    """Розпаковує лише названий шлях з точної ревізії Git."""
    дані = subprocess.check_output(["git", "archive", "--format=zip", sha, шлях], cwd=КОРІНЬ)
    with zipfile.ZipFile(io.BytesIO(дані)) as арх:
        арх.extractall(тека)


def виконати(докази, назва):
    """Будує точні джерела й запускає стенд із записаним обміном."""
    докази.mkdir(parents=True, exist_ok=True)
    if назва == "підготовка":
        архів(АВТО, НОВИЙ, докази / "авто")
        архів(СТАРИЙ, "аудит/проби/храповик_записів.js", докази / "до")
        архів(СТАРИЙ, "аудит/проби/живий_після_CI.js", докази / "до")
        print("Записи й код ДО отримано з точних SHA", flush=True)
        return
    sha = ВИМІРИ[назва]
    входи = subprocess.check_output(["git", "rev-parse", *[sha + ":" + ш for ш in
        ["джерела", "каталог_повний.xml.gz", "каталог_записи_v1.jsonl.gz", "каталог_маніфест_кадрів.json.gz"]]],
        cwd=КОРІНЬ, text=True).splitlines()
    джерела = докази / "джерела" / sha
    if not джерела.exists():
        архів(sha, "джерела", джерела)
    if not (джерела / "каталог_повний.xml.gz").exists():
        for файл in ["каталог_повний.xml.gz", "каталог_записи_v1.jsonl.gz", "каталог_маніфест_кадрів.json.gz"]:
            архів(sha, файл, джерела)
    збірка = докази / "збірки" / sha
    збірка.mkdir(parents=True, exist_ok=True)
    середовище = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1", LYUSTERKO_CATALOG="повний")
    if not (збірка / "index.html").exists():
        for паспортЗбірки in (докази / "збірки").glob("*/входи.json"):
            if json.loads(паспортЗбірки.read_text(encoding="utf8")) == входи and (паспортЗбірки.parent / "index.html").exists():
                shutil.copyfile(паспортЗбірки.parent / "index.html", збірка / "index.html")
                print(f"{sha}: ідентичні Git-об'єкти джерел і даних; збірка {паспортЗбірки.parent.name}", flush=True)
                break
    (збірка / "входи.json").write_text(json.dumps(входи), encoding="utf8")
    if not (збірка / "index.html").exists():
        print(f"Будую {sha}; журнал {збірка / 'збірка.log'}", flush=True)
        with (збірка / "збірка.log").open("w", encoding="utf8") as лог:
            rc = subprocess.run([sys.executable, str(джерела / "джерела/build_артефакт.py"),
                str(джерела / "джерела"), str(збірка / "index.html"), "показ-повний"],
                cwd=КОРІНЬ, env=середовище, stdout=лог, stderr=лог).returncode
        if rc:
            raise RuntimeError(f"Збірка {sha}: rc={rc}; {збірка / 'збірка.log'}")
    новий = назва == "main-новий-запис"
    сцена = докази / "авто" / НОВИЙ if новий else КОРІНЬ / ЗАПИС
    паспорт = json.loads((сцена / "повтор.json").read_text(encoding="utf8"))
    вихід = докази / назва
    вихід.mkdir(exist_ok=False)
    жінка = вихід / "жінка.json"
    жінка.write_text(json.dumps(паспорт["жінка"], ensure_ascii=False), encoding="utf8")
    # Та сама очистка режимів батька, що у прийманні CI.
    import re
    стенд = КОРІНЬ / "аудит/проби/рв6_стенд.js"
    for змінна in re.findall(r"process\.env\.([A-Z_][A-Z\d_]*)", стенд.read_text(encoding="utf8")):
        if змінна not in ["CHROMIUM", "NODE_PATH", "HTTPS_PROXY"]:
            середовище.pop(змінна, None)
    середовище.update(паспорт["змінні"])
    середовище.update(ZHINKA=str(жінка), ZNIMKY=str(вихід / "знімки"),
        REPLAY_EXCHANGE=str(сцена / ("відповіді/обмін" if новий else "VIDPOVIDI/обмін")))
    команда = ["node", str(стенд), "http://127.0.0.1:8765", str(збірка),
        os.environ["REPLAY_CACHE"], str(паспорт["сід"])]
    print(f"{назва}: {sha}, запис {сцена}", flush=True)
    with (вихід / "лог.txt").open("w", encoding="utf8") as лог:
        rc = subprocess.run(команда, cwd=КОРІНЬ, env=середовище, stdout=лог, stderr=лог,
            timeout=600).returncode
    результат = {"sha": sha, "rc": rc, "команда": команда, "запис": str(сцена)}
    (вихід / "результат.json").write_text(json.dumps(результат, ensure_ascii=False, indent=1), encoding="utf8")
    помилка = вихід / "знімки/помилка_відтворення.json"
    print(json.dumps(результат, ensure_ascii=False), flush=True)
    if помилка.exists():
        дані = json.loads(помилка.read_text(encoding="utf8"))
        print(json.dumps({к: дані.get(к) for к in ["код", "виклик", "причина"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    виконати(Path(sys.argv[1]).resolve(), sys.argv[2])

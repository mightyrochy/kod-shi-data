"""Вимір портрета тим самим кодом, але за РАМКАМИ ЗОН, які дала модель у прогоні (`zones` у її відповіді на читання портрета).
Запуск: PIP_DIR=<…> python3 -I вимір_рамок_моделі.py <файл портрета> <файл відповіді VIDPOVIDI/…кольори_з_портрета.txt>
Друкує стан виміру, причини, шум зон (щока проти щоки, L*) і виміряні Lab. Воріт і порогів не міняє."""
import importlib.util, json, os, sys
ТУТ = os.path.dirname(os.path.abspath(__file__))
сп = importlib.util.spec_from_file_location("вим", os.path.join(ТУТ, "..", "вимір-портрета-1211", "вимір.py"))
В = importlib.util.module_from_spec(сп); сп.loader.exec_module(В)
from PIL import Image
ІМЕНА = {"cheek_left": "щока_ліва", "cheek_right": "щока_права", "forehead": "лоб", "hair": "волосся", "iris_left": "око_ліве", "iris_right": "око_праве"}
def виміряти(портрет, відповідь_файл):
    текст = open(відповідь_файл, encoding="utf-8").read()
    j = json.loads(текст[текст.index("── ВІДПОВІДЬ"):].split("\n", 1)[1].strip())
    зони = {ІМЕНА[к]: dict(ліво=v[0], верх=v[1], право=v[2], низ=v[3]) for к, v in (j.get("zones") or {}).items() if v}
    img = Image.open(портрет).convert("RGB")
    в = В.ПВ.виміряти({ім: В.вирізати(img, р) for ім, р in зони.items()})
    шум = в["шкіра"].get("шум_зон") if isinstance(в.get("шкіра"), dict) else None
    return dict(стан=в["стан"], причини=в["причини"], шум_зон=шум, зони=len(зони),
                lab={к: [round(x, 1) for x in в[к]["lab"]] for к in ("шкіра", "волосся", "очі") if isinstance(в.get(к), dict) and "lab" in в[к]})
if __name__ == "__main__":
    print(json.dumps(виміряти(sys.argv[1], sys.argv[2]), ensure_ascii=False))

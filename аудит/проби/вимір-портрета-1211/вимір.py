"""Мірило 2 наряду Річ-ознаки-обличчя-вимір-портрета: класи з виміру кадру між двома знімками тієї самої людини.
Зони — геометрією від облич і очей Хаара (OpenCV), різ — як `пікселіРечіП` (без поля, ≤64 px, згладжування)."""
import base64, io, json, os, sys
# opencv-python-headless<5 (у 5 нема каскадів Хаара) і Pillow — поза репозиторієм: PIP_DIR=<тека> або в середовищі
if os.environ.get("PIP_DIR"): sys.path.insert(0, os.environ["PIP_DIR"])
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "джерела"))
import cv2, numpy as np
from PIL import Image
import портрет_вимір as ПВ, міст_вхід as МВ, face_features as ОЗ, colorspace as cs
ОБЛ = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
ОКО = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

def зони(img):
    сір = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    H, W = сір.shape
    обл = sorted(ОБЛ.detectMultiScale(сір, 1.1, 5, minSize=(max(60, int(min(W, H) * .10)),) * 2), key=lambda f: -f[2])
    if not len(обл) or (len(обл) > 1 and обл[1][2] > обл[0][2] * .7):
        return None, "облич %d" % len(обл)
    x, y, w, h = обл[0]
    # наближення воріт кадру моделі (`міст_вхід.ЧИТАННЯ_ПОРТРЕТА`, «If the photo is unusable»):
    # обличчя менше чверті кадру й чорно-біле фото модель відкидає до виміру — проба теж, інакше міряла б не портрет
    if w < min(W, H) * .25:
        return None, "обличчя < ¼ кадру"
    лаб = cv2.cvtColor(np.array(img.resize((96, 96))), cv2.COLOR_RGB2LAB).astype(float)
    if np.median(np.hypot(лаб[..., 1] - 128, лаб[..., 2] - 128)) < 4:
        return None, "чорно-біле"
    очі = ОКО.detectMultiScale(сір[y:y + h // 2, x:x + w], 1.05, 4, minSize=(w // 9, w // 9))
    очі = sorted(sorted(очі, key=lambda e: -e[2] * e[3])[:2], key=lambda e: e[0])
    if len(очі) != 2 or очі[1][0] < очі[0][0] + очі[0][2] * .6:
        # окуляри чи дрібне око: очі — геометрією рамки обличчя Хаара (центри на 0.30/0.70 ширини, 0.40 висоти)
        ew = int(w * .26)
        очі = [(int(w * .30 - ew / 2), int(h * .40 - ew / 2), ew, ew), (int(w * .70 - ew / 2), int(h * .40 - ew / 2), ew, ew)]
    т = lambda px, py: (round(px / W * 1000), round(py / H * 1000))
    def рамка(x0, y0, x1, y1):
        л, в = т(x0, y0); п, н = т(x1, y1)
        return {"ліво": max(0, л), "верх": max(0, в), "право": min(1000, п), "низ": min(1000, н)}
    з = {}
    for ім_о, ім_щ, (ex, ey, ew, eh) in (("око_ліве", "щока_ліва", очі[0]), ("око_праве", "щока_права", очі[1])):
        cx, cy, r = x + ex + ew / 2, y + ey + eh / 2, ew * .16
        з[ім_о] = рамка(cx - r, cy - r, cx + r, cy + r)
        з[ім_щ] = рамка(cx - w * .07, y + h * .60, cx + w * .07, y + h * .72)
    з["лоб"] = рамка(x + w * .38, y + h * .07, x + w * .62, y + h * .17)
    з["волосся"] = рамка(x + w * .36, y - h * .20, x + w * .64, y - h * .09)
    if з["волосся"]["верх"] >= з["волосся"]["низ"] - 5:
        return None, "волосся поза кадром"
    return з, None

def вирізати(img, р, сторона=64):
    W, H = img.size
    к = img.crop((round(р["ліво"] / 1000 * W), round(р["верх"] / 1000 * H), round(р["право"] / 1000 * W), round(р["низ"] / 1000 * H)))
    м = min(1, сторона / max(к.size))
    к = к.resize((max(1, round(к.size[0] * м)), max(1, round(к.size[1] * м))), Image.LANCZOS)
    return {"дані": base64.urlsafe_b64encode(к.tobytes()).decode().rstrip("="), "ширина": к.size[0], "висота": к.size[1]}

def заявлені(вим):
    hexx = lambda к: cs.to_hex(*вим[к]["lab"]) if hasattr(cs, "to_hex") else None
    F = МВ.features({"шкіра": ["#808080"], "волосся": ["#808080"], "очі": "#808080", "портрет_вимір": вим})[0]
    кл = ОЗ.класи(F); п = F["_meta"]["вимір_портрета"]["певні"]
    return {к: (кл[к] if п[к] else "не певна") for к in кл}, ОЗ._походження(F)

# опис.json: {"<людина>": [{"файл", "шлях", "ліцензія"}, …]} — фото лише поза репозиторієм (наряд, «Межі»)
ОПИС = sys.argv[1] if len(sys.argv) > 1 else "/tmp/набір/фото/опис.json"
опис = json.load(open(ОПИС))
вих = {}
for людина, фото in опис.items():
    рядки = []
    for ф in фото:
        img = Image.open(ф["шлях"]).convert("RGB")
        з, чому = зони(img)
        if not з:
            рядки.append(dict(файл=ф["файл"], пропуск=чому)); continue
        кадри = {ім: вирізати(img, р) for ім, р in з.items()}
        в1, в2 = ПВ.виміряти(кадри), ПВ.виміряти(кадри)
        р = dict(файл=ф["файл"], ліцензія=ф["ліцензія"], стан=в1["стан"], причини=в1["причини"], повтор_той_самий=в1 == в2,
                 шум_зон=в1["шкіра"].get("шум_зон") if isinstance(в1.get("шкіра"), dict) else None)
        if в1["стан"] == "вимір":
            р["класи"], р["походження"] = заявлені(в1)
            р["lab"] = {к: [round(x, 1) for x in в1[к]["lab"]] for к in ("шкіра", "волосся", "очі")}
        рядки.append(р)
    вих[людина] = рядки
json.dump(вих, open(os.path.join(os.path.dirname(ОПИС), "вимір.json"), "w"), ensure_ascii=False, indent=1)
for л, рр in вих.items():
    вим = [р for р in рр if р.get("стан") == "вимір"]
    print("%-26s фото %2d, облич+очей %2d, вимір %2d, поза воротами %2d" % (л, len(рр), sum("стан" in р for р in рр), len(вим),
          sum(р.get("стан") == "поза_воротами" for р in рр)))

# ── звірка між знімками тієї самої людини: усі пари виміряних кадрів ──
import itertools, math
людей = розбіжних = пар = 0
for л, рр in вих.items():
    вим = [р for р in рр if р.get("стан") == "вимір"]
    if len(вим) < 2:
        continue
    людей += 1
    for а, б in itertools.combinations(вим, 2):
        пар += 1
        ds = [round(б["lab"]["шкіра"][i] - а["lab"]["шкіра"][i], 1) for i in range(3)]
        різні = {к: (а["класи"][к], б["класи"][к]) for к in а["класи"]
                 if "не певна" not in (а["класи"][к], б["класи"][к]) and а["класи"][к] != б["класи"][к]}
        розбіжних += len(різні)
        print("  %-24s Δшкіра L/a/b %s; %s | %s%s" % (л, ds, а["класи"], б["класи"], ("  РОЗБІЖНІ " + str(різні)) if різні else ""))
print("людей з ≥2 виміряними кадрами: %d; пар: %d; розбіжних тверджень: %d" % (людей, пар, розбіжних))
print("повтор того самого кадру однаковий:", all(р.get("повтор_той_самий", True) for рр in вих.values() for р in рр))

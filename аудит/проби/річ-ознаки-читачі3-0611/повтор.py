"""Повтор ж1–ж9 (`model_hex`, `spectro`) і синтетичних облич з невідомою ознакою: осі (позиція, коди, домінанта),
практична палітра (вікна, метал, кольори з силою й знаком-проксі K-PCA-01, найдальші, прийоми), входи чеклістів палітри й їхні стани,
`міст_основи.палітри` — без моделей. Запуск: python3 повтор.py <корінь дерева коду> <вивід.json>"""
import copy, hashlib, json, sys, traceback
from pathlib import Path
К = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(К / "джерела"))
import міст_вхід as М, міст_основи as О, palettes as ПЛ, personal_palette as PP, суд_чеклісти as СЧ


def _спроба(ф):
    try:
        return ф()
    except Exception as e:   # падіння — теж факт виміру: тип і останній кадр
        кадр = traceback.extract_tb(e.__traceback__)[-1]
        return {"ВИНЯТОК": "%s: %s @ %s:%d" % (type(e).__name__, e, Path(кадр.filename).name, кадр.lineno)}


def _зріз(F, вхід=None):
    вих = {}
    ос = _спроба(lambda: ПЛ.осі(F))
    вих["осі"] = ос if "ВИНЯТОК" in ос else {к: ос[к] for к in ("позиція", "коди", "домінанта", "вторинна", "джерело_код")}
    п = _спроба(lambda: ПЛ.палітра_практична(F))
    вих["палітра"] = п if "ВИНЯТОК" in п else dict(
        вікна=dict(L=п["вікна"]["L"], C=п["вікна"]["C"], сімей=len(п["вікна"]["сім_ї"]),
                   сім_ї=hashlib.md5(json.dumps(п["вікна"]["сім_ї"], sort_keys=True).encode()).hexdigest()[:8]),
        метал=п["метал"], найдальші=п["найдальші"]["словами"],
        кольори=[(к["назва"], к["роль"], к["сила"], (к.get("знак_проксі") or {}).get("бік")) for к in п["кольори"]],
        прийоми_активні=[р["прийом"] for р in п["прийоми"] if р["активний"]],
        умови=dict(тримається=п["умови"]["тримається"], зсув=п["умови"]["зсув_підтону"]))
    вих["смуги"] = _спроба(lambda: dict(L=(PP.смуга_світлоти(F) or {}).get("межі"),
                                        rel_C=(PP.смуга_хроми(F) or {}).get("межі"), даних=sorted(PP.дані(F))))
    вп = _спроба(lambda: СЧ.входи_палітри(F))
    if "ВИНЯТОК" in вп:
        вих["чеклісти"] = вп
    else:
        ч = _спроба(lambda: СЧ.чеклісти([], {}, палітра=вп))
        вих["чеклісти"] = dict(бік_температури=вп["бік_температури"], м_яка=вп["м_яка"],
                               вікна=dict(L=вп["вікна"]["L"], C=вп["вікна"]["C"]),
                               не_стосується=вп["не_стосується"],
                               стани=(ч if "ВИНЯТОК" in ч else
                                      [(р.get("пункт"), р.get("стан")) for р in ч.get("палітра") or []]))
    if вхід is not None:
        р = _спроба(lambda: json.loads(О.палітри(json.dumps(вхід, ensure_ascii=False))))
        вих["міст_основи.палітри"] = р if "ВИНЯТОК" in р else dict(
            осі_коди=р.get("осі_коди"), осі_джерело=р.get("осі_джерело"),
            гілки=[(г.get("схема"), г.get("рідший")) for г in р.get("гілки") or []],
            відбиток=hashlib.md5(json.dumps(р.get("гілки"), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10])
    return вих


база = json.loads((К / "джерела/стенд_вх.json").read_text("utf8"))
вихід = {}
for шлях in sorted((К / "аудит/проби/жінки").glob("*.json")):
    ж = json.loads(шлях.read_text("utf8"))
    for дж in ("model_hex", "spectro"):
        вхід = dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=дж)
        F = М.features(copy.deepcopy(вхід))[0]
        вихід["%s/%s" % (шлях.stem, дж)] = _зріз(F, вхід)
# Синтетичні обличчя з невідомою ознакою: вимір `spectro` (протокол є), а риси бракує — її кольору код не знає.
import colorspace as С
ж1 = json.loads((К / "аудит/проби/жінки/ж1.json").read_text("utf8"))
шк, вл, оч = С.hx(ж1["skin"][0]), С.hx(ж1["hair"][0]), С.hx(ж1["eyes"])
for назва, (a, b, c) in (("лише_шкіра", (шк, None, None)), ("без_очей", (шк, вл, None)),
                         ("без_волосся", (шк, None, оч))):
    F = _спроба(lambda: С.features(a, b, c, джерело="spectro"))
    вихід["синт/" + назва] = F if "ВИНЯТОК" in F else _зріз(F)
вихід["синт/порожній_профіль"] = _зріз({})
# Риса з L, C, h, але без rel_C: ясності код не знає (вісь chroma), світлоту знає.
F = М.features(dict(база, шкіра=ж1["skin"], волосся=ж1["hair"], очі=ж1["eyes"], source="spectro"))[0]
for nm in list(F):
    if isinstance(F[nm], dict):
        F[nm].pop("rel_C", None)
вихід["синт/без_rel_C"] = _зріз(F)
Path(sys.argv[2]).write_text(json.dumps(вихід, ensure_ascii=False, indent=1, default=str), "utf8")
print("випадків", len(вихід), "винятків", json.dumps(вихід, ensure_ascii=False).count("ВИНЯТОК"))

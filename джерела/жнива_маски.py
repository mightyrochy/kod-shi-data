# -*- coding: utf-8 -*-
"""МАСКИ ЖНИВ V2 — маска речі на фото: ATR (`_мітки_atr` під замком ONNX-сесії з
`_підперти_stdlib`, `_шкіра_atr`, `маска_atr` з `dominance`), GroundingDINO+SAM у
ComfyUI (`_comfy`, `_sam_слово`, `маска_sam`), запасна від країв кадру
(`маска_без_людини`) і порядок їх спроб — `маска_речі` (ATR → SAM → запасна) з
порогами `ПОРІГ_DOMINANCE`/`ПОРІГ_DOMINANCE_ДРІБНИХ`.

ЧОМУ ОКРЕМИЙ ФАЙЛ (20.09.2026, хвиля стандарту, СТАНДАРТ_КОДУ п.16). `жнива_v2.py`
(1 603 рядки) розділено на вісім модулів `жнива_*` чистим перенесенням; `жнива_v2` —
фасад із реекспортом кожного імені. Спільне тут — (маска, частка, чому[, джерело])
від одного фото і слота; жодна функція не міряє кольору і не питає моделі мови.

ЩО ТУТ (рядки — за `жнива_v2.py` до поділу, коміт 95b0102): 213–470 суцільно.
Коментарі-провенанси переїхали разом із кодом; дати в них — дати рішень.
СТАН МОДУЛЯ: `_ПРОГРІТО` (ATR прогріто) і `_SAM_ЖИВИЙ` (ComfyUI відповів) — прапорці,
які функції ПЕРЕПРИСВОЮЮТЬ через `global`; вони живуть тут, а фасад `жнива_v2`
віддає лише їхнє початкове значення (False/None) — читати стан треба з цього модуля.
`_замок_sam`, `_свій_sam` — один об'єкт, реекспорт віддає його самого.

РЕБРА. Імпортує `жнива_реєстр` (OSS, ATR, ШКІРА, СЛОТ_РЕГІОНИ, `група_слота`,
`_замок_парсера`); чужий `Open Source Stylist` — ліниво з `sys.path`, як і було;
cv2/numpy/PIL — ліниво всередині функцій; фасад не імпортує."""
import os, shutil, sys, tempfile, threading
from жнива_реєстр import OSS, ATR, ШКІРА, СЛОТ_РЕГІОНИ, група_слота, _замок_парсера

# ── МАСКА ───────────────────────────────────────────────────────────────────
_ПРОГРІТО = False


def _підперти_stdlib():
    """Підкласти СПРАВЖНІЙ стандартний `profile`, доки вантажиться ланцюг ATR.

    У `джерела/` лежить власний `profile.py` (профіль людини), і він перекриває
    стандартний модуль. Ланцюг ATR тягне torchvision → torch._dynamo → cProfile,
    а той на рядку `run.__doc__ = _pyprofile.run.__doc__` падає:
    «module 'profile' has no attribute 'run'» (виміряно 17.09). Стандартний
    модуль кладеться в sys.modules за шляхом, а наш повертається одразу після
    прогріву — ліниві `import profile as _PR` у bridge і pipeline мають і далі
    знаходити свій.
    """
    import importlib.util, sysconfig
    стд = sysconfig.get_paths()["stdlib"]
    наш = sys.modules.pop("profile", None)
    for ім in ("profile", "cProfile"):
        ф = os.path.join(стд, ім + ".py")
        if ім in sys.modules or not os.path.exists(ф):
            continue
        спец = importlib.util.spec_from_file_location(ім, ф)
        м = importlib.util.module_from_spec(спец)
        sys.modules[ім] = м
        спец.loader.exec_module(м)
    return наш


def _мітки_atr(шлях):
    """Карта міток ATR (512×384) з чужого модуля — під замком: сесія ONNX одна."""
    global _ПРОГРІТО
    if OSS not in sys.path:
        sys.path.append(OSS)
    with _замок_парсера:
        if _ПРОГРІТО:
            from system.segmentation.parsing import parse_label_map
            return parse_label_map(шлях)
        наш = _підперти_stdlib()
        try:
            from system.segmentation.parsing import parse_label_map
            карта = parse_label_map(шлях)      # тут вантажиться torch і постають дві ONNX-сесії
            _ПРОГРІТО = True
            return карта
        finally:
            if наш is not None:
                sys.modules["profile"] = наш


def _шкіра_atr(арр, розмір):
    """Шкіра й волосся з карти ATR у розмірі фото — або None, коли людини в кадрі нема.

    ЧОМУ НЕ КОЛІР ШКІРИ (18.09.2026, виміряно на вибірці 60). Перша версія
    відсівала шкіру коридором YCrCb, і він з'їдав саму річ: бежевий, пісочний,
    тауп і теракотовий пояси лягають у той самий коридор, від маски лишались
    краї тла (0.2–4 % кадру), і всі п'ять поясів виміряли «білий». Карта ATR
    знає шкіру СЕМАНТИЧНО — обличчя, руки, ноги, — і на фото без людини не
    вигадує її зовсім.
    """
    import cv2, numpy as np
    if арр is None:
        return None
    шк = np.isin(арр, ШКІРА)
    if not шк.any():
        return None
    return cv2.resize(шк.astype("uint8"), розмір, interpolation=cv2.INTER_NEAREST) > 0


def маска_atr(шлях, регіони, арр=None):
    """(маска, dominance, чому) для слота. Береться найбільший із регіонів слота
    («низ» — це спідниця АБО штани, і яка саме, каже сама карта, не назва речі)."""
    import cv2, numpy as np
    арр = _мітки_atr(шлях) if арр is None else арр
    фон = int((арр > 0).sum())
    bgr = cv2.imread(шлях)
    h, w = bgr.shape[:2]
    найкращий, площа = None, 0
    for р in регіони:
        n = int(np.isin(арр, ATR[р]).sum())
        if n > площа:
            найкращий, площа = р, n
    if not найкращий or not фон:
        return None, 0.0, "ATR не знайшов регіон %s" % "/".join(регіони)
    dom = round(площа / фон, 3)
    м = cv2.resize(np.isin(арр, ATR[найкращий]).astype("uint8") * 255, (w, h), interpolation=cv2.INTER_NEAREST)
    return м, dom, "ATR %s, dominance %.3f" % (найкращий, dom)


# Нижче цієї частки кадру запасна маска — не річ, а шум на краях тла: на вибірці
# 60 маски 0.2 % і 0.4 % кадру «виміряли» білий колір тла. Така річ чесно йде в
# «не виміряно», а колір лишається за словом крамниці.
МІН_ЧАСТКА_ЗАПАСНОЇ = 0.01


def маска_без_людини(шлях, арр=None):
    """Запасний шлях: тло — від країв кадру, шкіра — з карти ATR.

    Для прикрас (ATR їх не знає) і крупних планів, де парсер цілого тіла
    розсипається — інвентар напрацювань, §4: «rembg/матування лишають усю людину»,
    тому тут не матування, а різниця з кольором рамки кадру.
    """
    import cv2, numpy as np
    bgr = cv2.imread(шлях)
    h, w = bgr.shape[:2]
    к = max(4, min(h, w) // 40)
    рамка = np.concatenate([bgr[:к].reshape(-1, 3), bgr[-к:].reshape(-1, 3),
                            bgr[:, :к].reshape(-1, 3), bgr[:, -к:].reshape(-1, 3)])
    тло = np.median(рамка, axis=0)
    відст = np.linalg.norm(bgr.astype("float32") - тло, axis=2)
    м = відст > 28
    шкіра = _шкіра_atr(арр, (w, h))
    if шкіра is not None:
        м &= ~шкіра
    м = м.astype("uint8") * 255
    ядро = np.ones((5, 5), "uint8")
    м = cv2.morphologyEx(cv2.morphologyEx(м, cv2.MORPH_OPEN, ядро), cv2.MORPH_CLOSE, ядро)
    n, мітки, стат, _ = cv2.connectedComponentsWithStats((м > 0).astype("uint8"), 8)
    if n <= 1:
        return None, 0.0, "тло не відділилось"
    i = 1 + int(np.argmax(стат[1:, cv2.CC_STAT_AREA]))
    м = ((мітки == i).astype("uint8")) * 255
    частка = float((м > 0).mean())
    if частка < МІН_ЧАСТКА_ЗАПАСНОЇ:
        return None, round(частка, 3), "запасна маска %.3f кадру — речі не видно" % частка
    return м, round(частка, 3), "запасна маска (тло від країв%s), частка кадру %.3f" % (
        ", шкіра з ATR" if шкіра is not None else "", частка)


# ── МАСКА ЧЕРЕЗ SAM (GroundingDINO + SAM у ComfyUI) ─────────────────────────
# ЧОМУ (18.09.2026). Запасна маска бере ВСЕ, що не схоже на краї кадру: на
# прикрасі це рука й шия, на поясі — уся сукня, на крупному плані — половина
# кадру. GroundingDINO називає річ словом і SAM вирізає саме її. Ставиться перед
# запасною, а не замість: ComfyUI може бути не піднятий, і тоді конвеєр іде далі.
# ПРОМПТ — ОДНЕ АНГЛІЙСЬКЕ СЛОВО (урок OSS, `system/segmentation/prompts.py`,
# V-SEG-004): «shirt», «belt», «footwear» працюють, а складене
# «shoes . sandals . wedge» повертає увесь силует.
COMFY_ХОСТ = os.environ.get("COMFY_HOST", "127.0.0.1")
COMFY_ПОРТ = int(os.environ.get("COMFY_PORT", "8000"))
SAM_СЛОВО = {"сережки": "earrings", "намисто": "necklace", "кольє": "necklace",
             "каблучка": "ring", "браслет": "bracelet", "брошка": "brooch",
             "прикраси": "jewelry", "пояс": "belt", "взуття": "shoe", "сумка": "handbag",
             "головний_убір": "hat", "шарф": "scarf", "сукня": "dress", "верх": "shirt",
             "верхній_шар": "jacket", "низ": "skirt"}
# Маска SAM дрібніша за запасну і це нормально: каблучка — 0.5 % кадру. Поріг
# тут лише проти ПОРОЖНЬОЇ маски (GroundingDINO нічого не знайшов → усі нулі);
# 300 пікселів k-means вимагає й сам, а 0.2 % кадру 1200×1600 — це 3 840.
МІН_ЧАСТКА_SAM = 0.002
_SAM_ЖИВИЙ = None                                   # None — ще не пробували, False — сервера нема
_замок_sam = threading.Lock()
_свій_sam = threading.local()


def _comfy():
    """ComfyUIClient ЦЬОГО ПОТОКУ, або None коли сервера нема.

    Сервер перевіряється ОДИН раз на процес: коли ComfyUI не піднятий, 60 речей
    не мусять по черзі чекати на відмову з'єднання. А клієнт — на потік, бо
    `requests.Session` потокобезпеки не обіцяє, а потоків тут три.
    """
    global _SAM_ЖИВИЙ
    if OSS not in sys.path:
        sys.path.append(OSS)
    with _замок_sam:
        if _SAM_ЖИВИЙ is None:
            try:
                from system.clients.comfyui import ComfyUIClient
                ComfyUIClient(COMFY_ХОСТ, COMFY_ПОРТ).system_stats()
                _SAM_ЖИВИЙ = True
            except Exception as _e:
                import os as _os, traceback as _tb   # п.14: не мовчати (форма bridge)
                if _os.environ.get("ЛЮСТЕРКО_ТРАСА"): _tb.print_exc()
                _SAM_ЖИВИЙ = False
    if not _SAM_ЖИВИЙ:
        return None
    if getattr(_свій_sam, "к", None) is None:
        from system.clients.comfyui import ComfyUIClient
        _свій_sam.к = ComfyUIClient(COMFY_ХОСТ, COMFY_ПОРТ)
    return _свій_sam.к


def _sam_слово(слот, арр):
    """Однослівний промпт GroundingDINO для слота. «Низ» — це спідниця АБО штани,
    і яка саме, каже карта ATR, а не назва речі (як і в `маска_atr`)."""
    import numpy as np
    if група_слота(слот) == "низ" and арр is not None and \
            int(np.isin(арр, ATR["pants"]).sum()) > int(np.isin(арр, ATR["skirt"]).sum()):
        return "pants"
    return SAM_СЛОВО.get(слот) or SAM_СЛОВО.get(група_слота(слот))


def маска_sam(шлях, слово, арр=None):
    """(маска, частка кадру, чому) від GroundingDINO+SAM; шкіра й волосся — геть.

    SAM вирізає РІЧ РАЗОМ із тим, що на ній лежить: намисто на шиї приходить із
    шматком шиї, пояс — зі складкою сукні під пальцями. Карта ATR знає шкіру й
    волосся семантично (мітки 2, 11–15), і `маска_без_людини` віднімає їх так
    само — тут той самий відрахунок, щоб колір міряли пікселі речі, а не тіла.
    """
    import cv2, numpy as np
    from PIL import Image
    к = _comfy()
    if not слово:
        return None, 0.0, "SAM не питали: слова для слота нема"
    if к is None:
        return None, 0.0, "SAM не питали: ComfyUI на %s:%d не піднятий" % (COMFY_ХОСТ, COMFY_ПОРТ)
    тека = tempfile.mkdtemp(prefix="sam_", dir=tempfile.gettempdir())
    try:
        from system.segmentation.grounded_sam import segment
        # Мітка ЛАТИНИЦЕЮ: вона стає ім'ям файлу маски, а cv2.imread не читає
        # шляхів поза ANSI-кодуванням (виміряно 18.09: «річ.png» не відкрився).
        м = cv2.imread(segment(шлях, {"item": слово}, к, тека)["item"], cv2.IMREAD_GRAYSCALE)
    except Exception as e:
        return None, 0.0, "SAM «%s» не дав маски: %s" % (слово, str(e)[:90])
    finally:
        shutil.rmtree(тека, ignore_errors=True)
    w, h = Image.open(шлях).size
    if м is None:
        return None, 0.0, "SAM «%s»: файл маски не прочитався" % слово
    if м.shape[:2] != (h, w):
        м = cv2.resize(м, (w, h), interpolation=cv2.INTER_NEAREST)
    б = м > 127
    шкіра = _шкіра_atr(арр, (w, h))
    if шкіра is not None:
        б &= ~шкіра
    частка = float(б.mean())
    if частка < МІН_ЧАСТКА_SAM:
        return None, round(частка, 4), "SAM «%s»: %.4f кадру — річ не знайдена" % (слово, частка)
    return б.astype("uint8") * 255, round(частка, 3), "SAM «%s»%s, частка кадру %.3f" % (
        слово, ", шкіра з ATR" if шкіра is not None else "", частка)


# DOMINANCE — частка регіону серед УСЬОГО розпарсеного. Для сукні чи пальта на
# моделі це 0.3–0.8, і 0.12 відсікає розсипаний парс крупного плану. Але пояс,
# взуття, капелюх чи сумка на моделі — завжди мала частка людини (пояс на
# вибірці: 0.033 при правильній масці), тож для них поріг свій.
ПОРІГ_DOMINANCE = 0.12
ПОРІГ_DOMINANCE_ДРІБНИХ = 0.02
ДРІБНІ_СЛОТИ = {"пояс", "взуття", "головний_убір", "шарф", "сумка"}


def маска_речі(шлях, слот):
    """(маска, частка, чому, джерело): ATR → SAM → запасна, у цьому порядку.

    Карта ATR рахується ОДИН раз і на фото прикраси теж: і SAM, і запасній масці
    вона потрібна, щоб прибрати руку чи шию моделі.
    """
    арр = _мітки_atr(шлях)
    регіони = СЛОТ_РЕГІОНИ.get(група_слота(слот)) or []
    чому = ""
    if регіони:
        м, dom, чому = маска_atr(шлях, регіони, арр)
        поріг = ПОРІГ_DOMINANCE_ДРІБНИХ if група_слота(слот) in ДРІБНІ_СЛОТИ else ПОРІГ_DOMINANCE
        if м is not None and dom >= поріг and (м > 0).mean() >= 0.005:
            return м, dom, чому, "ATR"
    м, частка, чому_sam = маска_sam(шлях, _sam_слово(слот, арр), арр)
    чому = (чому + " → " if чому else "") + чому_sam
    if м is not None:
        return м, частка, чому, "SAM"
    зап_м, зап_ч, зап_чому = маска_без_людини(шлях, арр)
    return зап_м, зап_ч, чому + " → " + зап_чому, "запасна"

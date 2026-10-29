# -*- coding: utf-8 -*-
"""розбір_рядків_5192.py — ПОРЯДКОВИЙ РОЗБІР ПОЛІВ КАРТКИ (варіант Б рядка 6429), ПОЗА ПРОДУКТОМ.

ЩО РОБИТЬ. Бере різні рядки «ключ: значення» полів картки (`дані_5192.py`, файл
`дані_5191_5194/рядки_5192.json.gz`) і кожен рядок — ОДНИМ викликом мовної моделі — перекладає в
коди схеми розбору (`каталог_розбір.ПОЛЯ`) з цитатою з самого рядка. Каталогу не міняє і в
розбір речей не підключається (п.16: підключення #1028 — окремим кроком).

ЧОМУ НЕ СКЕЛЕТ ОДНІЄЇ РЕЧІ (рядок 6543). Промпт речі після #1238 — 12 550 знаків рамки, граматика
відповіді — 18 785; повторити її на кожному рядку — платити за 46 полів там, де рядок «Склад»
стосується шести. Тому виклик несе ЛИШЕ поля груп, яких рядок може стосуватися (`ГРУПИ`), а скелет —
назви й описи полів без переліків кодів: переліки несе граматика `response_format` (ідея рядка
6202; `--переліки` повертає їх у текст для порівняння на пілоті).

ХТО ВИРІШУЄ, ЯКІ ПОЛЯ СТОСУЮТЬСЯ РЯДКА (п.12). Не код за словами ключа: МОДЕЛЬ, раз на кожен ключ
(виклик «ключ + до `ЗРАЗКІВ` його значень → коди груп»), і відповідь лягає даними в `ключі.json`
теки. Код лише шукає ключ у цій мапі як непрозорий рядок. Ключ без груп рядків у модель не шле.

ЩО ТРИМАЄ КОДИ (п.16). Відповідь рядка доповнюється до повної відповіді «unknown» і йде через
`каталог_розбір.з_відповіді` з текстом «ключ: значення»: той самий сторож цитат, зведення до
переліку й числа, що й у розборі речі. `not_applicable` граматика рядка не пускає: чи буває поле в
такої речі, рядок не знає (слоту він не бачить).

ВХІД — РЯДКИ КРАМНИЦІ, І ЛИШЕ ВОНИ. Пара (ключ, значення) іде в розбір, лише коли бодай в одній
речі вона стоїть словами крамниці за правилом `каталог_розбір.поля_крамниці` (службові ключі
жниварки, ключ із двійником «*_джерело» — наше попереднє збагачення — геть). Виміряно на
`каталог_повний.xml`: 9 762 пари 98 ключів, з них 1 220 — лише наше збагачення (`силует`,
`довжина`, `розміри_в_наявності`…), лишається 8 542.

ЖУРНАЛ І ВІДНОВЛЕННЯ (з приладу 5190, #991). Узято: id рядка — SHA-256 точних байтів «ключ\\0значення»;
журнал на диску, записаний ДО запиту (`inflight`) і після (`done` / `failed`), з fsync; замок теки
проти двох прогонів разом; атомарна заміна підсумкових файлів. Не взято: заборону повтору без
окремого дозволу (5190-repeat-v1) і почерговий проксі — там пілот берег заморожену історію одного
виклику, тут виклик локальний, і обірваний прогін має докотитись ТІЄЮ САМОЮ командою: рядок, чия
відповідь уже `done` під тим самим запитом (SHA-256 тіла), у модель удруге не йде; `inflight` без
`done` (обрив посеред виклику) іде знову.

ЯК ЗАПУСТИТИ (ноутбук, LM Studio, як `каталог_розбір_прогін.py`; MODEL_URL, MODEL_TEMP, MODEL_MAX_TOKENS):
  python3 джерела/прилади/розбір_рядків_5192.py --модель <ід> --куди <тека> --пілот 300 [--паралельно 2]
  python3 джерела/прилади/розбір_рядків_5192.py --модель <ід> --куди <тека> --усі
  python3 джерела/прилади/розбір_рядків_5192.py --заглушка --куди <тека> --пілот 0     (без моделі)
  python3 джерела/прилади/розбір_рядків_5192.py --зібрати <тека>                    (лише підсумки)
  python3 джерела/проби/еталон_частки.py <тека>/речі.json                       (якість на еталоні 404)
`--пілот N` — рядки 60 речей еталону 404 першими, далі інші рядки сідом 17 до N.
"""
import argparse
import concurrent.futures
import datetime
import gzip
import hashlib
import json
import os
import random
import statistics
import sys
import threading
import time
import urllib.request
import xml.etree.ElementTree as XML

ТУТ = os.path.dirname(os.path.abspath(__file__))
ДЖЕРЕЛА = os.path.dirname(ТУТ)
if ДЖЕРЕЛА not in sys.path:
    sys.path.insert(0, ДЖЕРЕЛА)

import каталог_розбір as КР                  # noqa: E402
import каталог_розбір_прогін as П            # noqa: E402
import протокол as ПР                        # noqa: E402
import збирач_промптів as ЗП                 # noqa: E402

ВЕРСІЯ = "lyusterko-catalog-row-parse-v1"
ЗАДАЧА = "CATALOG_ROW_PARSE_V1"
ЗАДАЧА_КЛЮЧА = "CATALOG_KEY_ROUTE_V1"
РЯДКИ = os.path.join(ДЖЕРЕЛА, "дані_5191_5194", "рядки_5192.json.gz")
КАТАЛОГ = os.path.join(ДЖЕРЕЛА, "..", "каталог_повний.xml.gz")
ЕТАЛОН = os.path.join(ДЖЕРЕЛА, "проби", "еталон_розбору.json")
СІД = 17
# Скільки значень ключа бачить модель, коли вирішує його групи: вісім рівномірно з упорядкованого
# переліку (код бере їх за номером, слів не читає), кожне до `КР.СТЕЛЯ_ЦИТАТИ` знаків.
ЗРАЗКІВ = 8

# ── ГРУПИ ПОЛІВ: КОД ГРУПИ → ШЛЯХИ `КР.ПОЛЯ` (кошик А, п.12: коди → коди) ─────────
# Група — поля, про які пише ОДИН вид рядка картки (склад, мірки взуття, колір…). Модель обирає
# групи ключа, а не 46 полів поодинці: так рішення коротке, а виклик рядка все одно вужчий за річ.
ГРУПИ = {
    "kind": ("slot", "item_type", "set_kind", "set_parts[].slot", "set_parts[].item_type"),
    "fibre": ("fabric", "material", "fabric_kind", "texture", "elastane_pct", "wool_pct"),
    "fit": ("cut", "size_fit", "elastic_waist", "belt", "veto.oversize", "veto.tight"),
    "length": ("length", "length_cm", "shaft"),
    "sleeve_neck": ("sleeve", "sleeve_cut", "neckline", "collar"),
    "outerwear": ("closure", "breasted", "hood", "fur_trim", "pile", "quilted", "filling"),
    "shoe": ("vamp", "heel.present", "heel.shape", "heel.height", "heel.height_cm", "sole",
             "shoe_width", "sole_attachment"),
    "bag": ("bag_size", "strap_cm"),
    "metal": ("metal", "metal_where", "chain_cm"),
    "colour": ("color_main", "color_extra[]", "color_why"),
    "surface": ("pattern", "decor[]", "veto.stripes", "veto.big_print", "veto.print", "veto.shine"),
}
_ПИШЕ_МОДЕЛЬ = [ш for ш, _, _ in КР.ПОЛЯ if ш not in КР.ВИВЕДЕНІ]
assert sorted(ш for г in ГРУПИ.values() for ш in г) == sorted(_ПИШЕ_МОДЕЛЬ), "кожне поле — в одній групі"
# Правила, які йдуть у виклик рядка лише тоді, коли в ньому є група, якої вони стосуються.
ПРАВИЛА_ГРУП = {
    "kind": "\"set_parts\": only when the row says the item is sold as a set, one entry per part; otherwise [].",
    "colour": "\"color_main\": the colour this row gives the item itself; other colours it names for this "
              "item go to \"color_extra\".",
    "metal": "\"metal_where\": the metal is the body of the item or only its hardware.",
    "fit": "\"veto\": \"yes\" when the row says the feature is there, \"no\" when it says it is not.",
    "surface": "\"veto\": \"yes\" when the row says the feature is there, \"no\" when it says it is not.",
}
ПРАВИЛО_МІРКИ = ("A field with \"unit\" takes a number: \"value\" the number the row gives, \"unit\" its unit, "
                 "the quote holds that number in digits. A range or numbers per size: the first number.")
ПРАВИЛА = (
    "The input is one field of a shop card: its \"key\" and the \"value\" the shop wrote in it. Answer only "
    "the fields in \"answer_schema\" and only from this row.",
    "Every field is a pair. \"quote\": the shortest words of this row that state the value, copied letter "
    "for letter in the shop's language, not translated or retold. \"value\": one code allowed for that field.",
    "No words of this row state this very feature: quote \"\" and value \"unknown\". Never infer a value from "
    "what such a field or such an item usually holds.",
    "The quote must state the chosen code itself, not a nearby one. Words that fit no code exactly: \"unknown\".",
    "\"no\" and \"none\": the row says the feature is absent; they need a quote like any value.",
    "The fields are about the item itself: what the row says only of one part of it (lining, insole, trim) "
    "states that part, not the item's fabric, material or colour.",
)
ПРАВИЛА_КЛЮЧА = (
    "The input is one key of shop cards and some values shops wrote under it.",
    "List every group whose fields such values can state; a key whose values state none of them: [].",
    "Decide by what the values say, not only by the key's name; other values under this key may differ.",
) + ("Groups and the item fields each one holds: %s." % "; ".join(
    "%s — %s" % (г, ", ".join(ш.replace("[]", "") for ш in шл)) for г, шл in ГРУПИ.items()),)
_ВХІД = (ЗП.Поле("key", "the name of the shop card field", треба=True),
         ЗП.Поле("value", "the value the shop wrote in it", треба=True))
_ВХІД_КЛЮЧА = (ЗП.Поле("key", "the name of a shop card field", треба=True),
               ЗП.Поле("values", "some values shops wrote under this key", треба=True))


def _крок(к):
    """Крок шляху «а[]» → («а», True)."""
    return (к[:-2], True) if к.endswith("[]") else (к, False)


def шляхи_груп(групи):
    """Коди груп → шляхи полів порядком `КР.ПОЛЯ` (той самий порядок, що в повному скелеті)."""
    є = {ш for г in групи for ш in ГРУПИ[г]}
    return [ш for ш in _ПИШЕ_МОДЕЛЬ if ш in є]


def _без_на(вузол):
    """Копія вузла схеми без `not_applicable` у жодному переліку: рядок слоту речі не бачить."""
    if isinstance(вузол, dict):
        return {к: ([к_ for к_ in в if к_ != КР.НЕ_СТОСУЄТЬСЯ] if к == "enum" else _без_на(в)) for к, в in вузол.items()}
    return [_без_на(в) for в in вузол] if isinstance(вузол, list) else вузол


def схема_рядка(шляхи):
    """JSON Schema відповіді рядка — `КР.схема_відповіді()`, обрізана до `шляхи`, без `features`."""
    повна, корінь = КР.схема_відповіді(), {"type": "object", "additionalProperties": False,
                                          "required": [], "properties": {}}
    for шлях in шляхи:
        дж, ціль, кроки = повна, корінь, шлях.split(".")
        for і, крок in enumerate(кроки):
            ім, список = _крок(крок)
            вузол = дж["properties"][ім]
            if ім not in ціль["required"]:
                ціль["required"].append(ім)
            if і == len(кроки) - 1:
                ціль["properties"][ім] = _без_на(вузол)
                break
            if ім not in ціль["properties"]:
                порожній = dict(вузол["items"] if список else вузол, required=[], properties={})
                ціль["properties"][ім] = dict(вузол, items=порожній) if список else порожній
            дж = вузол["items"] if список else вузол
            ціль = ціль["properties"][ім]["items"] if список else ціль["properties"][ім]
    return корінь


def скелет_рядка(шляхи, переліки=False):
    """Скелет промпта рядка: назва й опис кожного поля; коди переліку — лише з `переліки`."""
    с = {}
    for шлях in шляхи:
        коди, опис = КР.ПЕРЕЛІКИ[шлях], КР.ОПИСИ[шлях]
        свої = "|".join(к for к in коди if к != КР.НЕ_СТОСУЄТЬСЯ)
        if isinstance(коди, КР.Мірка):
            лист = {КР.ЦИТАТА: "<quote>", КР.ЗНАЧЕННЯ: "<number>%s — %s" % ("|" + свої if переліки else "", опис),
                    КР.ОДИНИЦЯ: "|".join(коди.одиниці + [КР.UNKNOWN]) if переліки else "<unit>"}
        else:
            лист = {КР.ЦИТАТА: "<quote>", КР.ЗНАЧЕННЯ: "%s — %s" % (свої if переліки else "<code>", опис)}
        вузол, кроки = с, шлях.split(".")
        for і, крок in enumerate(кроки):
            ім, список = _крок(крок)
            if і == len(кроки) - 1:
                вузол[ім] = [лист] if список else лист
            else:
                вузол = вузол.setdefault(ім, [{}])[0] if список else вузол.setdefault(ім, {})
    return с


def промпт_рядка(ключ, значення, групи, переліки=False):
    """Повідомлення моделі про один рядок — збирачем промптів, англійським шаблоном."""
    шляхи = шляхи_груп(групи)
    правила = ПРАВИЛА + tuple(dict.fromkeys(ПРАВИЛА_ГРУП[г] for г in групи if г in ПРАВИЛА_ГРУП))
    if any(isinstance(КР.ПЕРЕЛІКИ[ш], КР.Мірка) for ш in шляхи):
        правила += (ПРАВИЛО_МІРКИ,)
    о = ЗП.Оголошення(задача=ЗАДАЧА, роль="You read one field of a shop card and write what it says as codes, "
                      "each backed by a quote from that field.", вхід=_ВХІД, правила=правила, вихід=ЗАДАЧА,
                      межі=("лише_вхід",), скелет=скелет_рядка(шляхи, переліки), мова_промпту="en")
    return ЗП.зібрати(о, {"key": ключ, "value": _значення(значення)})


def промпт_ключа(ключ, зразки):
    """Повідомлення моделі про один ключ: які групи полів можуть стояти в його значеннях."""
    о = ЗП.Оголошення(задача=ЗАДАЧА_КЛЮЧА, роль="You decide which groups of item fields a shop card key can state.",
                      вхід=_ВХІД_КЛЮЧА, правила=ПРАВИЛА_КЛЮЧА, вихід=ЗАДАЧА_КЛЮЧА, межі=("лише_вхід",),
                      скелет={"groups": ["<group code>"]}, мова_промпту="en")
    return ЗП.зібрати(о, {"key": ключ, "values": [_значення(з)[:КР.СТЕЛЯ_ЦИТАТИ] for з in зразки]})


def схема_ключа():
    """Граматика відповіді ключа: список різних кодів груп."""
    return {"type": "object", "additionalProperties": False, "required": ["groups"],
            "properties": {"groups": {"type": "array", "uniqueItems": True, "maxItems": len(ГРУПИ),
                                      "items": {"enum": list(ГРУПИ)}}}}


def _значення(з):
    """Значення рядка так, як його бачить модель і сторож цитат: стеля `КР.СТЕЛЯ_ЗНАЧЕННЯ`, як у розборі речі."""
    т = str(з).strip()
    return т if len(т) <= КР.СТЕЛЯ_ЗНАЧЕННЯ else т[:КР.СТЕЛЯ_ЗНАЧЕННЯ] + "…"


def ід_рядка(ключ, значення):
    """SHA-256 точних байтів «ключ\\0значення» (як `row_id` приладу 5190 — без нормалізації)."""
    return hashlib.sha256(("%s\0%s" % (ключ, значення)).encode("utf-8")).hexdigest()


# ── РЯДКИ КАТАЛОГУ ───────────────────────────────────────────────────────────
def _службове(ключ, ключі_речі):
    """Те саме правило, що `КР.поля_крамниці`: службовий ключ чи наше збагачення (двійник «*_джерело»)."""
    return ключ not in КР.ЗАВЖДИ and (ключ in КР.СЛУЖБОВІ or ключ.endswith("_джерело")
                                     or ключ + "_джерело" in ключі_речі or len(ключ) > КР.СТЕЛЯ_КЛЮЧА)


def рядки_каталогу():
    """({id рядка: (ключ, значення)}, {id речі: [id рядка]}) — пари `рядки_5192`, що бодай в одній речі
    стоять словами крамниці; id речі — «id офера@магазин», як в еталоні й `розбір.json`."""
    with open(РЯДКИ, "rb") as ф:
        пари = {(к, з) for к, в in json.loads(gzip.decompress(ф.read())).items() for з in в}
    with open(КАТАЛОГ, "rb") as ф:
        офери = XML.fromstring(gzip.decompress(ф.read())).iter("offer")
    рядки, речі = {}, {}
    for о in офери:
        поля = [(п.get("name"), "".join(п.itertext())) for п in о.findall("param")]
        ключі = {к for к, _ in поля}
        магазин = next((з.strip().lower() for к, з in поля if к in ("магазин", "Магазин")), "")
        for к, з in поля:
            if (к, з) in пари and not _службове(к, ключі):
                і = ід_рядка(к, з)
                рядки[і] = (к, з)
                речі.setdefault(о.get("id") + "@" + магазин, []).append(і)
    return рядки, {р: list(dict.fromkeys(в)) for р, в in речі.items()}


def ід_еталону():
    """id 60 речей еталону 404 порядком файла."""
    with open(ЕТАЛОН, encoding="utf-8") as ф:
        return [р["id"] for р in json.load(ф)["речі"]]


def вибрати(рядки, речі, пілот=None):
    """id рядків прогону: усі (порядком ключ, значення) або рядки еталону першими й інші сідом до `пілот`."""
    if пілот is None:
        return sorted(рядки, key=lambda і: рядки[і])
    перші = list(dict.fromkeys(і for р in ід_еталону() for і in речі.get(р, ())))
    решта = sorted(set(рядки) - set(перші), key=lambda і: рядки[і])
    return перші + random.Random(СІД).sample(решта, max(0, min(len(решта), пілот - len(перші))))


def зразки_ключа(ключ, рядки):
    """До `ЗРАЗКІВ` значень ключа рівномірно з упорядкованого переліку — за номером, не за словами."""
    в = sorted({з for к, з in рядки.values() if к == ключ})
    return [в[і * len(в) // ЗРАЗКІВ] for і in range(min(ЗРАЗКІВ, len(в)))]


# ── ЖУРНАЛ ────────────────────────────────────────────────────────────────────
class Журнал:
    """Журнал викликів теки (`журнал.jsonl`): рядок на подію, дописується з fsync; замок теки — на час прогону."""

    def __init__(self, тека):
        """Відкриває журнал теки й бере замок; замок лишився від обірваного процесу — його знімає людина."""
        self.шлях, self.замок = os.path.join(тека, "журнал.jsonl"), os.path.join(тека, ".замок")
        try:
            with open(self.замок, "x", encoding="utf-8") as ф:
                ф.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
        except FileExistsError:
            raise SystemExit("тека %s зайнята іншим прогоном; коли його нема (обрив) — видаліть %s"
                             % (тека, self.замок))
        self.готові, self._лок = готові(тека), threading.Lock()

    def записати(self, подія):
        """Дописує подію рядком і скидає на диск до наступного кроку."""
        подія = dict(подія, utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        with self._лок, open(self.шлях, "a", encoding="utf-8") as ф:
            ф.write(json.dumps(подія, ensure_ascii=False) + "\n")
            ф.flush()
            os.fsync(ф.fileno())

    def закрити(self):
        """Знімає замок теки."""
        if os.path.exists(self.замок):
            os.remove(self.замок)


def події(тека):
    """Події журналу теки порядком запису; обірваний останній рядок (обрив посеред запису) — пропуск."""
    шлях = os.path.join(тека, "журнал.jsonl")
    if not os.path.exists(шлях):
        return []
    вих = []
    with open(шлях, encoding="utf-8") as ф:
        for р in ф:
            try:
                вих.append(json.loads(р))
            except ValueError:
                continue
    return вих


def готові(тека):
    """{(id, SHA запиту): подія done} — останнє `done` кожного запиту; `inflight` без `done` сюди не входить."""
    return {(п["id"], п["запит"]): п for п in події(тека) if п.get("стан") == "done"}


# ── ВИКЛИК МОДЕЛІ ─────────────────────────────────────────────────────────────
def тіло(повідомлення, схема, ід_моделі):
    """Тіло запиту форми OpenAI з граматикою відповіді — як `каталог_розбір_прогін.модель`."""
    т = dict(model=ід_моделі, messages=[dict(role="user", content=json.dumps(повідомлення, ensure_ascii=False))],
             stream=False, max_tokens=int(os.environ.get("MODEL_MAX_TOKENS") or П.МАКС_ТОКЕНІВ),
             response_format={"type": "json_schema", "json_schema": {"name": ЗАДАЧА.lower(), "strict": True,
                                                                     "schema": схема}})
    if os.environ.get("MODEL_TEMP"):
        т["temperature"] = float(os.environ["MODEL_TEMP"])
    return т


def sha_тіла(т):
    """SHA-256 тіла запиту: інша модель, правило чи граматика — інший запит, і відповідь не береться з журналу."""
    return hashlib.sha256(json.dumps(т, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def надіслати(т):
    """(текст відповіді, секунд) від LM Studio (`П.АДРЕСА`, MODEL_URL); виняток — вгору, у журнал."""
    запит = urllib.request.Request(П.АДРЕСА + "/chat/completions", data=json.dumps(т, ensure_ascii=False).encode("utf-8"),
                                   headers={"Content-Type": "application/json"})
    т0 = time.time()
    with urllib.request.urlopen(запит, timeout=3600) as в:
        дані = json.loads(в.read().decode("utf-8"))
    return (((дані.get("choices") or [{}])[0].get("message") or {}).get("content") or ""), round(time.time() - т0, 1)


def заглушка(т, цитата=""):
    """Відповідь за граматикою без моделі (дим): перелік — перший код, крім "unknown"; число — "unknown";
    список — порожній, крім груп ключа (усі: заглушка слів ключа не читає); цитата — `цитата`."""
    def з(с, ім=None):
        if "enum" in с:
            return next((к for к in с["enum"] if к != КР.UNKNOWN), КР.UNKNOWN)
        if "anyOf" in с:
            return КР.UNKNOWN
        if с.get("type") == "array":
            return list(с["items"]["enum"]) if ім == "groups" else []
        if с.get("type") == "object":
            вих = {к: з(в, к) for к, в in с["properties"].items()}
            return dict(вих, quote=цитата) if КР.ЦИТАТА in с["properties"] else вих
        return цитата
    return json.dumps(з(т["response_format"]["json_schema"]["schema"]), ensure_ascii=False), 0.0


class Обрив(Exception):
    """Штучний обрив прогону (`--стоп-після`): перевірка відновлення без моделі."""


def _виклик(журнал, вид, ід, т, свідок, стоп, мірка, цитата):
    """Один виклик із журналом: `inflight` до запиту, `done`/`failed` після; повтор на не-JSON — іншим сідом."""
    запит = sha_тіла(т)
    if (ід, запит) in журнал.готові:
        return журнал.готові[(ід, запит)]
    with мірка["лок"]:
        мірка["викликів"] += 1
        обрив = стоп is not None and мірка["викликів"] > стоп
    if обрив and мірка["викликів"] > стоп + 1:
        raise Обрив()                                 # решта черги після обриву — без сліду в журналі
    журнал.записати(dict(свідок, вид=вид, id=ід, запит=запит, стан="inflight"))
    if обрив:
        raise Обрив()                                 # обрив посеред виклику: `inflight` без `done`
    відп, секунд = "", 0.0
    try:
        for спроба in range(1 + П.ПОВТОРІВ_НА_НЕ_JSON):
            т_ = dict(т, seed=спроба) if спроба else т
            відп, с = заглушка(т_, цитата) if мірка["заглушка"] else надіслати(т_)
            секунд += с
            if isinstance(ПР.розібрати_json(відп.replace(КР.ВСТАВКА, "")), dict):
                break
    except Exception as е:                            # noqa: BLE001 — впалий виклик названий у журналі
        журнал.записати(dict(свідок, вид=вид, id=ід, запит=запит, стан="failed", помилка="%s: %s" % (type(е).__name__, е)))
        return None
    подія = dict(свідок, вид=вид, id=ід, запит=запит, стан="done", відповідь=відп, секунд=round(секунд, 1),
                 знаків_запиту=len(т["messages"][0]["content"]), знаків_відповіді=len(відп))
    журнал.записати(подія)
    return подія


def групи_з(відповідь):
    """Коди груп з відповіді ключа; чужий код — геть (граматика його й так не пустить)."""
    об = ПР.розібрати_json((відповідь or "").replace(КР.ВСТАВКА, ""))
    г = об.get("groups") if isinstance(об, dict) else None
    return [к for к in ГРУПИ if isinstance(г, list) and к in г]


def прогін(куди, ід_моделі, вибрані, рядки, паралельно=П.ПАРАЛЕЛЬНО, переліки=False, мапа=None, стоп=None):
    """Ключі вибраних рядків → групи (моделлю або з `мапа`), далі кожен рядок з групами → модель; усе в журнал."""
    os.makedirs(куди, exist_ok=True)
    журнал = Журнал(куди)
    мірка = dict(викликів=0, лок=threading.Lock(), заглушка=ід_моделі == "заглушка")
    try:
        ключі = sorted({рядки[і][0] for і in вибрані})
        мапа = dict(мапа or {})
        for к in ключі:
            if к in мапа:
                continue
            зр = зразки_ключа(к, рядки)
            п = _виклик(журнал, "key", ід_рядка(к, ""), тіло(промпт_ключа(к, зр), схема_ключа(), ід_моделі),
                        dict(ключ=к, зразки=зр), стоп, мірка, "")
            мапа[к] = групи_з(п["відповідь"]) if п else None
        _записати(os.path.join(куди, "ключі.json"), {к: мапа[к] for к in ключі})
        роботи = [(і, мапа[рядки[і][0]]) for і in вибрані if мапа.get(рядки[і][0])]

        def одна(р):
            """Один рядок у модель (потік): журнал пише сам, спільного не чіпає."""
            і, гр = р
            к, з = рядки[і]
            return _виклик(журнал, "row", і, тіло(промпт_рядка(к, з, гр, переліки), схема_рядка(шляхи_груп(гр)), ід_моделі),
                           dict(ключ=к, значення=з, групи=гр), стоп, мірка, _значення(з)[:КР.СТЕЛЯ_ЦИТАТИ])
        # Пачками (`П.ЗАПИС_КОЖНІ`), а не всією чергою: пул, якому віддано всі рядки, на Ctrl+C чекав би кінця
        # черги; так обрив чекає лише поточної пачки, а поступ видно.
        вийшло, т0 = [], time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, паралельно)) as пул:
            for край in range(0, len(роботи), П.ЗАПИС_КОЖНІ):
                вийшло += list(пул.map(одна, роботи[край:край + П.ЗАПИС_КОЖНІ]))
                print("%d/%d рядків · нових викликів %d · %.1f хв" % (len(вийшло), len(роботи), мірка["викликів"],
                                                                      (time.time() - т0) / 60), flush=True)
    finally:
        журнал.закрити()
    print("тека %s · ключів %d (без груп %d) · рядків %d, у модель %d · нових викликів %d · впало %d"
          % (куди, len(ключі), sum(1 for к in ключі if not мапа.get(к)), len(вибрані), len(роботи),
             мірка["викликів"], sum(1 for п in вийшло if п is None)))
    return зібрати(куди)


# ── ПІДСУМКИ БЕЗ МОДЕЛІ ───────────────────────────────────────────────────────
def _записати(шлях, дані):
    """JSON через тимчасовий файл і заміну: обірваний запис не псує попередній."""
    with open(шлях + ".tmp", "w", encoding="utf-8") as ф:
        json.dump(дані, ф, ensure_ascii=False, indent=1)
    os.replace(шлях + ".tmp", шлях)


def _невідомо():
    """Повна відповідь «нічого не сказано»: кожне поле "unknown" без цитати, списки порожні."""
    об = {КР.ОСОБЛИВОСТІ: []}
    for шлях, коди, _ in КР.ПОЛЯ:
        кроки = [_крок(к) for к in шлях.split(".")]
        if кроки[0][1]:
            об[кроки[0][0]] = []
            continue
        лист = {КР.ЦИТАТА: "", КР.ЗНАЧЕННЯ: КР.UNKNOWN}
        if isinstance(коди, КР.Мірка):
            лист[КР.ОДИНИЦЯ] = КР.UNKNOWN
        if len(кроки) == 1:
            об[кроки[0][0]] = лист
        else:
            об.setdefault(кроки[0][0], {})[кроки[1][0]] = лист
    return об


def _взяти(об, шлях):
    """Значення шляху «а.б» / «а[]» / «а[].б» з обʼєкта (для «а[].б» — увесь список «а»)."""
    ім = _крок(шлях.split(".")[0])[0]
    в = об.get(ім) if isinstance(об, dict) else None
    if "." in шлях and not шлях.split(".")[0].endswith("[]"):
        в = в.get(шлях.split(".")[1]) if isinstance(в, dict) else None
    return в


def коди_рядка(відповідь, ключ, значення, групи):
    """Відповідь рядка → ({шлях: код}, {шлях: цитата}, причини) — через `КР.з_відповіді` з текстом рядка."""
    об = ПР.розібрати_json((відповідь or "").replace(КР.ВСТАВКА, ""))
    if not isinstance(об, dict):
        return None, {}, ["не JSON"]
    повна = _невідомо()
    for к, в in об.items():
        if к in повна and isinstance(в, dict) and isinstance(повна[к], dict) and КР.ЦИТАТА not in повна[к]:
            повна[к].update(в)
        elif к in повна:
            повна[к] = в
    поля, причини = КР.з_відповіді(json.dumps(повна, ensure_ascii=False), {"params": {ключ: _значення(значення)}})
    шляхи = list(dict.fromkeys(ш.split("[]")[0] + ("[]" if "[]" in ш else "") for ш in шляхи_груп(групи)))
    коди = {ш: _взяти(поля, ш) for ш in шляхи}
    цитати = {}
    for ш in шляхи:
        сире = _взяти(об, ш)
        if isinstance(сире, dict) and коди[ш] not in (КР.UNKNOWN, None, []):
            цитати[ш] = сире.get(КР.ЦИТАТА)
    return коди, цитати, [п for п in причини if not п.startswith("features")]


def _є(код):
    """Чи поле рядка каже щось, крім «невідомо»."""
    return код not in (None, КР.UNKNOWN, [], "")


def речі_з_рядків(рядки_розбору, речі, ід):
    """Коди речей `ід` з їхніх рядків формою `розбір.json` (для `еталон_частки.py`): поле з одним різним
    кодом серед рядків — цей код; з кількома — "unknown" і причина `rows_disagree` (код звіряє коди, не слова)."""
    вих = {}
    for р in ід:
        зібране, причини = {}, []
        for і in речі.get(р, ()):
            for ш, к in ((рядки_розбору.get(і) or {}).get("коди") or {}).items():
                if _є(к):
                    зібране.setdefault(ш, []).append(к)
        запис = {}
        for ш, різні in зібране.items():
            різні = list({json.dumps(к, ensure_ascii=False, sort_keys=True): к for к in різні}.values())
            if ш.endswith("[]") or ш == "set_parts":
                код = list(dict.fromkeys(json.dumps(х, ensure_ascii=False, sort_keys=True) for к in різні for х in к))
                код = [json.loads(х) for х in код]
            elif len(різні) == 1:
                код = різні[0]
            else:
                код = КР.UNKNOWN
                причини.append("rows_disagree · field=%s · codes=%s" % (ш, json.dumps(різні, ensure_ascii=False)))
            ім, *під = ш.replace("[]", "").split(".")
            if під:
                запис.setdefault(ім, {})[під[0]] = код
            else:
                запис[ім] = код
        вих[р] = dict(запис, features="", **{П.ПРИЧИНИ: причини, "рядків": len(речі.get(р, ()))})
    return вих


def зібрати(тека):
    """З журналу теки — `рядки.json` (коди й цитати кожного рядка), `речі.json` (речі еталону з рядків) і
    `прогін.json` (лічба й секунди); без моделі, тож перезбирається будь-коли."""
    рядки_розбору, сек, знаків = {}, [], []
    for (і, _), п in готові(тека).items():
        if п["вид"] != "row":
            continue
        коди, цитати, причини = коди_рядка(п["відповідь"], п["ключ"], п["значення"], п["групи"])
        рядки_розбору[і] = dict(ключ=п["ключ"], значення=п["значення"], групи=п["групи"], коди=коди, цитати=цитати,
                                причини=причини)
        сек.append(п["секунд"])
        знаків.append((п["знаків_запиту"], п["знаків_відповіді"]))
    _, речі = рядки_каталогу()
    речі_ет = речі_з_рядків(рядки_розбору, речі, ід_еталону())
    вс = події(тека)
    лік = dict(рядків=len(рядки_розбору), ключів=sum(1 for п in вс if п.get("вид") == "key" and п.get("стан") == "done"),
               впало=sum(1 for п in вс if п.get("стан") == "failed"),
               кодів=sum(1 for р in рядки_розбору.values() for к in (р["коди"] or {}).values() if _є(к)),
               вигадано=sum(1 for р in рядки_розбору.values() for п in р["причини"] if п.startswith("invented")),
               не_json=sum(1 for р in рядки_розбору.values() if р["коди"] is None),
               секунд_медіана=statistics.median(сек) if сек else None, секунд_усього=round(sum(сек), 1),
               знаків_запиту_медіана=statistics.median(з for з, _ in знаків) if знаків else None,
               знаків_відповіді_медіана=statistics.median(в for _, в in знаків) if знаків else None,
               речей_еталону_з_рядками=sum(1 for в in речі_ет.values() if в["рядків"]))
    _записати(os.path.join(тека, "рядки.json"), рядки_розбору)
    _записати(os.path.join(тека, "речі.json"), речі_ет)
    # Аркуш очима (рядок 6542: нових полів еталон 404 не міряє): кожен код, що не «unknown», — з рядком і цитатою.
    with open(os.path.join(тека, "рядки.tsv.tmp"), "w", encoding="utf-8") as ф:
        ф.write("ключ\tзначення\tполе\tкод\tцитата\n")
        for р in sorted(рядки_розбору.values(), key=lambda р: (р["ключ"], р["значення"])):
            for ш, к in (р["коди"] or {}).items():
                if _є(к):
                    ф.write("\t".join(" ".join(str(х).split()) for х in (р["ключ"], р["значення"], ш,
                            json.dumps(к, ensure_ascii=False) if not isinstance(к, str) else к, р["цитати"].get(ш) or "")) + "\n")
    os.replace(os.path.join(тека, "рядки.tsv.tmp"), os.path.join(тека, "рядки.tsv"))
    _записати(os.path.join(тека, "прогін.json"), dict(лік, версія=ВЕРСІЯ, url=П.АДРЕСА))
    print("зібрано %s: %s" % (тека, json.dumps(лік, ensure_ascii=False)))
    return лік


def main():
    """Командний рядок (див. докстрінг модуля)."""
    а = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    а.add_argument("--модель")
    а.add_argument("--заглушка", action="store_true", help="без моделі: відповідь за граматикою")
    а.add_argument("--куди")
    а.add_argument("--пілот", type=int, help="рядки еталону 404 першими, далі інші сідом 17 до N")
    а.add_argument("--усі", action="store_true", help="усі рядки")
    а.add_argument("--паралельно", type=int, default=П.ПАРАЛЕЛЬНО)
    а.add_argument("--переліки", action="store_true", help="коди переліків і в тексті скелета (порівняння 6202)")
    а.add_argument("--ключі", help="готова мапа ключ → групи (ключі.json іншої теки): без викликів ключів")
    а.add_argument("--стоп-після", type=int, help="штучний обрив після N викликів (перевірка відновлення)")
    а.add_argument("--зібрати", metavar="ТЕКА")
    ар = а.parse_args()
    if ар.зібрати:
        зібрати(ар.зібрати)
        return
    if not ар.куди or not (ар.модель or ар.заглушка) or (ар.пілот is None) == (not ар.усі):
        а.error("треба --куди, --модель (чи --заглушка) і одне з --пілот N / --усі")
    рядки, речі = рядки_каталогу()
    вибрані = вибрати(рядки, речі, None if ар.усі else ар.пілот)
    мапа = None
    if ар.ключі:
        with open(ар.ключі, encoding="utf-8") as ф:
            мапа = json.load(ф)
    try:
        прогін(ар.куди, "заглушка" if ар.заглушка else ар.модель, вибрані, рядки, ар.паралельно, ар.переліки, мапа,
               ар.стоп_після)
    except Обрив:
        print("обрив після %d викликів (--стоп-після): та сама команда докотить прогін" % ар.стоп_після)
        sys.exit(3)


if __name__ == "__main__":
    main()

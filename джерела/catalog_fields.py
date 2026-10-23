"""Поля розбору каталогу: коди, джерела й числові одиниці без читання слів крамниці."""
import math

import каталог_коди as КК
import внутрішня_мова as ВМ
import slots as СЛ

НЕВІДОМО = "unknown"
НЕ_СТОСУЄТЬСЯ = "not_applicable"
НАБОРИ = {"suit": "костюм", "casual_suit": "костюм_повсякденний", "set": "комплект"}
КАНАЛИ = {"women": "жіноче", "men": "чоловіче", "kids": "дитяче", "unisex": "унісекс"}
У_СМ = {"cm": 1, "mm": 0.1, "m": 100, "in": 2.54}
# Чинний мінімальний допуск виміру крамниці (T3); не точність, заявлена моделлю.
ДОПУСК_ДОВЖИНИ_СМ = 2.0


def поля(річ):
    """Повертає повний розбір речі, зберігаючи unknown і not_applicable окремо."""
    розбір = річ.get("розбір")
    розбір = розбір if isinstance(розбір, dict) else КК.поля(річ.get("id"))
    фото = фото_тип(річ)
    if фото and фото.get("status") == "classified" and розбір.get("item_type", НЕВІДОМО) == НЕВІДОМО:
        розбір = dict(розбір, item_type=фото["item_type"], slot=фото["slot"],
                      evidence=dict(розбір.get("evidence") or {}, item_type={"photo": фото["provenance"]}))
    return розбір


def фото_тип(річ):
    """Лише прийнятий контракт фото, прив'язаний до SKU і поточної галереї."""
    import photo_type as ФТ
    запис = ФТ.читати().get(str(річ.get("id")))
    галерея = річ.get("фото")
    if запис and isinstance(галерея, (list, tuple)) and запис["provenance"]["image"]["url"] in галерея:
        return запис
    return None


def значення(річ, шлях):
    """Читає поле чи вкладений код; відсутність — unknown, не заперечення ознаки."""
    з = поля(річ)
    for к in шлях.split("."):
        if not isinstance(з, dict) or к not in з:
            return НЕВІДОМО
        з = з[к]
    return НЕВІДОМО if з is None or з == "" else з


def ключ(річ, шлях, перелік=None):
    """Перетворює код закритого переліку на ключ ядра; стан лишається в повному розборі."""
    з = код(річ, шлях)
    return ВМ.ключ(перелік or шлях, з)


def код(річ, шлях):
    """Читає рядковий код; контейнер чи число замість коду означають unknown."""
    з = значення(річ, шлях)
    return з if isinstance(з, str) else НЕВІДОМО


def ознака(річ, шлях):
    """yes/no → True/False; unknown і not_applicable не перетворюються на істину рядка."""
    return {"yes": True, "no": False}.get(код(річ, шлях))


def число(річ, шлях, одиниця="cm"):
    """Читає вимір розбору з явною одиницею; слова і безрозмірні числа не приймає."""
    з = значення(річ, шлях)
    if not isinstance(з, dict):
        return None
    в, од = з.get("value"), з.get("unit")
    if isinstance(в, bool) or not isinstance(в, (int, float)) or not math.isfinite(в) or в < 0:
        return None
    if одиниця == "cm" and isinstance(од, str) and од in У_СМ:
        return в * У_СМ[од]
    return в if од == одиниця else None


def джерело(річ, шлях):
    """Доказ поля, збережений нормалізатором після звірки цитати з входом моделі."""
    з = поля(річ).get("evidence") or {}
    if not isinstance(з, dict):
        return None
    if шлях in з:
        return з[шлях]
    частини = [д for к, д in з.items() if к.startswith(шлях + "[") and isinstance(д, dict) and д.get("quote")]
    return {"quote": "; ".join(д["quote"] for д in частини),
            "sources": sorted({с for д in частини for с in д.get("sources", [])})} if частини else None


def файли(тека):
    """Входи побудови: відсутній файл теж входить у ключ інвалідації."""
    import os
    import photo_type as ФТ
    return tuple(os.path.join(тека, ім) for ім in (КК.РОЗБІР_ІМ, КК.РОЗБІР_ІМ + ".gz", *ФТ.ФАЙЛИ))


def відбиток():
    """Ключ кеша бази змінюється при появі чи заміні розбору або фото-приймання."""
    import os
    шляхи = файли(os.path.dirname(os.path.abspath(__file__)))
    return tuple((ш, os.stat(ш).st_mtime_ns, os.path.getsize(ш)) if os.path.isfile(ш) else (ш, None) for ш in шляхи)


def код_типу(річ):
    """Відомий код типу з розбору; назва, категорія й старий param тип не є кодовим входом."""
    з = значення(річ, "item_type")
    return з if isinstance(з, str) and з in СЛ.СЛОТ_ТИПУ else НЕВІДОМО


def код_слоту(річ):
    """Слот за єдиною таблицею типів; явно названий набір зберігає власний слот."""
    набір = код(річ, "set_kind")
    if набір in НАБОРИ:
        return "set"
    if набір == "jewelry_set":
        return "jewelry"
    return СЛ.СЛОТ_ТИПУ.get(код_типу(річ), НЕВІДОМО)


def слот(річ, канал="жіноче"):
    """Слот придатної речі за кодами розбору й аудиторії, без словникових запасних шляхів."""
    вид = код(річ, "listing_kind")
    if вид in ВМ.ТАБЛИЦЯ["listing_kind"] and вид != "item":
        return None
    аудиторія = КАНАЛИ.get(код(річ, "audience"))
    if канал and аудиторія and аудиторія not in (канал, "унісекс"):
        return None
    return СЛ.КЛЮЧІ.get(код_слоту(річ))


def джерело_рядком(річ, шлях):
    """Провенанс для старих читачів рядка; самі цитати лишаються в evidence."""
    д = джерело(річ, шлях)
    if isinstance(д, dict) and д.get("quote"):
        return "catalog_parse:%s · %s" % (шлях, д["quote"])
    return "photo_type:item_type" if isinstance(д, dict) and д.get("photo") else None


def перелік(річ, шлях):
    """Список кодів без перетворення unknown на заперечення."""
    з = значення(річ, шлях)
    return tuple(к for к in з if isinstance(к, str)) if isinstance(з, list) else ()


МІРНІСТЬ = {"runs_small": "маломірить", "true_to_size": "повномірить", "runs_large": "великомірить"}
ВИРІЗ = {"round": "круглий", "v_neck": "V-подібний", "deep_v": "глибокий V", "square": "квадратний",
         "boat": "човник", "halter": "халтер", "one_shoulder": "одне плече", "off_shoulder": "відкриті плечі",
         "strapless": "без бретелей", "turtleneck": "гольф", "stand_collar": "стійка",
         "shirt_collar": "сорочковий", "cowl": "хомут"}
РУКАВ = {"sleeveless": "без рукавів", "straps": "бретелі", "cap": "крильце", "short": "короткий",
         "elbow": "до ліктя", "three_quarter": "3/4", "long": "довгий"}
ТКАНИНИ = {"denim": "denim", "jersey": "knit_fine", "knitted": "knit_chunky", "leather": "leather",
           "faux_leather": "leather", "patent_leather": "patent", "satin": "satin", "atlas": "satin",
           "taffeta": "smooth_shine", "silk": "silk_shine", "tweed": "tweed_boucle", "boucle": "tweed_boucle"}
БЛИСК = {"denim": 0, "knit_fine": 0, "knit_chunky": 0, "leather": 1, "patent": 2, "satin": 2,
         "silk_shine": 1, "smooth_matte": 0, "smooth_shine": 1, "tweed_boucle": 0}
БЛИСК_ОЗДОБИ = {"sequins": 3, "rhinestones": 3, "glitter": 3, "lurex": 2, "metallic": 2}
ДЕТАЛІ = {"slit": "з розрізом", "corset": "корсетний", "elastic": "на резинці", "shirt": "сорочковий",
          "peplum": "з басками", "draped": "з драпіруванням", "wrap": "з запахом"}
ВЗУТТЯ = {"vamp": ("виріз_стопи", {"low": "низький", "high": "високий"}),
          "shaft": ("халява_рівень", {"ankle": "щиколотка", "calf": "литка", "knee": "коліно", "thigh": "пах"}),
          "sole": ("підошва", {"smooth": "гладка", "leather": "шкіра", "lug": "трактор",
                                    "polyurethane": "поліуретан", "eva": "eva", "tpr": "tpr"}),
          "shoe_width": ("повнота", {"narrow": "вузька", "medium": "середня", "wide": "широка"}),
          "sole_attachment": ("ремонтопридатна", {"stitched": True, "glued": False})}
ВЕРХНЄ = {"breasted": ("бортність", {"single_breasted": "однобортне", "double_breasted": "двобортне"}),
          "closure": ("застібка", {"zip": "блискавка", "buttons": "ґудзики", "none": "нема"}),
          "collar": ("комір", {"lapel": "ревер", "shawl": "шаль", "turn_down": "відкладний", "none": "без_коміра"}),
          "sleeve_cut": ("рукав", {"set_in": "вшивний", "raglan": "реглан"}),
          "pile": ("ворс", {"teddy": "тедді", "shaggy": "шаггі", "boucle": "букле", "long_pile": "довгий_ворс"}),
          "filling": ("наповнювач", {"down": "пух", "sintepon": "синтепон", "hollofiber": "холофайбер",
                       "isosoft": "ізософт", "wadding": "ватин", "thinsulate": "тінсулейт", "none": False})}


def з_таблиці(річ, таблиця):
    """Проєкція закритих кодів на ключі чинних читачів."""
    return {ім: м.get(код(річ, ш)) for ш, (ім, м) in таблиця.items()}


def тканина(річ):
    """Текстура й блиск за кодами; тафта — тканина, не припущення про поліестер."""
    т = код(річ, "texture")
    поле = "texture"
    if т not in БЛИСК:
        т, поле = ТКАНИНИ.get(код(річ, "fabric")), "fabric"
    б = БЛИСК.get(т)
    оздоба = [БЛИСК_ОЗДОБИ[к] for к in перелік(річ, "decor") if к in БЛИСК_ОЗДОБИ]
    if оздоба:
        б, поле = max(оздоба + ([б] if б is not None else [])), "decor"
    return dict(тканина=т.replace("_", "-") if т else None, блиск=б, за_чим=джерело_рядком(річ, поле))


def мотив(річ):
    """Клас мотиву з pattern; колір і піксельний масштаб сюди не входять."""
    return dict(клас=ключ(річ, "pattern"), за_чим=джерело_рядком(річ, "pattern"))


def збіг_межі(річ, межа, група=None):
    """Точна рівність кодів межі людини та ознак речі, без назви й цитат."""
    if not isinstance(межа, str) or not межа.strip():
        return False
    шляхи = {"типи": (("item_type", "тип"),), "тканини": (("fabric", "волокно"), ("material", "матеріал")),
              "принти": (("pattern", "візерунок"),), "кольори": (("color_name", "колір_ім"),)}
    пари = шляхи.get(група, tuple(п for г in шляхи.values() for п in г))
    for перелік_, ім in пари:
        м = ВМ.код(перелік_, межа) or (межа if межа in ВМ.ТАБЛИЦЯ[перелік_] else None)
        к = код(річ, "color_main" if перелік_ == "color_name" else перелік_)
        if к not in ВМ.ТАБЛИЦЯ[перелік_]:
            к = ВМ.код(перелік_, річ.get(ім))
        if м and к and (м == к or (м == "print_generic" and к not in ("solid", "lace_motif"))):
            return True
    if група is None:
        поля_кодів = ("крій", "текстура", "довжина_рівень", "халява_рівень", "виріз_стопи", "виріз_тип", "відкрита_зона")
        if any(річ.get(п) == межа for п in поля_кодів):
            return True
    return False


def взуттєві(річ):
    """Виміри та конструкція взуття без типових висот, домислених із назви типу."""
    коди = з_таблиці(річ, ВЗУТТЯ)
    в = dict(виріз_стопи=коди["виріз_стопи"], халява_рівень=коди["халява_рівень"],
             халява_джерело=джерело_рядком(річ, "shaft"), підошва=коди["підошва"],
             повнота=коди["повнота"], ремонтопридатна=коди["ремонтопридатна"],
             каблук_від=число(річ, "heel.min_cm"), каблук_до=число(річ, "heel.max_cm"),
             каблук_клас=джерело_рядком(річ, "heel.min_cm") or джерело_рядком(річ, "heel.max_cm"))
    в.update(каблук=ознака(річ, "heel.present"), каблук_см=число(річ, "heel.height_cm"),
             устілка_см=число(річ, "insole_cm"), халява_см=число(річ, "shaft_cm"),
             матеріал_верху=ключ(річ, "material"), розмірність=МІРНІСТЬ.get(код(річ, "size_fit")))
    if в["каблук"] is False:
        в["каблук_см"] = 0.0
    return в


def верхні(річ):
    """Ознаки верхнього шару з відповідних кодів розбору."""
    коди = з_таблиці(річ, ВЕРХНЄ)
    в = dict(бортність=коди["бортність"], застібка=коди["застібка"], комір=коди["комір"],
             рукав=коди["рукав"], ворс=коди["ворс"], наповнювач=коди["наповнювач"],
             пояс=ознака(річ, "belt"), капюшон=ознака(річ, "hood"), опушка=ознака(річ, "fur_trim"),
             простібка=ознака(річ, "quilted"), оверсайз=ознака(річ, "veto.oversize"),
             капюшон_знімний=ознака(річ, "hood_detachable"),
             простібка_орієнтація={"horizontal": "горизонтальна", "diagonal": "нахилена"}.get(код(річ, "quilt_orientation")))
    в["тип_верхнього"] = ключ(річ, "item_type") if код_слоту(річ) == "outerwear" else None
    if код(річ, "neckline") == "stand_collar":
        в["комір"] = "стійка"
    вовна = число(річ, "wool_pct", "percent")
    в["вовна_частка"] = вовна / 100 if вовна is not None else None
    return в


def сезон(річ):
    """Чинні смуги доречності тканини (T3), тепер ключовані кодом fabric."""
    import сценарій as П
    к = код(річ, "fabric")
    if к in ("velour", "velvet", "tweed", "boucle"):
        return (П.МОРОЗ_ДО_C, П.ПАЛЬТО_ДО_C)
    if к in ("wool", "cashmere", "mohair", "angora"):
        return (П.МОРОЗ_ДО_C, П.ЛІТО_ВІД_C)
    if к in ("linen", "chiffon", "batiste", "muslin"):
        return (П.ЛІТО_ВІД_C, 999)
    return None


def проєкція(річ):
    """Повний кодовий вхід і проєкції для чинних правил каталогу; unknown ≠ not_applicable."""
    т, м = тканина(річ), мотив(річ)
    крій = код(річ, "cut")
    рід = {"knit": "трикотаж", "woven": "полотно"}.get(код(річ, "fabric_kind"))
    матеріал_поле = "material" if ключ(річ, "material") else "fabric"
    в = dict(розбір=поля(річ), текстура=т["тканина"], блиск=т["блиск"], тканина_за_чим=т["за_чим"],
             візерунок=м["клас"], візерунок_за_чим=м["за_чим"], візерунок_джерело="catalog_parse" if м["клас"] else None,
             волокно=ключ(річ, "fabric"), матеріал=ключ(річ, матеріал_поле), матеріал_джерело=джерело_рядком(річ, матеріал_поле),
             крій=крій if крій not in (НЕВІДОМО, НЕ_СТОСУЄТЬСЯ) else None, крій_джерело=джерело_рядком(річ, "cut"),
             рід_тканини_слово=рід, рід_тканини_за_чим=джерело_рядком(річ, "fabric_kind"),
             виріз_тип=ВИРІЗ.get(код(річ, "neckline")), рукав_слово=РУКАВ.get(код(річ, "sleeve")),
             розмірність=МІРНІСТЬ.get(код(річ, "size_fit")), довжина=ключ(річ, "length"),
             довжина_джерело=джерело_рядком(річ, "length"), довжина_виробу_см=число(річ, "length_cm"),
             довжина_виробу_джерело=джерело_рядком(річ, "length_cm"),
             метал=ключ(річ, "metal"), формат={"small": "маленький", "medium": "середній", "large": "великий"}.get(код(річ, "bag_size")),
             ланцюг_см=число(річ, "chain_cm"), den=число(річ, "den", "den"))
    в["сезон_тканини"] = сезон(річ)
    в["сезон_за_чим"] = джерело_рядком(річ, "fabric") if в["сезон_тканини"] else None
    в["еластан_%"] = число(річ, "elastane_pct", "percent")
    в["еластан_джерело"] = джерело_рядком(річ, "elastane_pct")
    в["еластан_за_чим"] = в["еластан_джерело"]
    в["матеріал_за_чим"] = в["матеріал_джерело"]
    в["рід_за_чим"] = в["рід_тканини_за_чим"]
    в["крій_за_чим"] = в["крій_джерело"]
    в["довжина_рівень"] = в["довжина"]
    в["рукав_рівень"] = в["рукав_слово"]
    в["довжина_виробу_розкид_см"] = ДОПУСК_ДОВЖИНИ_СМ if в["довжина_виробу_см"] is not None else None
    в["довжина_виробу_точка"] = {"shoulder": "плечі", "waist": "талія", "inseam": "пах"}.get(код(річ, "length_anchor"))
    в["довжина_виробу_за_чим"] = в["довжина_виробу_джерело"]
    в["фото_тип"] = фото_тип(річ)
    в["ремінь_см"] = число(річ, "strap_cm") / 2 if число(річ, "strap_cm") is not None else None
    в["деталі_крою"] = [ДЕТАЛІ[к] for к in перелік(річ, "cut_details") if к in ДЕТАЛІ]
    в["талія"] = ("elastic_waist" if ознака(річ, "elastic_waist") is True else
                  "belt" if ознака(річ, "belt") is True else "wrap" if крій == "wrap" else None)
    в.update(верхні(річ))
    if код_слоту(річ) == "shoes":
        в.update(взуттєві(річ))
    # Кожне поле розбору має власний стовпець у таблиці, повний запис зберігає провенанс.
    в.update({"код_" + к: з for к, з in поля(річ).items() if к not in ("features", "evidence")})
    return в

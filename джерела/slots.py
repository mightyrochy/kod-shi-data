# -*- coding: utf-8 -*-
"""Коди, назви, порядок і групи слотів для каталогу, образу й внутрішньої мови."""

КЛЮЧІ = {
    "top": "верх", "bottom": "низ", "dress": "сукня", "set": "комплект",
    "outerwear": "верхній_шар", "shoes": "взуття", "bag": "сумка", "scarf": "шарф",
    "headwear": "головний_убір", "belt": "пояс", "tights": "колготи", "socks": "шкарпетки",
    "jewelry": "прикраси", "earrings": "сережки", "collar_necklace": "кольє",
    "necklace": "намисто", "brooch": "брошка", "bracelet": "браслет", "ring": "каблучка",
    "glasses": "окуляри", "gloves": "рукавички", "watch": "годинник", "swimwear": "купальник",
    "underwear": "білизна", "accessory": "аксесуар",
}


def _слоти(*коди):
    """Повертає назви слотів у заданому порядку кодів."""
    return tuple(КЛЮЧІ[код] for код in коди)


# Будова образу. Порядок у типових слотах, графі та пакеті визначає порядок обходу.
ВЕРХ_І_НИЗ = _слоти("top", "bottom")
ЦІЛЬНИЙ_ОДЯГ = _слоти("dress", "set")
ВЗУТТЯ_І_СУМКА = _слоти("shoes", "bag")
БАЗОВИЙ_ОДЯГ = ВЕРХ_І_НИЗ + ЦІЛЬНИЙ_ОДЯГ
# Блокер починає з цільного одягу.
БАЗОВИЙ_ОДЯГ_ВІД_ЦІЛОГО = ЦІЛЬНИЙ_ОДЯГ + ВЕРХ_І_НИЗ
СЛОТИ_З_ПОДОЛОМ = _слоти("bottom") + ЦІЛЬНИЙ_ОДЯГ
# Ремонт силуету спершу перебирає речі з подолом.
БАЗОВИЙ_ОДЯГ_ВІД_НИЗУ = СЛОТИ_З_ПОДОЛОМ + _слоти("top")
# Основні площини одягу для кольору, покриття й силуету.
ВЕЛИКІ_ПОВЕРХНІ = БАЗОВИЙ_ОДЯГ + _слоти("outerwear")
КОМПЛЕКТ_І_ВЕРХ = _слоти("set", "top")
ВЕРХ_НИЗ_І_ВЗУТТЯ = ВЕРХ_І_НИЗ + _слоти("shoes")
СЛОТИ_ТИПОВОГО_ОБРАЗУ = ВЕРХ_І_НИЗ + ВЗУТТЯ_І_СУМКА
СЛОТИ_ВИМІРУ_ОСОБИ = ВЕРХ_І_НИЗ + _слоти("dress", "outerwear") + ВЗУТТЯ_І_СУМКА
СЛОТИ_ГРАФА = ВЕЛИКІ_ПОВЕРХНІ + ВЗУТТЯ_І_СУМКА + _слоти(
    "scarf", "headwear", "belt", "tights", "socks", "earrings", "collar_necklace", "necklace",
    "brooch", "bracelet", "ring", "glasses",
)
СЛОТИ_ПАКЕТА = ВЕЛИКІ_ПОВЕРХНІ + ВЗУТТЯ_І_СУМКА + _слоти(
    "belt", "headwear", "scarf", "jewelry", "earrings", "necklace", "collar_necklace", "bracelet", "ring", "brooch",
)
СЛОТИ_ЧИПІВ_ОЦІНКИ = _слоти("top", "bottom", "dress", "outerwear", "shoes", "bag", "scarf", "headwear", "belt",
                            "jewelry")
НЕОБОВЯЗКОВІ_СЛОТИ_КОМПОЗИТОРА = _слоти("outerwear", "shoes", "bag", "scarf", "jewelry", "headwear", "belt",
                                        "tights", "socks", "earrings", "necklace", "collar_necklace", "bracelet",
                                        "ring", "brooch", "glasses", "dress", "set")
СЛОТИ_БЛОКЕРА_НЕПОВНОТИ = _слоти("outerwear", "jewelry", "earrings", "collar_necklace", "necklace", "bracelet",
                                 "ring", "brooch", "belt", "scarf", "headwear")
# Структура образу приймає також успадкований слот «шар2».
СЛОТИ_ТРЕТЬОЇ_РЕЧІ_ОБРАЗУ = (
    _слоти("outerwear")
    + ("шар2",)
    + _слоти(
        "jewelry", "belt", "scarf", "headwear", "earrings", "necklace", "collar_necklace",
        "bracelet", "brooch", "ring", "glasses", "watch", "gloves",
    )
)
# Суд ремесла окремо бачить підвіску.
СЛОТИ_ТРЕТЬОЇ_РЕЧІ_РЕМЕСЛА = (
    _слоти(
        "outerwear", "scarf", "belt", "headwear", "jewelry", "earrings", "necklace", "collar_necklace",
        "ring", "bracelet", "brooch", "watch", "glasses",
    )
    + ("підвіска",)
)
# Контрольна рука впізнає також успадкований слот «комбінезон».
СЛОТИ_ТІЛА_ПОЛОМОК = _слоти("top", "bottom", "dress", "outerwear") + ("комбінезон",)
СЛОТИ_ПРИКРАС_ПОЛОМОК = _слоти("earrings", "necklace", "collar_necklace", "bracelet", "ring")


# Посадка, край і шари. Комплект або верхній шар входять лише там, де правило читає їхню геометрію.
СЛОТИ_ВЕРХІВ = _слоти("top", "outerwear")
СЛОТИ_ВЕРХІВ_ВІД_ШАРУ = СЛОТИ_ВЕРХІВ[::-1]
ОДЯГ_ПІД_ШАРОМ = _слоти("top", "dress", "set", "bottom")
СЛОТИ_ШАРІВ = СЛОТИ_ВЕРХІВ + ЦІЛЬНИЙ_ОДЯГ
СЛОТИ_ВНУТРІШНЬОГО_ВЕРХУ = _слоти("top") + ЦІЛЬНИЙ_ОДЯГ
СЛОТИ_ГОРЛОВИНИ_БЕЗ_КОМПЛЕКТУ = _слоти("top", "dress")
СЛОТИ_ГОРЛОВИНИ_ВІД_СУКНІ = СЛОТИ_ГОРЛОВИНИ_БЕЗ_КОМПЛЕКТУ[::-1]
СЛОТИ_КАСКАДУ = СЛОТИ_ВЕРХІВ + _слоти("dress")
СЛОТИ_НИЗУ_БЕЗ_КОМПЛЕКТУ = _слоти("dress", "bottom")
СЛОТИ_НИЗУ_БЕЗ_КОМПЛЕКТУ_ВІД_НИЗУ = СЛОТИ_НИЗУ_БЕЗ_КОМПЛЕКТУ[::-1]
СЛОТИ_КРОЮ_БЕЗ_КОМПЛЕКТУ = СЛОТИ_ВЕРХІВ + СЛОТИ_НИЗУ_БЕЗ_КОМПЛЕКТУ_ВІД_НИЗУ
СЛОТИ_КРОЮ_БЕЗ_КОМПЛЕКТУ_ВІД_НИЗУ = СЛОТИ_НИЗУ_БЕЗ_КОМПЛЕКТУ_ВІД_НИЗУ + СЛОТИ_ВЕРХІВ
СЛОТИ_НИЖНЬОГО_КРАЮ = СЛОТИ_З_ПОДОЛОМ + _слоти("outerwear")
СЛОТИ_ПОСАДКИ_НИЗУ = _слоти("bottom", "set")
СЛОТИ_ОБГОРТКИ_СИЛУЕТУ = ВЕЛИКІ_ПОВЕРХНІ + _слоти("tights")
СЛОТИ_ТАЛІЇ_ДЕТАЛЛЮ = _слоти("dress", "outerwear")
СЛОТИ_ПОВНИХ_ВИМІРІВ_ФОТО = ЦІЛЬНИЙ_ОДЯГ + _слоти("outerwear")
ОКРЕМІ_СЛОТИ_ОДЯГУ = ВЕРХ_І_НИЗ + _слоти("outerwear")
СЛОТИ_РОЗМІРІВ_ОДЯГУ = _слоти("top", "bottom", "dress", "outerwear", "set")


# Аксесуари. Місце носіння, вимір, ціна й матеріал мають власні набори.
# Загальний слот прикрас також містить тканинні обручі й резинки.
СЛОТИ_КОНКРЕТНИХ_ПРИКРАС = _слоти("earrings", "necklace", "collar_necklace", "bracelet", "ring", "brooch")
СЛОТИ_ПРИКРАС = _слоти("jewelry") + СЛОТИ_КОНКРЕТНИХ_ПРИКРАС
ЮВЕЛІРНІ_СЛОТИ = _слоти("jewelry", "earrings", "necklace", "collar_necklace", "ring", "bracelet", "watch", "brooch")
СЛОТИ_ЛАНЦЮГА = _слоти("jewelry", "collar_necklace", "necklace")
# Аксесуари зі структурною роллю в образі.
СЛОТИ_АКСЕСУАРІВ = _слоти("bag", "scarf", "jewelry", "belt", "headwear", "earrings", "necklace", "collar_necklace",
                          "bracelet", "ring", "brooch")
АКСЕСУАРИ_БІЛЯ_ОБЛИЧЧЯ = _слоти("scarf", "glasses")
АКСЕСУАРИ_З_КІЛЬКОМА_МІСЦЯМИ = _слоти("scarf", "bag")
СЛОТИ_БЕЗ_ВИМІРУ_БІЛЯ_ОБЛИЧЧЯ = _слоти("bag", "jewelry")
СЛОТИ_ЗНІМНИХ_АКЦЕНТІВ = _слоти("jewelry", "bag", "scarf", "headwear", "belt", "watch", "glasses")
СЛОТИ_КІЛЬКОСТІ_АКЦЕНТІВ = СЛОТИ_ЗНІМНИХ_АКЦЕНТІВ + _слоти("outerwear")
СЛОТИ_ЦІНИ_АКСЕСУАРА = _слоти("bag", "scarf", "jewelry", "belt", "headwear", "shoes")
СЛОТИ_ЦІНИ_З_ГОДИННИКОМ = _слоти("bag", "scarf", "jewelry", "belt", "headwear", "watch", "glasses", "shoes")
ДРІБНІ_СЛОТИ_МАСОК = set(_слоти("belt", "shoes", "headwear", "scarf", "bag"))
ДРІБНІ_ЗІ_ШКАРПЕТКАМИ = _слоти("shoes", "bag", "belt", "scarf", "headwear", "socks")
СЛОТИ_ПОЛЯ_МЕТАЛУ = _слоти("belt", "bag")
СЛОТИ_МЕТАЛУ_ОБРАЗУ = СЛОТИ_ПРИКРАС + СЛОТИ_ПОЛЯ_МЕТАЛУ
СЛОТИ_МЕТАЛУ_ФІДУ = (
    _слоти("earrings", "collar_necklace", "necklace", "bracelet", "ring", "jewelry")
    + ("підвіска",)
    + _слоти("brooch")
)
# Набори полів фіду також використовуються в об’єднанні.
МЕТАЛ_СЛОТИ = set(СЛОТИ_МЕТАЛУ_ФІДУ)
МЕТАЛ_СЛОТИ_ПОЛЕ = set(СЛОТИ_ПОЛЯ_МЕТАЛУ)
СЛОТИ_ШКІРЯНОЇ_ОСНОВИ = _слоти("shoes", "bag", "belt")


# Колір. Порядок акцентних слотів розв'язує рівність при відборі.
СЛОТИ_АКЦЕНТІВ_З_ТКАНИНИ = _слоти("scarf", "headwear", "belt")
СЛОТИ_БЕЗ_ВІКНА_КОЛЬОРУ = _слоти("belt") + СЛОТИ_ПРИКРАС + _слоти("scarf")
# Перелік для суду принтів.
СЛОТИ_АКСЕСУАРНОГО_ПРИНТУ = _слоти("bag", "shoes", "belt", "scarf", "jewelry", "headwear")
# Короткий перелік палітри ставить пояс після прикрас.
СЛОТИ_КОРОТКОГО_АКЦЕНТУ = _слоти("bag", "shoes", "scarf", "jewelry", "belt", "headwear")
СЛОТИ_ЯКОРЯ_КОЛЬОРУ = _слоти("shoes", "bag", "belt", "tights")
ПОРЯДОК_АКЦЕНТНИХ_СЛОТІВ = _слоти("bag", "shoes", "belt", "scarf", "headwear", "jewelry", "necklace",
                                  "collar_necklace", "earrings", "bracelet", "ring", "brooch")
ЗНІМНІ_СЛОТИ_КОЛЬОРУ = _слоти("jewelry", "scarf", "belt", "bag", "headwear", "outerwear")
# Траурний регістр перебирає сукню й комплект перед окремими частинами.
ВЕЛИКІ_ПОВЕРХНІ_ТРАУРУ = БАЗОВИЙ_ОДЯГ_ВІД_ЦІЛОГО + _слоти("outerwear")
СЛОТИ_ТРАУРНОГО_РЕГІСТРУ = ВЕЛИКІ_ПОВЕРХНІ_ТРАУРУ + ВЗУТТЯ_І_СУМКА + _слоти("belt", "scarf", "headwear")


# Погода й покриття. Окремі перевірки взуття, головного убору й одягу читають власні умови сезону.
АКСЕСУАРИ_ЧУТЛИВІ_ДО_ВОЛОГИ = ВЗУТТЯ_І_СУМКА + _слоти("gloves")
АКСЕСУАРИ_ПОГОДИ = _слоти("headwear", "scarf", "gloves", "bag")
СЛОТИ_ВЛАСНИХ_УМОВ_СЕЗОНУ = БАЗОВИЙ_ОДЯГ + _слоти("headwear", "shoes")
СЛОТИ_ВЕРХНЬОГО_ВИХОДУ = ВЗУТТЯ_І_СУМКА + _слоти("outerwear")
СЛОТИ_ГОЛОВИ_І_ШИЇ = _слоти("headwear", "scarf")
# У вимірі тепла збережені успадковані «шапка» та «рукавиці».
СЛОТИ_РУКАВИЦЬ = ("рукавиці",) + _слоти("gloves")
АКСЕСУАРИ_ХОЛОДУ = ("шапка",) + СЛОТИ_ГОЛОВИ_І_ШИЇ + СЛОТИ_РУКАВИЦЬ


# Коди слота для наявності полів запису каталогу й застосовності знань про річ.
КОДИ_СЛОТІВ_ВЕРХІВ = ("top", "outerwear")
КОДИ_СЛОТІВ_ГОРЛОВИНИ_БЕЗ_КОМПЛЕКТУ = ("top", "dress")
КОДИ_СЛОТІВ_ПРИКРАС = ("jewelry", "necklace", "collar_necklace", "bracelet", "earrings", "brooch", "ring")
КОДИ_ЮВЕЛІРНИХ_СЛОТІВ = ("jewelry", "earrings", "collar_necklace", "necklace", "brooch", "bracelet", "ring", "watch")
КОДИ_ТКАНИННИХ_СЛОТІВ = ("top", "bottom", "dress", "set", "outerwear", "scarf", "headwear", "gloves", "tights",
                         "socks", "underwear", "swimwear")
КОДИ_ДРІБНИХ_СЛОТІВ_КАТАЛОГУ = ("scarf", "headwear", "belt", "tights", "socks", "glasses", "gloves")
КОДИ_ВИНЯТКІВ_З_ПОЛІВ_КАТАЛОГУ = ("shoes", "accessory")
КОДИ_СЛОТІВ_БЕЗ_КРОЮ = ("shoes", "bag") + КОДИ_ЮВЕЛІРНИХ_СЛОТІВ + КОДИ_ДРІБНИХ_СЛОТІВ_КАТАЛОГУ
КОДИ_СЛОТІВ_БЕЗ_РУКАВА = ("bottom",) + КОДИ_СЛОТІВ_БЕЗ_КРОЮ
КОДИ_СЛОТІВ_БЕЗ_ТКАНИНИ = КОДИ_ЮВЕЛІРНИХ_СЛОТІВ + ("glasses", "shoes", "bag", "belt")
КОДИ_ТВЕРДИХ_І_ТОНКИХ_СЛОТІВ = КОДИ_ЮВЕЛІРНИХ_СЛОТІВ + ("glasses", "tights", "socks")
КОДИ_ПОЛЯ_МЕТАЛУ = ("belt", "bag")
КОДИ_СЛОТІВ_БЕЗ_МЕТАЛУ_ПРИКРАС = ("top", "bottom", "dress", "set", "outerwear", "shoes", "bag", "socks", "tights",
                                  "swimwear", "underwear")
КОДИ_ГРУП_КАТАЛОГУ = ("top", "bottom", "dress", "outerwear", "shoes", "bag")
# Публічна полиця чергує крамниці в порядку власних категорій, де coat, jewels і hat — групи пошуку.
ПОРЯДОК_КАТЕГОРІЙ_ПОШУКУ = ("dress", "top", "bottom", "coat", "shoes", "bag", "jewels", "scarf", "set", "belt", "hat")
# Каталожні групи ставлять кольє останнім.
ПОРЯДОК_ГРУПИ_ПРИКРАС_КАТАЛОГУ = _слоти("jewelry", "earrings", "necklace", "bracelet", "ring", "brooch",
                                        "collar_necklace")


_SLOT_TYPES = {
    "dress": ("evening_dress", "cocktail_dress", "sheath_dress", "sundress", "jumpsuit", "dress_generic"),
    "set": ("suit", "casual_suit", "two_piece_set"),
    "shoes": ("ugg_boots", "over_knee_boots", "chelsea_boots", "ballet_flats", "mules", "espadrilles", "pumps", "dress_shoes", "moccasins", "loafers", "sneakers", "plimsolls", "ankle_boots", "boots", "heeled_sandals", "sandals"),
    "bag": ("clutch", "backpack", "tote", "baguette_bag", "hobo_bag", "crossbody_bag", "bucket_bag", "belt_bag", "briefcase", "saddle_bag", "bag_generic"),
    "top": ("hoodie", "sportswear", "loungewear", "t_shirt", "shirt", "blouse", "knitwear", "cardigan", "sweater", "bodysuit", "longsleeve", "vest", "top_garment"),
    "bottom": ("leggings", "jeans", "shorts", "skirt", "trousers"),
    "outerwear": ("coat", "trench_coat", "jacket", "blazer", "half_coat", "down_jacket", "fur_coat", "sheepskin_coat", "parka", "raincoat", "rain_cape", "windbreaker", "anorak", "bomber", "poncho"),
    "scarf": ("stole", "kerchief", "twilly", "snood", "shawl", "bactus_scarf", "scarf_generic"),
    "headwear": ("headband", "bow", "hair_clip", "hair_tie", "beanie", "hat", "beret", "cap"),
    "belt": ("belt",), "earrings": ("earrings",), "bracelet": ("bracelet",),
    "necklace": ("necklace",), "collar_necklace": ("collar_necklace",), "brooch": ("brooch",),
    "watch": ("watch",), "glasses": ("glasses",), "gloves": ("gloves",), "tights": ("tights",),
    "socks": ("socks",), "swimwear": ("swimsuit",), "underwear": ("lingerie",),
    "ring": ("ring",), "jewelry": ("jewelry_generic",),
}

СЛОТ_ТИПУ = {t: s for s, types in _SLOT_TYPES.items() for t in types}
ДВОСЛОТОВІ_ТИПИ = {
    тип: КОДИ_СЛОТІВ_ВЕРХІВ for тип in ("cardigan", "blazer", "vest", "poncho")
} | {
    тип: ("headwear", "jewelry") for тип in ("headband", "bow", "hair_clip", "hair_tie")
}

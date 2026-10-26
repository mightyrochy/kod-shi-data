# -*- coding: utf-8 -*-
"""Єдина таблиця виду та слота для каталогу й внутрішньої мови."""

КЛЮЧІ = {
    "top": "верх", "bottom": "низ", "dress": "сукня", "set": "комплект",
    "outerwear": "верхній_шар", "shoes": "взуття", "bag": "сумка", "scarf": "шарф",
    "headwear": "головний_убір", "belt": "пояс", "tights": "колготи", "socks": "шкарпетки",
    "jewelry": "прикраси", "earrings": "сережки", "collar_necklace": "кольє",
    "necklace": "намисто", "brooch": "брошка", "bracelet": "браслет", "ring": "каблучка",
    "glasses": "окуляри", "gloves": "рукавички", "watch": "годинник", "swimwear": "купальник",
    "underwear": "білизна", "accessory": "аксесуар",
}

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
    "cardigan": ("top", "outerwear"), "blazer": ("top", "outerwear"),
    "vest": ("top", "outerwear"), "poncho": ("top", "outerwear"),
    "headband": ("headwear", "jewelry"), "bow": ("headwear", "jewelry"),
    "hair_clip": ("headwear", "jewelry"), "hair_tie": ("headwear", "jewelry"),
}

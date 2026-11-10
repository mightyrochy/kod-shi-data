"""Крок 26, 14003 (рішення менеджера 07.11): сім'я блоку ISCC-NBS на межі brown ↔ red у темних — за більшістю назв
практиків, які блоку дає розд. 14 NBS SP 440 (`розділ14_блоки.txt`, дослівно з OCR archive.org).

Назву відносять до сім'ї за ГОЛОВНИМ словом кольору — останнім словом зі словника нижче («Red Mahogany», «Reddish
Brown» — бура; «Brownish Red», «Wine Red» — червона). Матеріал і пігмент (lake, oxide, earth, ochre) і місце (Indian,
Venetian, Pompeii) — не слово кольору; назва без слова зі словника — «—» і лишається в знаменнику. Вино й бордо
(wine, claret, burgundy, maroon, port, лат. vinosus) — червона, як і K-COL-06 не має бордо серед нейтралей (рішення
07.11). Блок — тієї сім'ї, якій належить БІЛЬШЕ ПОЛОВИНИ всіх його назв; нема — лишається за ISCC-NBS.

python3 аудит/перевірка/річ_колір_межі_крок26/розділ14.py [--назви 41 44]"""
import collections
import re
import sys
from pathlib import Path

ТЕКСТ = Path(__file__).with_name("розділ14_блоки.txt")
ДЖЕРЕЛА = ("Maerz and Paul", "Plochere", "Ridgway", "Taylor, Knoche, Granville", "Textile Color Card Association",
           "Other sources")
СЛОВНИК = {
    "red": "red reddish scarlet crimson vermilion vermillion carmine maroon wine claret burgundy garnet ruby cardinal "
           "rouge vinaceous vinosus vinoso subvinoso atrovinosus sanguineus sanguine ruber oxblood port oporto cerise "
           "cherry madder",
    "brown": "brown brownish brunneo mahogany chocolate chestnut castaneus russet cordovan umber sienna siena sepia "
             "cocoa coffee tan fawn cinnamon rust bay badius auburn henna acajou castor taupe drab",
    "pink": "pink pinkish rose coral blush cameo salmon peach",
    "purple": "purple purplish violet lilac mauve plum mulberry amethyst lavender aubergine",
    "orange": "orange flame",
    "gray": "gray grey griseus ash slate livid lividus",
    "black": "black blackish ebony",
}
СІМ_Я_СЛОВА = {слово: сім_я for сім_я, слова in СЛОВНИК.items() for слово in слова.split()}
# сім'я таблиці `колір_сім_ї_вікна.md` до кроку 26 — для блоків, які тут лічимо
ТАБЛИЦЯ = {**{н: "red" for н in range(11, 22) if н != 18}, 18: "pink", **{н: "achromatic" for н in (22, 23, 24)},
           **{н: "brown" for н in range(40, 48)}}


def блоки(текст=None):
    """{номер блоку: [рядки назв]} — заголовок «N. НАЗВА БЛОКУ», рядки джерел і номери сторінок відкинуто."""
    поточний, вихід = None, collections.defaultdict(list)
    for рядок in (текст or ТЕКСТ.read_text(encoding="utf-8")).splitlines():
        с = re.sub(r"\s+", " ", рядок).strip()
        if not с or с.startswith("#"):
            continue
        м = re.match(r"^([0-9][0-9.]*)\s+([A-Z][A-Z \-]+)$", с)
        if м:
            номер = {"4.1": "43"}.get(м.group(1).rstrip("."), м.group(1).rstrip("."))   # OCR: «4.1.» — заголовок 43
            if номер.isdigit():
                поточний = int(номер)
                continue
        if re.fullmatch(r"[0-9]+", с) or re.fullmatch(r"[A-Z ]+", с) or поточний is None:
            continue                                   # номер сторінки чи хвіст заголовка («BROWN»)
        if any(с.startswith(д) for д in ДЖЕРЕЛА) or re.fullmatch(r"\([A-Za-z]+\)\.?", с):
            continue                                   # назва джерела чи перенесений хвіст «(MA)»
        вихід[поточний].append(с)
    return вихід


def сім_я_назви(назва):
    """Сім'я головного слова кольору назви або «—»."""
    без_дужок = re.sub(r"\(.*?\)", " ", назва)
    слова = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", без_дужок)      # «RedBoottopping» → Red, Boottopping
    сім_ї = [СІМ_Я_СЛОВА[с.lower()] for с in слова if с.lower() in СІМ_Я_СЛОВА]
    return сім_ї[-1] if сім_ї else "—"


def вердикт(назви):
    """(сім'я більшості чи None, Counter сімей, усього назв)."""
    лік = collections.Counter(сім_я_назви(н) for н in назви)
    сім_я, число = лік.most_common(1)[0] if лік else ("—", 0)
    return (сім_я if сім_я != "—" and 2 * число > len(назви) else None), лік, len(назви)


def головна():
    б = блоки()
    if "--назви" in sys.argv:
        for н in (int(x) for x in sys.argv[sys.argv.index("--назви") + 1:]):
            print(н, " | ".join(f"{с} ⟨{сім_я_назви(с)}⟩" for с in б[н]))
        return
    print("блок · таблиця · назв · сім'ї назв · більшість → сім'я модуля")
    for н in sorted(б):
        сім_я, лік, усього = вердикт(б[н])
        було = ТАБЛИЦЯ.get(н, "?")
        межа = {було, сім_я or було} <= {"red", "brown"}      # крок рішає лише межу brown ↔ red
        стане = (сім_я or було) if межа else було
        хвіст = "  ЗМІНА" if стане != було else ("" if межа else f"  (поза межею brown ↔ red: {було} лишається)")
        print(f"{н} · {було} · {усього} · " + ", ".join(f"{с} {ч}" for с, ч in лік.most_common())
              + f" · {сім_я or 'нема'} → {стане}{хвіст}")


if __name__ == "__main__":
    головна()

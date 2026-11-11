"""Крок 27 (рішення менеджера 08.11, п.4): чи беж, кемел і хакі K-COL-06 цілком у нейтральних сім'ях модуля — за
назвами практиків розд. 14 NBS SP 440 (Kelly–Judd 1976) по всіх 267 блоках (`розділ14_усі_блоки.txt`, дослівно з OCR
archive.org; виправлено лише зіпсовані заголовки — шапка файлу).

Лічба та сама, що в кроці 26 (`../річ_колір_межі_крок26/розділ14.py`): назву бере блок, під заголовком якого її
наводить джерело; сім'я блоку — таблиця модуля `джерела/колір_сім_ї_вікна.md`. Тут ще джерело кожної назви: п'ять
колірних систем розділу (Maerz & Paul, Plochere, Ridgway, Taylor–Knoche–Granville, TCCA) й «Other sources».

Роль нейтралі K-COL-06 поза нейтральними сім'ями (`ролі_нейтралі` генератора) — блоки, де колірна система наводить
саму назву (слово без іншого слова кольору: «Navy 1», «Cream 9D2», «Beige 11C2»; «Navy Blue», «Rose Beige», «Cream-Buff» —
інша назва), у сім'ї, де таких блоків слова найбільше. Правило звірено на ролях кроку 26: воно дає рівно нейві
{183, 187, 188, 201} (230 і 229 — фіолетова сім'я; 200, 204, 179 — лише «Navy Blue», «Bright/Light Navy») і
кремовий {89} (90 — лише «Cream» федеральних стандартів з «Other sources»; 92 — ахроматична).

python3 аудит/перевірка/річ_колір_межі_крок27/розділ14_нейтралі.py [--назви]"""
import collections
import re
import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела" / "лабораторія"))
import колір_сім_ї_межі as МЕЖІ   # noqa: E402

ТЕКСТ = Path(__file__).with_name("розділ14_усі_блоки.txt")
СИСТЕМИ = ("Maerz and Paul", "Plochere", "Ridgway", "Taylor, Knoche, Granville", "Textile Color Card Association")
ІНШІ = "Other sources"
НЕЙТРАЛЬНІ = ("achromatic", "brown", "olive")          # `сім_ї_нейтралі` генератора
СЛОВА = {"Navy": r"navy", "Cream": r"cream", "Beige": r"beige", "Camel": r"camel(?!lia)", "Khaki": r"khaki"}
РОЛІ_КРОКУ_26 = {"Navy": {183, 187, 188, 201}, "Cream": {89}}


def блоки(текст=None):
    """{номер блоку: [(джерело, рядок назви)]} — як `розділ14.блоки` кроку 26, але з джерелом назви."""
    поточний, джерело, вихід = None, None, collections.defaultdict(list)
    for рядок in (текст or ТЕКСТ.read_text(encoding="utf-8")).splitlines():
        с = re.sub(r"\s+", " ", рядок).strip()
        if not с or с.startswith("#"):
            continue
        м = re.match(r"^([0-9][0-9.]*)\s+([A-Z][A-Z \-]+)$", с)
        if м:
            номер = {"4.1": "43"}.get(м.group(1).rstrip("."), м.group(1).rstrip("."))
            if номер.isdigit():
                поточний, джерело = int(номер), None
                continue
        if re.fullmatch(r"[0-9]+", с) or re.fullmatch(r"[A-Z ]+", с) or поточний is None:
            continue
        знайдене = [д for д in СИСТЕМИ + (ІНШІ,) if с.startswith(д)]
        if знайдене:
            джерело = знайдене[0]
            continue
        if re.fullmatch(r"\([A-Za-z]+\)\.?", с):
            continue
        вихід[поточний].append((джерело, с))
    return вихід


def сама_назва(рядок, слово):
    """Рядок — сама назва `слово` (далі код зразка, номер чи позначка джерела, а не інше слово)."""
    м = re.match(r"^%s(?:s)?(?:\.|\b|(?=[gm]\b))\s*(.*)$" % СЛОВА[слово], рядок, re.I)
    if not м or re.match(r"^%s-" % СЛОВА[слово], рядок, re.I):   # «Cream-Buff» — інша назва
        return False
    далі = м.group(1)
    return not re.match(r"^[A-Z][a-z]+|^[A-Z][a-z]*-", далі)


def main():
    _, власник = МЕЖІ.прочитати_сім_ї(МЕЖІ.ТАБЛИЦЯ.read_text(encoding="utf-8"))
    б = блоки()
    print("блоків %d, назв %d" % (len(б), sum(len(v) for v in б.values())))
    for слово, шаблон in СЛОВА.items():
        усі = {н: [(д, р) for д, р in v if re.search(r"\b" + шаблон, р, re.I)] for н, v in б.items()}
        усі = {н: v for н, v in усі.items() if v}
        за_сім = collections.Counter()
        for н, v in усі.items():
            за_сім[власник[н]] += len(v)
        поза = {н: v for н, v in усі.items() if власник[н] not in НЕЙТРАЛЬНІ}
        самі = {н: [р for д, р in v if д in СИСТЕМИ and сама_назва(р, слово)] for н, v in поза.items()}
        самі = {н: v for н, v in самі.items() if v}
        сім_ї = collections.Counter(власник[н] for н in самі)
        роль_сім = сім_ї.most_common(1)[0][0] if сім_ї else None
        роль = sorted(н for н in самі if власник[н] == роль_сім)
        print("\n%s: назв %d — %s" % (слово, sum(len(v) for v in усі.values()),
                                       ", ".join("%s %d" % кв for кв in за_сім.most_common())))
        print("  у нейтральних сім'ях модуля: %d з %d" % (sum(len(v) for н, v in усі.items() if власник[н] in НЕЙТРАЛЬНІ),
                                                        sum(len(v) for v in усі.values())))
        for н in sorted(поза):
            print("  поза: %d %s (%d з %d назв блоку): %s" % (н, власник[н], len(поза[н]), len(б[н]),
                                                            "; ".join("%s — %s" % (р, д or "?") for д, р in поза[н])))
        print("  сама назва колірної системи поза нейтральними: %s → роль: %s %s" % (
            {н: самі[н] for н in sorted(самі)}, роль_сім, роль))
        if слово in РОЛІ_КРОКУ_26:
            print("  звірка з роллю кроку 26 %s: %s" % (sorted(РОЛІ_КРОКУ_26[слово]),
                                                     "збіг" if set(роль) == РОЛІ_КРОКУ_26[слово] else "РОЗХОДИТЬСЯ"))
        if "--назви" in sys.argv:
            for н in sorted(усі):
                print("   %d %s: %s" % (н, власник[н], "; ".join(р for _, р in усі[н])))


if __name__ == "__main__":
    main()

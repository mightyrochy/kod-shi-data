"""Спроба 7: модель відповідає ознаками з коротких закритих переліків, код блоку складає таблиця словника без фото.

Крок 1 (усі кадри галереї): назва, принт, кольори — кожен з тоном із переліку (~29) і часткою.
Крок 2 (ті самі кадри, по одному запиту на колір): світлість і насиченість (для нейтральних — нальот) серед тих, що
словник має для цього тону. Тон з одним блоком («brownish pink») кроку 2 не має. Нема пари ознак у словнику —
найближчий блок тону (`ознаки.код_блоку`), прапорець «точно»=false рахується окремо.
Вихід у форматі попередніх прогонів (`основний`, `решта`) — тож `лічба_прогін7.py` і `аркуші_суду.py` читають його.

    python прогін7.py --вхід 40|13 [--тека-фото ТЕКА] --модель М --вихід ФАЙЛ [--продовжити]
"""
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

import ознаки
import прогін as П
import прогін_13 as П13

АДРЕСА = "http://127.0.0.1:1234/v1/chat/completions"
ТАБЛ, НАЗВИ = ознаки.таблиця()
ТОНИ = ознаки.тони(ТАБЛ)
МАКС_КОЛЬОРІВ = 3

ВСТУП = """Describe the fabric colours of the target garment across ALL supplied gallery images.
Ignore the background, skin, mannequins, hangers and other garments. Distinguish fabric
colour from illumination, shadows, shine and transparency. Do not return hexadecimal colours."""


def промпт_кроку1():
    """Крок 1: лише закритий перелік тонів, без словника блоків."""
    return f'''{ВСТУП}
For each visible fabric colour choose ONE tone from this closed list and give its area fraction
(fractions must sum to 1; at most {МАКС_КОЛЬОРІВ} colours). Tone "neutral" means white, gray or black fabric,
including slightly tinted ones.
Tones: {", ".join(ТОНИ)}
Give a nuanced Ukrainian shade name in "назва" and a Ukrainian pattern name in "принт",
or null if there is no pattern. Do not infer text content that is not legible.
Return only valid JSON with this structure:
{{"назва":"…","принт":null,"кольори":[{{"тон":"<tone from the list>","частка":0.8}},{{"тон":"<tone from the list>","частка":0.2}}]}}
The values in the JSON structure illustrate syntax only.'''


def поля_кроку2(тон):
    """Назви полів і допустимі значення для тону."""
    світлості, другі = ознаки.варіанти(ТАБЛ, тон)
    return світлості, другі


def промпт_кроку2(тон, частка):
    """Крок 2: два малі закриті переліки для тону, який модель сама назвала."""
    світлості, другі = поля_кроку2(тон)
    if тон == "neutral":
        друге_ім = "tint"
        опис = "tint = the slight colour cast of the neutral, or none"
    else:
        друге_ім = "saturation"
        опис = "saturation runs from most saturated (vivid) to least (weak / grayish)"
    return f'''{ВСТУП}
You earlier named one fabric colour of this garment with tone "{тон}" (about {частка:g} of the fabric area).
Choose its lightness and its {друге_ім}, each from the closed list below ({опис}).
"lightness": {json.dumps(світлості)}
"{друге_ім}": {json.dumps(другі)}
Return only valid JSON: {{"lightness":"<from the list>","{друге_ім}":"<from the list>"}}'''


def виклик(повідомлення, параметри, модель):
    """Один запит до LM Studio; усічену відповідь не приймає."""
    запит = urllib.request.Request(АДРЕСА, data=json.dumps(
        {"model": модель, "messages": повідомлення, **параметри}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(запит, timeout=300) as відповідь:
        сире = json.loads(відповідь.read())
    if сире["choices"][0]["finish_reason"] == "length":
        raise ValueError("відповідь усічено")
    текст = сире["choices"][0]["message"]["content"].strip()
    return текст, json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", текст))


def обробити_річ(вхід, річ, модель):
    """Крок 1 і крок 2 для однієї речі; повертає сирі відповіді й відповідь у форматі попередніх прогонів."""
    зразок = П.запит_моделі(вхід, річ, модель)  # кадри кодуються один раз
    користувач = зразок["messages"][1]
    параметри = вхід["параметри"]
    текст1, дані1 = виклик([{"role": "system", "content": промпт_кроку1()}, користувач], параметри, модель)
    частки = {}
    for к in дані1["кольори"][:МАКС_КОЛЬОРІВ]:
        if к["тон"] in ТОНИ and к["частка"] > 0:
            частки[к["тон"]] = частки.get(к["тон"], 0) + float(к["частка"])
    поза_переліком = [к["тон"] for к in дані1["кольори"] if к["тон"] not in ТОНИ]
    сума = sum(частки.values())
    if not частки:
        raise ValueError(f"Річ {річ['номер']}: жодного тону з переліку ({поза_переліком})")
    крок2, кольори = [], []
    for тон, частка in sorted(частки.items(), key=lambda п: -п[1]):
        частка = round(частка / сума, 3)
        світлості, другі = поля_кроку2(тон)
        if len(світлості) == 1 and len(другі) == 1:
            світлість, друга, текст2 = світлості[0], другі[0], None
        else:
            зміст = [{"type": "text", "text": f"Target garment: {річ['тип']}. Return JSON only."}] + користувач["content"][1:]
            текст2, дані2 = виклик([{"role": "system", "content": промпт_кроку2(тон, частка)},
                                    {"role": "user", "content": зміст}], параметри, модель)
            світлість = дані2["lightness"]
            друга = дані2["tint" if тон == "neutral" else "saturation"]
        код, точно = ознаки.код_блоку(ТАБЛ, тон, світлість, друга)
        допустимі = світлість in світлості and друга in другі
        крок2.append({"тон": тон, "частка": частка, "сира_відповідь": текст2, "світлість": світлість,
                      "друга_ознака": друга, "в_переліку": допустимі, "код": код, "точно": точно})
        кольори.append({"код": код, "частка": частка})
    return {
        "крок1_сира_відповідь": текст1, "тони_поза_переліком": поза_переліком, "крок2": крок2,
        "відповідь": {"назва": дані1.get("назва"), "принт": дані1.get("принт"), "основний": кольори[0],
                      "решта": кольори[1:], "не_певний": []},
    }


def головна():
    а = argparse.ArgumentParser(description=__doc__)
    а.add_argument("--вхід", choices=("40", "13"), required=True)
    а.add_argument("--тека-фото", type=Path)
    а.add_argument("--модель", required=True)
    а.add_argument("--вихід", type=Path, required=True)
    а.add_argument("--продовжити", action="store_true")
    а = а.parse_args()
    вхід = П.прочитати_json(П.ТЕКА / "наступний_вхід.json")
    if а.вхід == "13":
        вхід = П13.вхід_13(а.тека_фото)
    if а.вихід.exists() and not а.продовжити:
        raise ValueError("Для нової спроби потрібен новий файл виходу")
    результати = П.прочитати_json(а.вихід) if а.вихід.exists() else {}
    for річ in вхід["речі"]:
        if str(річ["номер"]) in результати:
            continue
        результати[str(річ["номер"])] = обробити_річ(вхід, річ, а.модель)
        П.записати_json(а.вихід, результати)
        print(f"Готово: {len(результати)}/{len(вхід['речі'])}", flush=True)
    П.записати_json(а.вихід.with_suffix(".метадані.json"), {
        "модель": а.модель, "параметри": вхід["параметри"], "розмір_кадру": вхід["розмір_кадру"],
        "крок1_промпт": промпт_кроку1(), "крок2_промпт_приклад": промпт_кроку2("pink", 0.8),
        "тонів": len(ТОНИ), "готово": len(результати),
        "словник_sha256": hashlib.sha256((П.ТЕКА / "словник_iscc_267.tsv").read_bytes()).hexdigest()})


if __name__ == "__main__":
    головна()

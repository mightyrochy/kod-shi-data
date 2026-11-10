"""Перелічує збережені відповіді за блоками ISCC–NBS без запуску моделей.

--підготувати створює вхід наступної спроби з усією вибраною галереєю.
Лише явний --прогін МОДЕЛЬ викликає LM Studio; у спробі 4 він не потрібний.
"""
import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

import блоки

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ОГЛЯД = КОРІНЬ / "аудит/проби/річ_колір_огляд_людьми"
МОДЕЛІ = ("qwen3-vl-8b-instruct", "qwen3.5-9b")
ПАРАМЕТРИ = {"temperature": 0.0, "max_tokens": 2000}
РОЗМІР = (640, 640)


def прочитати_json(шлях):
    """Читає збережений JSON без заміни відсутніх даних порожньою відповіддю."""
    return json.loads(шлях.read_text(encoding="utf-8"))


def записати_json(шлях, значення):
    """Записує відтворюваний JSON українською."""
    шлях.write_text(json.dumps(значення, ensure_ascii=False, allow_nan=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def прочитати_tsv(шлях):
    """Читає таблицю без перетлумачення людських назв."""
    with шлях.open(encoding="utf-8") as файл:
        return list(csv.DictReader(файл, delimiter="\t"))


def записати_tsv(шлях, рядки):
    """Записує детальний доказ кожного вердикту."""
    with шлях.open("w", encoding="utf-8", newline="") as файл:
        писач = csv.DictWriter(файл, fieldnames=рядки[0].keys(), delimiter="\t", lineterminator="\n")
        писач.writeheader()
        писач.writerows(рядки)


def еталонні_свотчі(рядок, ключ):
    """Бере підібрані свотчі, інакше лише визнаний власником свотч коду."""
    перший = рядок["середина_1_hex_OKLab"].split(" | ")[0]
    другий = рядок["середина_2_hex_OKLab"].split(" | ")[0]
    if not перший:
        if рядок["ПІСЛЯ_більшість"] == "п":
            перший = ключ["ПІСЛЯ"]["hex"]
        elif рядок["ДО_більшість"] == "п":
            перший = ключ["ДО"]["hex"]
        else:
            raise ValueError(f"Річ {рядок['номер']}: немає визнаного чи підібраного свотча")
    return [перший] + ([другий] if другий else [])


def оцінити(відповіді, модель, родини, оцінки_принту):
    """Перевіряє кожен свотч у ділянці запропонованого коду, без родин і dE."""
    рядки = [р for р in прочитати_tsv(ОГЛЯД / "лічба_sproba2_власник.tsv") if int(р["номер"]) <= 40]
    ключ = прочитати_json(ОГЛЯД / "ключ_sproba2.json")["речі"]
    if len(рядки) != 40 or set(відповіді) != {р["номер"] for р in рядки}:
        raise ValueError("Вхід має містити ті самі 40 речей і відповідей")
    звіт = []
    for рядок in рядки:
        номер = рядок["номер"]
        відповідь = відповіді[номер]
        свотчі = еталонні_свотчі(рядок, ключ[номер])
        точки = [блоки.свотч_у_munsell(hex) for hex in свотчі]
        еталони = [блоки.коди_точки(точка) for точка in точки]
        основний = відповідь["основний"]["код"]
        решта = [р["код"] for р in відповідь["решта"] if р["частка"] > 0]
        коди = [основний] + решта if len(свотчі) > 1 else [основний]
        правильна = блоки.зіставити(еталони, коди)
        сусідня = not правильна and блоки.зіставити(еталони, коди, із_сусідами=True)
        пояснення = "; ".join(f"{hex} → блоки {','.join(map(str, sorted(номери)))}"
                               for hex, номери in zip(свотчі, еталони))
        принт = оцінки_принту.get(номер)
        звіт.append({
            "номер": номер, "назва_моделі": відповідь["назва"],
            "коди_моделі": " ".join(map(str, коди)), "свотчі_власника": " / ".join(свотчі),
            "Munsell_H_V_C": " / ".join(" ".join(f"{x:.10f}" for x in т) for т in точки),
            "блоки_свотчів": " / ".join(" ".join(map(str, sorted(к))) for к in еталони),
            "родина_було": родини[номер], "блок_правильний": "ТАК" if правильна else "НІ",
            "лише_сусідній_блок": int(сусідня),
            "причина": "" if правильна else f"{пояснення}; запропоновано {коди}; " +
                ("кожен хибний код сусідить по грані" if сусідня else "є несусідній код або бракує кольору"),
            "принт_моделі": відповідь.get("принт") or "",
            "принт_правильний": принт[модель] if принт else "поза 12",
        })
    підсумок = {
        "родина_було": sum(р["родина_було"] == "ТАК" for р in звіт),
        "блок": sum(р["блок_правильний"] == "ТАК" for р in звіт),
        "хибні_лише_сусідній_блок": sum(р["лише_сусідній_блок"] for р in звіт),
        "принт_назва_виконавець": sum(р[модель] == "ТАК" for р in оцінки_принту.values()),
        "принт_обсяг": len(оцінки_принту),
    }
    return підсумок, звіт


def промпт():
    """Будує промпт з канонічним словником без особливих підказок кольору."""
    словник = прочитати_tsv(ТЕКА / "словник_iscc_267.tsv")
    довідник = "\n".join(f"{р['код']}: {р['назва_uk']}" for р in словник)
    return f'''Describe the fabric colours of the target garment across ALL supplied gallery images.
Ignore the background, skin, mannequins, hangers and other garments. Distinguish fabric
colour from illumination, shadows, shine and transparency. Use only the canonical
ISCC–NBS shade codes in the dictionary below. Do not return hexadecimal colours.
Include each visible fabric colour with its area fraction; fractions must sum to 1.
If uncertain between shades, include candidate codes in "не_певний" rather than invent certainty.
Give a nuanced Ukrainian shade name in "назва" and a Ukrainian pattern name in "принт",
or null if there is no pattern. Do not infer text content that is not legible.
Return only valid JSON with this structure:
{{"назва":"…","принт":null,"основний":{{"код":1,"частка":0.8}},
"решта":[{{"код":2,"частка":0.2}}],"не_певний":[]}}
The numeric values in the JSON structure illustrate syntax only.

Canonical dictionary (same for every garment):
{довідник}'''


def підготувати():
    """Зберігає лише дозволені поля й усі вибрані кадри; свотчів і назв еталону немає."""
    набір = прочитати_json(КОРІНЬ / "ohliad-koloru/sets/sproba2.json")
    речі = []
    for річ in набір["речі"]:
        кадри = []
        for фото in річ["галерея"]:
            if фото.startswith(("http://", "https://")):
                кадри.append({"url": фото})
            else:
                шлях = КОРІНЬ / "ohliad-koloru/foto" / фото
                кадри.append({"файл": шлях.relative_to(КОРІНЬ).as_posix(),
                              "sha256": hashlib.sha256(шлях.read_bytes()).hexdigest()})
        if not кадри:
            raise ValueError(f"Річ {річ['номер']}: немає галереї")
        речі.append({"номер": річ["номер"], "тип": річ["тип"], "кадри": кадри})
    записати_json(ТЕКА / "наступний_вхід.json", {
        "формат": 1, "стан": "підготовлено, моделі не запускалися", "параметри": ПАРАМЕТРИ,
        "розмір_кадру": РОЗМІР,
        "словник_sha256": hashlib.sha256((ТЕКА / "словник_iscc_267.tsv").read_bytes()).hexdigest(),
        "system_prompt": промпт(), "речі": речі,
    })
    print(f"Підготовлено: {len(речі)} речей, {sum(len(р['кадри']) for р in речі)} кадрів")


def запит_моделі(вхід, річ, модель):
    """Будує запит з кожним кадром, не передаючи моделі шляхів чи еталонів."""
    from PIL import Image
    зміст = [{"type": "text", "text": f"Target garment: {річ['тип']}. Return JSON only."}]
    for кадр in річ["кадри"]:
        if "файл" in кадр:
            байти = (КОРІНЬ / кадр["файл"]).read_bytes()
            if hashlib.sha256(байти).hexdigest() != кадр["sha256"]:
                raise ValueError(f"Кадр змінився: {кадр['файл']}")
        else:
            with urllib.request.urlopen(кадр["url"], timeout=60) as відповідь:
                байти = відповідь.read()
        with Image.open(io.BytesIO(байти)) as зображення:
            зображення = зображення.convert("RGB")
            зображення.thumbnail(tuple(вхід["розмір_кадру"]), Image.Resampling.LANCZOS)
            буфер = io.BytesIO()
            зображення.save(буфер, format="JPEG", quality=85)
        дані = base64.b64encode(буфер.getvalue()).decode("ascii")
        зміст.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + дані}})
    return {"model": модель, "messages": [
        {"role": "system", "content": вхід["system_prompt"]},
        {"role": "user", "content": зміст}], **вхід["параметри"]}


def прогнати(модель, вихід):
    """Запускає лише явно обрану спробу, зупиняється при збої чи усіченні.

    Завантаження й вивантаження належать сесії з GPU, яка завантажила модель.
    Старі відповіді й частково записаний прогін не перезаписуються.
    """
    if вихід.exists():
        raise ValueError("Для нової спроби потрібен новий файл виходу")
    вхід = прочитати_json(ТЕКА / "наступний_вхід.json")
    if вхід["словник_sha256"] != hashlib.sha256((ТЕКА / "словник_iscc_267.tsv").read_bytes()).hexdigest():
        raise ValueError("Словник змінився після підготовки входу")
    результати = {}
    for річ in вхід["речі"]:
        запит = urllib.request.Request("http://127.0.0.1:1234/v1/chat/completions",
            data=json.dumps(запит_моделі(вхід, річ, модель)).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(запит, timeout=300) as відповідь:
            сире = json.loads(відповідь.read())
        if сире["choices"][0]["finish_reason"] == "length":
            raise ValueError(f"Річ {річ['номер']}: відповідь усічено")
        результати[str(річ["номер"])] = json.loads(сире["choices"][0]["message"]["content"])
        записати_json(вихід, результати)
        записати_json(вихід.with_suffix(".метадані.json"), {
            "модель": модель, "параметри": вхід["параметри"],
            "вхід_sha256": hashlib.sha256((ТЕКА / "наступний_вхід.json").read_bytes()).hexdigest(),
            "готово": len(результати),
        })
        print(f"Готово відповідей: {len(результати)}/40")


def головна():
    """Розділяє перелічування, підготовку й явний запуск моделі."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument("--словник", action="store_true")
    парсер.add_argument("--підготувати", action="store_true")
    парсер.add_argument("--прогін", metavar="МОДЕЛЬ")
    парсер.add_argument("--вихід", type=Path)
    аргументи = парсер.parse_args()
    if аргументи.прогін:
        if аргументи.вихід is None:
            парсер.error("--прогін потребує --вихід з новою назвою файлу")
        прогнати(аргументи.прогін, аргументи.вихід)
        return
    if аргументи.словник:
        print(f"Словник: {len(блоки.оновити_словник())} блоків")
    if аргументи.підготувати:
        підготувати()
    історія = прочитати_json(ТЕКА / "родини_спроба3.json")["моделі"]
    принти = {р["номер"]: р for р in прочитати_tsv(ТЕКА / "принт_оцінка.tsv")}
    зведення = {}
    for модель in МОДЕЛІ:
        відповіді = прочитати_json(ТЕКА / f"відповіді_моделі_{модель}.json")
        підсумок, рядки = оцінити(відповіді, модель, історія[модель], принти)
        записати_tsv(ТЕКА / f"звіт_{модель}.tsv", рядки)
        if модель == "qwen3.5-9b":
            записати_tsv(ТЕКА / "звіт.tsv", рядки)
        зведення[модель] = підсумок
        print(модель + ": " + json.dumps(підсумок, ensure_ascii=False))
    записати_json(ТЕКА / "підсумок_блоків.json", зведення)


if __name__ == "__main__":
    головна()

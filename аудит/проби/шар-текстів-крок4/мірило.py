"""Читає обміни Sonnet і показ у парних проходах Шару текстів."""

from collections import Counter
import json
from pathlib import Path
import re
import sys


_АДРЕСА = re.compile(r"#\d+·\d+|\bваріант\s*\d", re.I)
_СЦЕНИ = ("с3", "с5", "с8")


def json_файл(шлях):
    return json.loads(шлях.read_text(encoding="utf-8")) if шлях.exists() else {}


def пояснення(запит):
    """Після підписів фото стоїть JSON пояснення з договором."""
    початок = запит.find('{"task":')
    if початок < 0:
        початок = запит.find('{"version":')
    if початок < 0:
        return None
    try:
        тіло, _ = json.JSONDecoder().raw_decode(запит[початок:])
    except ValueError:
        return None
    return тіло if ("facts" in тіло and "advice" in тіло.get("answer_schema", {}).get("properties", {})
                    or "Explain the chosen outfit" in тіло.get("task", {}).get("role", "")) else None


def прочитати_прохід(тека):
    назви = ("запит", "відповідь")
    обміни, лічба = [], Counter()
    журнал = тека / "обміни.jsonl"
    if журнал.exists():
        for рядок in журнал.read_text(encoding="utf-8").splitlines():
            запис = json.loads(рядок)
            if not запис.get("модель_cli") or not (тіло := пояснення(запис.get("запит") or "")):
                continue
            обміни.append({"час": запис.get("час"), "секунди": запис.get("с"),
                           "токени_виходу": (запис.get("usage") or {}).get("output_tokens"),
                           "з_каталогом": "pool" in тіло or "swap_candidates" in тіло,
                           "адреса_пулу": {к: bool(_АДРЕСА.search(запис.get(к) or "")) for к in назви}})
    стан = json_файл(тека / "стан.json")
    хід = стан.get("П_ядро") or стан.get("ядро") or {}
    for рядок in хід.get("звіт", []):
        збій = рядок.get("збій") or {}
        if рядок.get("рука") == 1 and збій.get("вид") == "текст_картки":
            дані = збій.get("дані") or {}
            лічба.update(дані.get("відхилення") or {})
    картка = next((к for к in стан.get("картки", []) if к and к.get("рука") == 1), {})
    return {"є_знімок_стану": bool(стан), "модель_відповідала": bool(обміни),
            "від_кліку_до_карток_с": хід.get("секунд_до_карток"),
            "відхилення_руки_1": dict(лічба), "виклики_пояснення": обміни,
            "речі_руки_1": [р.get("назва") for р in картка.get("речі", []) if isinstance(р, dict)],
            "поради_руки_1": картка.get("як_носити") or []}


def підсумок(корінь):
    результат = {}
    for бік in ("до", "після"):
        проходи = {назва: прочитати_прохід(корінь / бік / назва)
                   for назва in (f"{сцена}-{сід}" for сцена in _СЦЕНИ for сід in (3, 4))}
        лічба = Counter()
        обміни = []
        for прохід in проходи.values():
            лічба.update(прохід["відхилення_руки_1"])
            обміни.extend(прохід["виклики_пояснення"])
        результат[бік] = {
            "закінчені_проходи": sum(п["є_знімок_стану"] and п["модель_відповідала"] for п in проходи.values()),
            "картки_руки_1_з_порадою": sum(bool(п["поради_руки_1"]) for п in проходи.values()),
            "відхилення_руки_1": dict(лічба),
            "секунди_викликів_пояснення_сума": round(sum(з["секунди"] or 0 for з in обміни), 2),
            "токени_виходу_пояснень_сума": sum(з["токени_виходу"] or 0 for з in обміни),
            "виклики_без_лічильника_токенів": sum(з["токени_виходу"] is None for з in обміни),
            "проходи": проходи,
        }
    return результат


if __name__ == "__main__":
    print(json.dumps(підсумок(Path(sys.argv[1])), ensure_ascii=False, indent=2))

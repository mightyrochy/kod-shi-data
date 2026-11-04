"""Витяг фактичних входів і відповідей із незміненого запису обміну."""
import json
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parent

def тексти(вміст):
    if isinstance(вміст, str):
        return [вміст]
    return [блок.get("text", "") for блок in вміст if isinstance(блок, dict)]

def читати(сцена):
    факти = {"сцена": сцена.name, "виклики": []}
    for файл in sorted(сцена.glob("VIDPOVIDI/обмін/*.json")):
        обмін = json.loads(файл.read_text(encoding="utf-8"))
        запит = обмін["запит"]
        відповідь = обмін["відповідь"]
        рядок = {"файл": str(файл.relative_to(КОРІНЬ)), "status": відповідь.get("status")}
        for повідомлення in запит.get("messages", []):
            for текст in тексти(повідомлення.get("content", [])):
                try:
                    дані = json.loads(текст)
                except (ValueError, TypeError):
                    continue
                if isinstance(дані, dict):
                    for ключ in ["person", "occasion", "day", "scenario", "brief", "passport"]:
                        if ключ in дані:
                            рядок[ключ] = дані[ключ]
        try:
            тіло = json.loads(відповідь["body"])
            рядок["відповідь"] = "\n".join(тексти(тіло.get("content", [])))
        except (ValueError, KeyError, TypeError):
            рядок["відповідь"] = str(відповідь.get("body", ""))
        факти["виклики"].append(рядок)
    лог = сцена.joinpath("лог.txt").read_text(encoding="utf-8")
    факти["рядки_питань"] = [рядок for рядок in лог.splitlines() if any(слово in рядок for слово in
        ["паспорт:", "паспорт ", "щаб", "part_of_day", "formality", "open_zones", "П-7", "утрим", "✘", "ДОКАЗ ·"])]
    return факти

if __name__ == "__main__":
    назви = sys.argv[1:] or [ф.name for ф in КОРІНЬ.iterdir() if ф.joinpath("результат.json").is_file()]
    результат = [читати(КОРІНЬ / назва) for назва in назви]
    КОРІНЬ.joinpath("факти.json").write_text(json.dumps(результат, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for сцена in результат:
        print(сцена["сцена"], "викликів:", len(сцена["виклики"]))
        for виклик in сцена["виклики"]:
            if "person" in виклик:
                print(json.dumps(виклик, ensure_ascii=False)[:2500])
        for рядок in сцена["рядки_питань"]:
            print(рядок[:1500])

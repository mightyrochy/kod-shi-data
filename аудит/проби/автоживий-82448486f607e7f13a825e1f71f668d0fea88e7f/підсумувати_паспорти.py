"""Витяг структурованих полів із журналів вердиктів завершених сцен."""
import json
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
ПОЛЯ = ("подія", "нагода", "місце", "пора", "година", "хвилини", "ошатність", "причина_ошатності", "джерело_полів")
ВИМІРИ = ("occasion", "place", "part_of_day", "hour", "minute", "formality", "open_zones", "undertone")

def витяг(паспорт):
    if isinstance(паспорт, str):
        try:
            паспорт = json.loads(паспорт)
        except ValueError:
            return {"сирий": паспорт}
    if not isinstance(паспорт, dict):
        return паспорт
    д = {к: паспорт[к] for к in ПОЛЯ if к in паспорт}
    for ключ in ["виміри", "звідки"]:
        if isinstance(паспорт.get(ключ), dict):
            д[ключ] = {к: паспорт[ключ][к] for к in ВИМІРИ if к in паспорт[ключ]}
    return д

підсумок = []
for сцена in sorted(ТЕКА.iterdir()):
    if not сцена.joinpath("результат.json").is_file() or not сцена.joinpath("вердикти.txt").is_file():
        continue
    дані = json.loads(сцена.joinpath("вердикти.txt").read_text(encoding="utf-8"))
    глобальний = дані.get("спільне", {})
    for прогін in дані.get("прогони", []):
        спільне = dict(глобальний, **прогін.get("спільне", {}))
        паспорт = спільне.get("паспорт")
        if паспорт is not None:
            підсумок.append({"сцена": сцена.name, "прогін": прогін.get("прогін"), "паспорт": витяг(паспорт)})

ТЕКА.joinpath("паспорти.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for рядок in підсумок:
    print(json.dumps(рядок, ensure_ascii=False))

"""Витягає факти записаного прогону, не оцінюючи доречність образів."""
import json
from pathlib import Path
import re

ТЕКА = Path(__file__).resolve().parent

def прочитати(шлях):
    return json.loads(шлях.read_text(encoding="utf-8")) if шлях.exists() else None

def main():
    план = json.loads((ТЕКА / "НАРЯД.md").read_text(encoding="utf-8").split("ПЛАН ЖИВОГО — ДАНІ (JSON):\n", 1)[1].splitlines()[0])
    підсумок = {}
    червоні = []
    for сцена, питання in план["scenes"].items():
        шлях = ТЕКА / сцена
        if not шлях.exists():
            підсумок[сцена] = {"питання": питання, "стан": "не запускалася"}
            continue
        лог = (шлях / "лог.txt").read_text(encoding="utf-8") if (шлях / "лог.txt").exists() else ""
        мінуси = [р.strip() for р in лог.splitlines() if р.lstrip().startswith("✗")]
        плюси = [р for р in лог.splitlines() if р.lstrip().startswith("✔")]
        дані = {"питання": питання, "результат": прочитати(шлях / "результат.json"),
                "доказ": прочитати(шлях / "знімки/доказ.json"), "зелених_звірок": len(плюси),
                "червоних_звірок": len(мінуси), "червоні": мінуси,
                "знімків_png": len(list((шлях / "знімки").glob("*.png"))), "ходи": []}
        for файл in sorted((шлях / "VIDPOVIDI/обмін").glob("*.json")):
            обмін = прочитати(файл)
            try:
                тіло = json.loads(обмін["відповідь"]["body"])
                текст = "".join(б.get("text", "") for б in тіло.get("content", []) if б.get("type") == "text")
                if not текст:
                    текст = тіло.get("choices", [{}])[0].get("message", {}).get("content", "")
                текст = re.sub(r"^```(?:json)?\s*|\s*```$", "", текст.strip())
                відповідь = json.loads(текст)
                if "update" in відповідь:
                    дані["ходи"].append({"файл": str(файл.relative_to(ТЕКА)), "update": відповідь["update"]})
            except (ValueError, TypeError, KeyError, IndexError):
                pass
        звіт = прочитати(шлях / "вердикти.txt")
        if звіт:
            дані["ключі_вердиктів"] = list(звіт)
            дані["спільне"] = звіт.get("спільне")
        підсумок[сцена] = дані
        червоні.extend(["\n" + сцена, *мінуси])
    (ТЕКА / "ФАКТИ.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ТЕКА / "ЧЕРВОНІ.txt").write_text("\n".join(червоні) + "\n", encoding="utf-8")
    for сцена, д in підсумок.items():
        р = д.get("результат") or {}
        print(сцена, "rc=" + str(р.get("rc")), "+" + str(д.get("зелених_звірок", 0)),
              "-" + str(д.get("червоних_звірок", 0)), "png=" + str(д.get("знімків_png", 0)))

if __name__ == "__main__":
    main()

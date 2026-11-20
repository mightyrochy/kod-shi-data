"""Зводить факти запису без викликів моделей і без оцінки людиною."""
from pathlib import Path
import json
import re

тека = Path(__file__).resolve().parent
план = json.loads((тека / "ПЛАН.json").read_text(encoding="utf-8"))
факти = {}
for сцена in план["scenes"]:
    запис = тека / сцена
    результат = запис / "результат.json"
    if not результат.is_file():
        continue
    р = json.loads(результат.read_text(encoding="utf-8"))
    ф = {к: р.get(к) for к in ("rc", "sha", "дерево_стенда", "секунд", "початок", "кінець", "вивантажено")}
    підсумок = re.search(r"ВПАЛО (\d+)", (запис / "лог.txt").read_text(encoding="utf-8"))
    ф["червоних_звірок"] = int(підсумок[1]) if підсумок else 0
    ф["червоні_рядки"] = [{"рядок": н, "текст": т[:1600]} for н, т in enumerate((запис / "лог.txt").read_text(encoding="utf-8").splitlines(), 1) if "✗" in т]
    вердикти = запис / "вердикти.txt"
    ф["журнал_паспорта"] = []
    ф["діагноз_фото"] = []
    if вердикти.is_file():
        в = json.loads(вердикти.read_text(encoding="utf-8"))
        ф["вердиктів"] = в.get("вердиктів")
        for прогін in в.get("прогони", []):
            for вердикт in прогін.get("вердикти", []):
                ф["діагноз_фото"] += [д for д in вердикт.get("етапи", {}).get("діагноз_руки", []) if isinstance(д, str) and "description_with_photos_failed" in д]
            розмова = прогін.get("спільне", {}).get("етапи", {}).get("розмова", {})
            if "зміни_паспорта" in розмова:
                ж = розмова["зміни_паспорта"]
                ф["журнал_паспорта"].append({"записів": len(ж), "усі_мають_хто_поля": all(isinstance(з, dict) and "хто" in з and "поля" in з for з in ж), "зміни": ж})
    ф["обмінів"] = 0
    ф["стеля_виводу"] = []
    ф["відповіді_не_200"] = []
    for файл in sorted((запис / "VIDPOVIDI/обмін").glob("*.json")):
        о = json.loads(файл.read_text(encoding="utf-8"))
        ф["обмінів"] += 1
        в = о.get("відповідь", {})
        if в.get("status") != 200:
            ф["відповіді_не_200"].append({"файл": файл.name, "status": в.get("status"), "body": str(в.get("body", ""))[:1000]})
        try:
            тіло = json.loads(в.get("body", ""))
        except (ValueError, TypeError):
            continue
        if тіло.get("stop_reason") == "max_tokens" or any(ч.get("finish_reason") == "length" for ч in тіло.get("choices", [])):
            ф["стеля_виводу"].append(файл.name)
    факти[сцена] = ф
(тека / "факти.json").write_text(json.dumps(факти, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({с: {к: ф.get(к) for к in ("rc", "секунд", "обмінів", "стеля_виводу")} for с, ф in факти.items()}, ensure_ascii=False))

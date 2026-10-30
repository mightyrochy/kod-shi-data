"""Витягає факти із завершених записів, не викликає моделі й не міняє звірок."""
from collections import Counter
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
summary = {}
for folder in sorted(root.iterdir()):
    if not folder.is_dir() or not (folder / "done.txt").exists():
        continue
    log = (folder / "лог.txt").read_text(encoding="utf-8")
    calls = json.loads((folder / "знімки/модель_виклики.json").read_text(encoding="utf-8"))["виклики"]
    proof = json.loads((folder / "знімки/доказ.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "результат.json").read_text(encoding="utf-8"))
    repeats = []
    previous_prompts = []
    for path in sorted((folder / "відповіді").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        prompt = text.split("\n", 1)[1].split("\n── ВІДПОВІДЬ", 1)[0].strip()
        try:
            parsed = json.loads(prompt)
        except ValueError:
            continue
        if isinstance(parsed, dict) and "format_error" in parsed:
            original = {key: value for key, value in parsed.items() if key != "format_error"}
            matches = [name for name, data in previous_prompts if data == original]
            repeats.append({"файл": path.name, "один_JSON": True,
                "format_error": parsed["format_error"], "ключі": list(parsed),
                "початковий_без_змін": matches})
        previous_prompts.append((path.name, parsed))
    data = {
        **result,
        "успішних_звірок": len(re.findall(r"^\s*✔ ", log, re.M)),
        "невдалих_звірок": len(re.findall(r"^\s*✗ ", log, re.M)),
        "провали": re.findall(r"^\s*✗ (.*)$", log, re.M),
        "факт": proof["факт"],
        "вердикт_приладу": proof["вердикт"],
        "SHA_доказу": proof["код"],
        "викликів": len(calls),
        "HTTP_200": sum(call.get("статус") == 200 for call in calls),
        "типи_викликів": dict(Counter(call["тип"] for call in calls)),
        "max_tokens": [{"номер": i + 1, **call} for i, call in enumerate(calls) if call.get("стоп") == "max_tokens"],
        "вхідних_токенів_макс": max(call.get("вхід", 0) for call in calls),
        "втрат_фото": sum(call.get("фото_не_дійшло", 0) for call in calls),
        "повтори_з_format_error": repeats,
        "знімки_карток": [path.name for path in sorted((folder / "знімки").glob("kartka_poz*.png"))],
    }
    summary[folder.name] = data
(root / "підсумок.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
for scene, data in summary.items():
    print(f"{scene}: rc={data['rc']}; звірки {data['успішних_звірок']}/{data['невдалих_звірок']}; HTTP {data['HTTP_200']}/{data['викликів']}; карток {data['факт']['карток']}; повторів {len(data['повтори_з_format_error'])}; max_tokens {len(data['max_tokens'])}; втрат фото {data['втрат_фото']}")

"""Збирає лише записані факти; моделей не викликає й вердиктів не змінює."""
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
    result = json.loads((folder / "результат.json").read_text(encoding="utf-8"))
    proof_file = folder / "знімки/доказ.json"
    proof = json.loads(proof_file.read_text(encoding="utf-8")) if proof_file.exists() else {}
    calls_file = folder / "знімки/модель_виклики.json"
    calls = json.loads(calls_file.read_text(encoding="utf-8"))["виклики"] if calls_file.exists() else []
    state_file = folder / "знімки/поверхня_стани.json"
    states = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else []
    summary[folder.name] = {
        **result,
        "успішних_звірок": len(re.findall(r"^\s*✔ ", log, re.M)),
        "невдалих_звірок": len(re.findall(r"^\s*✗ ", log, re.M)),
        "провали": re.findall(r"^\s*✗ (.*)$", log, re.M),
        "факт": proof.get("факт"), "вердикт_приладу": proof.get("вердикт"),
        "SHA_доказу": proof.get("код"),
        "викликів": len(calls), "HTTP_200": sum(c.get("статус") == 200 for c in calls),
        "типи_викликів": dict(Counter(c["тип"] for c in calls)),
        "max_tokens": [{"номер": i + 1, **c} for i, c in enumerate(calls) if c.get("стоп") == "max_tokens"],
        "вхідних_токенів_макс": max((c.get("вхід", 0) for c in calls), default=0),
        "втрат_фото": sum(c.get("фото_не_дійшло", 0) for c in calls),
        "невдалі_HTTP": [{"номер": i + 1, **c} for i, c in enumerate(calls) if c.get("статус") != 200],
        "знімки_карток": [p.name for p in sorted((folder / "знімки").glob("kartka_poz*.png"))],
        "станів_поверхні": len(states),
        "останній_стан_із_речами": next((s for s in reversed(states) if s.get("речі") or s.get("оцінка")), None),
    }
(root / "підсумок.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
for scene, data in summary.items():
    print(f"{scene}: rc={data['rc']}; звірки {data['успішних_звірок']}/{data['невдалих_звірок']}; "
          f"HTTP {data['HTTP_200']}/{data['викликів']}; карток {len(data['знімки_карток'])}; втрат фото {data['втрат_фото']}")
    for failure in data["провали"]:
        print("  " + failure)

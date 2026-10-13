"""РОЗМОВА-2 (рядки 936/1001/1133): живий хід розмови (`claude -p`, ZHYVA=sonnet) → суд частин → що дійшло до жінки.
Запуск: ZHYVA=claude-sonnet-5-5 python3 джерела/проби/розмова2_проба.py "фраза" [ще фраза …]"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import мовний_шар as М
СИС = "You are the model behind a mobile styling app. Output only the raw JSON the prompt asks for."
ЗМІШАНЕ = re.compile(r"\b(?=\w*[a-z])(?=\w*[а-яіїєґ])\w+", re.I)     # слово з літерами двох абеток
for фраза in sys.argv[1:]:
    вх = {"розмова": {"нове": фраза, "історія": []}, "сценарій": {}}
    пром = json.loads(М.мова(вх))["промпт"]
    відп = subprocess.run(["claude", "-p", "--model", os.environ.get("ZHYVA", "claude-sonnet-5-5"), "--tools", "",
                           "--no-session-persistence", "--system-prompt", СИС], input=пром, capture_output=True,
                          text=True, timeout=600).stdout
    р = json.loads(М.мова({**вх, "відповідь_моделі": відп}))
    ч = р["частини"]
    пш = json.loads(М.мова({"паспорт_з": р["внутрішня"], "сценарій": {}, "слова_розмови": [фраза], "частини": ч}))
    print("\n«%s»\n  model invite_topics=%s\n  kept=%s  allowed=%s" % (фраза, ч.get("invite_topics"), пш["теми_поради"], пш["дозволені"]))
    print("  hour/minute моделі=%s/%s · паспорт година/хвилини=%s/%s" % (р["внутрішня"].get("hour"), р["внутрішня"].get("minute"),
          пш["паспорт"].get("година"), пш["паспорт"].get("хвилини")))
    print("  відкинуто=%s" % json.dumps(пш["відкинуто"], ensure_ascii=False))
    print("  текст: %s\n  змішані слова: %s" % (пш["текст"], ЗМІШАНЕ.findall(пш["текст"])))

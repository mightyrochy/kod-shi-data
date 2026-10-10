# -*- coding: utf-8 -*-
"""Рядок 4511: що лишається у вході перекладача від ярлика hex — «color (sage green)», «code (off-white)» — на
записаних відповідях рук 3–4 (`*проза_рука_3_4.txt`). Шлях — як у показі: `людською()` з `показ.html` (node, hex
лишається) → `мовний_шар.мова` → текст у промпті шару. Друкує по гілці: текстів із hex, залишків «ярлик (назва)»,
голих «code»/«hex», і приклади. ДО/ПІСЛЯ — той самий запуск на базі (git stash) і на правці.
Запуск: cd джерела && python3 проби/колір_ярлик_hex.py origin/claude/zhyvi-19:аудит/живі_19 […]"""
import json, os, re, subprocess, sys, tempfile
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, К)
import мовний_шар as М
JS = r"""const fs = require('fs'), [, html, ф] = process.argv, s = fs.readFileSync(html, 'utf8');
const п = s.indexOf('function людською('), б = s.indexOf('const безМашинногоСліду', п);
eval(s.slice(п, s.indexOf('.trim();', s.indexOf("String(s||'')", б)) + 8) + '\nglobalThis.Л = людською;');
const т = fs.readFileSync(ф, 'utf8'), в = т.slice(т.indexOf('── ВІДПОВІДЬ')), р = в.slice(в.indexOf('\n') + 1);
process.stdout.write(JSON.stringify(Л(р, {}, true)[0]));"""
ЯРЛИК = re.compile(r"\b(?:hex|code|colou?r)\b\s*(?:code\b\s*)?[:=]?\s*\([^()\n]*\)", re.I)
ГОЛИЙ = re.compile(r"\b(?:hex|code)\b", re.I)
for арг in sys.argv[1:]:
    гілка, тека = арг.split(":", 1)
    файли = [ф for ф in subprocess.run(["git", "ls-tree", "-r", "--name-only", гілка, "--", тека], capture_output=True,
                                       text=True, check=True).stdout.split("\n") if ф.endswith("проза_рука_3_4.txt")]
    з_hex = ярлик = голих = 0; приклади = []
    for ф in файли:
        сирий = subprocess.run(["git", "show", гілка + ":" + ф], capture_output=True, text=True, check=True).stdout
        if not re.search(r"#[0-9a-fA-F]{6}\b", сирий.split("── ВІДПОВІДЬ")[-1]):
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as т:
            т.write(сирий)
        опис = json.loads(subprocess.run(["node", "-e", JS, os.path.join(К, "показ.html"), т.name], capture_output=True,
                                         text=True, check=True).stdout); os.unlink(т.name)
        пр = json.loads(М.мова({"тексти": {"опис": опис}}))["промпт"]
        текст = " ".join(р["текст"] for р in json.loads(пр[пр.index("ТЕКСТИ:") + 8:]))
        з_hex += 1; зн = ЯРЛИК.findall(текст); ярлик += len(зн); голих += len(ГОЛИЙ.findall(текст)); приклади += зн
    print("%s: текстів із hex %d · «ярлик (назва)» %d · голих code/hex %d · %s" % (тека, з_hex, ярлик, голих, приклади[:6]))

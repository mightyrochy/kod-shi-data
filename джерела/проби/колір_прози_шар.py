# -*- coding: utf-8 -*-
"""Рядок 3934: колір прози рук 3–4 — що код подає мовному шару, ДО і ПІСЛЯ, на записаних відповідях.

Проза руки (`*проза_рука_3_4.txt` стенда) іде тим самим шляхом, що в показі: `людською()` з `показ.html`
(node) → `мовний_шар.мова({тексти})` → промпт шару. ДО — `людською` без `лишитиHex` (hex знімає показ),
ПІСЛЯ — з ним (hex стає кодом `[colour: …]`, `мовний_шар.кольори_кодом`). Друкує: «color,» без кольору,
кодів кольору у вході шару і які коди з внутрішнім словом пішли в промпт.
Запуск: `python3 проби/колір_прози_шар.py <тека VIDPOVIDI> […]` (ЖИВІ-15 №11–12: `claude/zhyvi-15:аудит/живі_15/А/`)."""
import glob, json, os, re, subprocess, sys
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, К)
import мовний_шар as М
JS = r"""const fs = require('fs'), [, html, hex, ф] = process.argv, s = fs.readFileSync(html, 'utf8');
const п = s.indexOf('function людською('), б = s.indexOf('const безМашинногоСліду', п);
eval(s.slice(п, s.indexOf('.trim();', s.indexOf("String(s||'')", б)) + 8) + '\nglobalThis.Л = людською;');
const т = fs.readFileSync(ф, 'utf8'), в = т.slice(т.indexOf('── ВІДПОВІДЬ')), р = в.slice(в.indexOf('\n') + 1);
process.stdout.write(JSON.stringify(Л(р, {}, hex === '1')[0]));"""


def вхід_шару(файл, лишити):
    опис = json.loads(subprocess.run(["node", "-e", JS, os.path.join(К, "показ.html"), лишити, файл],
                                     capture_output=True, text=True, check=True).stdout)
    пр = json.loads(М.мова({"тексти": {"опис": опис}}))["промпт"]
    return пр, json.loads(пр[пр.index("ТЕКСТИ:") + 8:])[0]["текст"]


for тека in sys.argv[1:]:
    for ф in sorted(glob.glob(os.path.join(тека, "*проза_рука_3_4.txt"))):
        print(os.path.relpath(ф, тека))
        for що, лишити in (("ДО   ", "0"), ("ПІСЛЯ", "1")):
            пр, т = вхід_шару(ф, лишити)
            коди = пр[пр.index("Коди: ") + 6:пр.index("ТЕКСТИ:")].strip() if "[colour: код]" in пр else "—"
            print("  %s «color,» без кольору %d · [colour: …] %d · she/her %d · коди: %s" % (
                що, len(re.findall(r"\bcolou?r\s*,", т, re.I)), т.count("[colour: "),
                len(re.findall(r"\b(she|her)\b", т, re.I)), коди))

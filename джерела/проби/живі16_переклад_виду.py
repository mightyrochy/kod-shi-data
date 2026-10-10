"""ОЦІНКА-Ж16 (рядок 4022): перекладач (мовний шар, MamayLM) міняє вид речі в описі картки — «pendant necklace» →
«кулонна каблучка», «ankle boots … lace-up» → «туфлі-човники на підборах … зі шнурівкою» (ЖИВІ-16 №11 рука 2,
`seed3_27`). Записані виклики перекладача ЖИВІ-15/16 №11–13: на кожен текст входу (англійською) і його переклад — речення,
де англійський вид названо, а в перекладі стоїть ІНШИЙ вид (словник нижче — слова читає ПРОБА, не код). Кращим: 0.
Запуск: cd джерела && python3 проби/живі16_переклад_виду.py"""
import json, re, subprocess
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ВИД = ((r"\bpendant|\bnecklace", r"каблучк|перстен|сереж|браслет", r"\bring\b|earring|bracelet"),
       (r"ankle boots|\bboots\b", r"туфл|човник|босоніж", r"\bpumps|\bshoes\b|sandal"),
       (r"\bearrings", r"каблучк|намист|браслет", r"\bring\b|necklace|bracelet"),
       (r"\bbelt\b", r"сукн|шарф", r"dress|scarf"))  # (вид англійською, інший вид у перекладі, той інший вид англійською)
for ж in ("15", "16"):
    Г = "origin/claude/zhyvi-%s" % ж
    git("fetch", "-q", "origin", "claude/zhyvi-%s" % ж)
    текстів = хибних = 0
    for ф in [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_%s/А" % ж).split("\n")
              if re.search(r"/1[123]_.*VIDPOVIDI/.*_мовний_шар\.txt$", ф)]:
        т = git("show", "%s:%s" % (Г, ф))
        з = т.split("── ВІДПОВІДЬ")[0]
        вх, ви = re.search(r"\[\s*\{.*\}\s*\]", з[з.rfind("\n["):], re.S), re.search(r"\{.*\}", т.split("── ВІДПОВІДЬ", 1)[-1], re.S)
        try:
            вх, ви = json.loads(вх.group(0)), json.loads(ви.group(0))
        except (AttributeError, ValueError):
            continue
        for о in вх if isinstance(вх, list) else []:
            en, uk = str(о.get("текст") or ""), str(ви.get(str(о.get("н"))) or "")
            for ре, ні, ні_en in ВИД:
                for і, р in enumerate(en.split("\n")):
                    if re.search(ре, р, re.I):
                        текстів += 1
                        ук = (uk.split("\n") + [""] * 99)[і]
                        if re.search(ні, ук, re.I) and not re.search(ні_en, р, re.I):
                            хибних += 1
                            print("Ж%s %s/%s: %r → %r" % (ж, ф.split("/")[-3][:2], ф.split("/")[-1][:8], р[:70], ук[:80]))
    print("Ж%s: речень з видом %d · вид у перекладі інший %d" % (ж, текстів, хибних))

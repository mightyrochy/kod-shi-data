"""ОЦІНКА-Ж19 (рядки 4104, 4280; #866): проза рук 3–4 ЖИВІ-18/19 №11–13 (`*проза_рука_3_4*`) через
`мовний_шар.кольори_кодом` тим кодом, що в теці аргументу (типово `.`), — так, як текст іде в перекладача (цілим).
На кожен рядок прози з hex: що лишилось на місці hex (`[colour: …]` чи нічого) і які слова кольору (`_слова_кольору`)
є в САМОМУ рядку. «Втрачено» = hex знято без коду, а в його рядку назви кольору нема або лише «soft»/«light»
(частини складених кодів) — на картці «кольору,» / «відтінку,» без назви. Кращим: втрачено 0.
Запуск: cd джерела && python3 проби/живі19_кольори.py [тека джерел іншої збірки]"""
import re, subprocess, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
HEX, СЛОВА, ЗАГАЛЬНІ = re.compile(r"#[0-9a-fA-F]{6}\b"), М._слова_кольору(), {"soft", "light"}
for ж in ("18", "19"):
    Г = "origin/claude/zhyvi-%s" % ж
    git("fetch", "-q", "origin", "claude/zhyvi-%s" % ж)
    всього = кодом = втрачено = 0
    for ф in [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_%s/А" % ж).split("\n")
              if re.search(r"/1[123]_.*VIDPOVIDI/.*проза_рука_3_4", ф)]:
        т = git("show", "%s:%s" % (Г, ф)).split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
        for р, ц in zip(т.split("\n"), М.кольори_кодом(т).split("\n")):
            if not HEX.search(р):
                continue
            всього += len(HEX.findall(р)); кодом += ц.count("[colour:")
            назви = {w.lower() for w in re.findall(r"[A-Za-z]+", HEX.sub("", р))} & СЛОВА
            if "[colour:" not in ц and назви <= ЗАГАЛЬНІ:
                втрачено += 1
                print("   Ж%s %s втрачено (слова кольору в рядку: %s): %s" % (ж, ф.split("/")[-3][:2],
                      sorted(назви) or "—", ц[:100]))
    print("Ж%s: hex %d · кодом %d · втрачено %d" % (ж, всього, кодом, втрачено))

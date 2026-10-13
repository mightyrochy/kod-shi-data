# -*- coding: utf-8 -*-
"""Рядок 3640 · replay записаних відповідей ремонту (ВЕРДИКТ_V1 → ОБРАЗИ_V1, роль «improve them»; живі 11–14 і
пачка 2 — гілки `claude/zhyvi-13`, `-14` і поточна): вихід у токенах проти стелі 4000, частка «done» у символах,
записи «done» на гейт / зауваження / блокер, і скільки важила б та сама відповідь за правилом ремонту ПІСЛЯ —
запис лише гейтові й зауваженню, для якого міняли річ («fixed»/«partly» без «why»), «declined» над зауваженням
і запис блокера не пишуться. TOKENIZER=<tokenizer.json> — точна лічба; без нього 3,29 симв./т. (як 3530).
Запуск: cd джерела && python3 проби/ремонт_стеля_3640.py"""
import hashlib, json, os, re, subprocess
Т = os.environ.get("TOKENIZER") and __import__("tokenizers").Tokenizer.from_file(os.environ["TOKENIZER"])
ток = (lambda т: len(Т.encode(т).ids)) if Т else (lambda т: round(len(т) / 3.29))
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ЗАП = re.compile(r'\{\s*"finding"\s*:\s*"([^"]*)"\s*,\s*"action"\s*:\s*"([^"]*)"(\s*,\s*"why"\s*:\s*"(?:[^"\\]|\\.)*")?\s*\}\s*,?')
ДОНЕ = re.compile(r'"done"\s*:\s*\[(?:[^\[\]"]|"(?:[^"\\]|\\.)*")*\]?')
бачено, обірвані, с = set(), [], dict(відп=0, т=0, к=0, обрив=0, обрив_к=0, симв=0, done=0, гейт=0, зауваж=0, блокер=0, лишено=0)
for г in ("HEAD", "origin/claude/zhyvi-13", "origin/claude/zhyvi-14"):
    for ф in git("ls-tree", "-r", "--name-only", г, "--", "../аудит/").split("\n"):
        пр, _, в = git("show", "%s:%s" % (г, ф)).partition("\n── ВІДПОВІДЬ") if re.search(r"/VIDPOVIDI/.*ВЕРДИКТ_V1_ОБРАЗИ_V1.*\.txt$", ф) else ("", "", "")
        в = в.partition("\n")[2].strip()
        if not в or "improve them" not in пр or hashlib.md5(в.encode()).digest() in бачено:
            continue
        бачено.add(hashlib.md5(в.encode()).digest())
        дріт = json.loads(пр.partition("\n")[2])
        гейти = {з.get("id") for о in дріт["verdict"] for з in о.get("findings") or [] if з.get("register") == "gate"}
        def після(м):
            вид = "гейт" if м.group(1) in гейти else "блокер" if м.group(1).startswith("b-") else "зауваж"
            с[вид] += 1
            if вид == "блокер" or (вид == "зауваж" and м.group(2) == "declined"):
                return ""
            с["лишено"] += 1
            return м.group(0) if м.group(2) == "declined" else м.group(0).replace(м.group(3) or "\0", "")
        к_т = ЗАП.sub(після, в)
        т, к = ток(в), ток(к_т)
        for ключ, v in (("відп", 1), ("т", т), ("к", к), ("обрив", т >= 3900), ("обрив_к", т >= 3900 and к >= 3900),
                        ("симв", len(в)), ("done", sum(len(x) for x in ДОНЕ.findall(в)))):
            с[ключ] += v
        обірвані += [к] if т >= 3900 else []
print("ремонт: відповідей %d · обірвано на стелі %d · «done» %d%% символів · записів «done»: гейт %d, зауваження %d, "
      "блокер %d" % (с["відп"], с["обрив"], 100 * с["done"] // с["симв"], с["гейт"], с["зауваж"], с["блокер"]))
print("ПІСЛЯ (правило 3640): записів лишилось %d · токенів виходу %d → %d (−%d%%) · написана частина обірваних: %s т. · "
      "обірваних і після — %d" % (с["лишено"], с["т"], с["к"], 100 - 100 * с["к"] // с["т"], sorted(обірвані), с["обрив_к"]))

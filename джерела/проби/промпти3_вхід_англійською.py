"""ПРОМПТИ-3 (рядок 6191): перекладачки коментаря й питання — збирачем англійською. На записах живих прогонів (типово
`origin/claude/zhyvi-pachka-15`): розмір промпту ДО (`main`) і ПІСЛЯ (ця гілка) з тими самими словами й речами — знаки
й токени Gemma 3 (GEMMA_TOKENIZER=<tokenizer.json>; без нього — «—»); replay записаних відповідей `прийняти_вхід` кодом
`main` і цієї гілки — `vetoes`/`wants` і вся внутрішня мова. Кращим: токенів ПІСЛЯ менше, розбіжностей 0.
Запуск: cd джерела && [GEMMA_TOKENIZER=…] python3 проби/промпти3_вхід_англійською.py [гілка без origin/claude/]"""
import gzip, importlib.util, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, "."); import мовний_шар as Н
Г = sys.argv[1] if len(sys.argv) > 1 else "zhyvi-pachka-15"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True).stdout
git("fetch", "-q", "origin", "claude/%s:refs/remotes/origin/claude/%s" % (Г, Г))
ш = os.path.join(tempfile.mkdtemp(), "мш_main.py"); open(ш, "wb").write(git("show", "origin/main:джерела/мовний_шар.py"))
сп = importlib.util.spec_from_file_location("мш_main", ш); С = importlib.util.module_from_spec(сп); сп.loader.exec_module(С)
ток = None
if os.environ.get("GEMMA_TOKENIZER"):
    from tokenizers import Tokenizer
    _т = Tokenizer.from_file(os.environ["GEMMA_TOKENIZER"]); ток = lambda s: len(_т.encode(s).ids)
розмір = lambda s: "%5d симв. / %s ток." % (len(s), ток(s) if ток else "—")
for вид in ("verdict_comment", "question", "review_items_fix"):          # голий промпт виду: слів і речей нема
    print("%-16s ДО %s → ПІСЛЯ %s" % (вид, розмір(С.промпт_входу(вид, "")), розмір(Н.промпт_входу(вид, ""))))
записів = різне = 0
for ф in git("ls-tree", "-r", "--name-only", "origin/claude/" + Г, "../аудит").decode().split("\n"):
    if not re.search(r"VIDPOVIDI/.*мовний_шар_вхід", ф):
        continue
    т = git("show", "origin/claude/%s:%s" % (Г, ф)); т = (gzip.decompress(т) if ф.endswith(".gz") else т).decode()
    пр, відп = т.split("\n", 1)[1].split("\n\n── ВІДПОВІДЬ (", 1)
    вид = "verdict_comment" if "коментар жінки до образу" in пр else "question" if "ставить стилістці питання" in пр else 0
    if not вид:
        continue
    відп, слова = відп.split("\n", 1)[1], пр.split("\nСЛОВА:\n", 1)[1].split("\n\nКОНТЕКСТ:")[0]
    кт = json.loads(пр.rsplit("\nКОНТЕКСТ:\n", 1)[1]) if "\nКОНТЕКСТ:\n" in пр else None
    речі = (кт or {}).get("items") or []
    арг = dict(ід_речей={р["id"] for р in речі} if речі else None, слоти_речей={р["id"]: р["slot"] for р in речі}, слова=слова)
    до, після = С.прийняти_вхід(вид, відп, **арг), Н.прийняти_вхід(вид, відп, **арг)
    записів += 1; різне += до["внутрішня"] != після["внутрішня"]
    print("%-40s %-15s ДО %s → ПІСЛЯ %s | vetoes %s wants %s | %s" % (ф.split("/")[2][:40], вид, розмір(пр),
          розмір(Н.промпт_входу(вид, слова, кт)), json.dumps(після["внутрішня"].get("vetoes"), ensure_ascii=False),
          json.dumps(після["внутрішня"].get("wants"), ensure_ascii=False), "те саме" if до["внутрішня"] == після["внутрішня"]
          else "РІЗНЕ: " + json.dumps([до["внутрішня"], після["внутрішня"]], ensure_ascii=False)[:300]))
print("записів:", записів, "| внутрішня мова replay різна:", різне)

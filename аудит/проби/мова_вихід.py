"""П.6 наряду 25.09, роль ВИХІД: модель-«голос» переписує текст для жінки природною українською на «ти».
Вхід — JSONL {група, мітка, вид, текст} (тексти живих прогонів); на кожну модель з MODELS кожен текст іде з наказом
НАКАЗ; друкує час, довжину до→після, числа й #коди, що зникли/з'явились, знахідки R-LNG-UA (language_gate.російське)
до→після і слова, чиїх основ (5 літер) нема по той бік, — підказка для огляду очима, не вердикт. Після — JSONL для
мова_лічильник.py. Запуск (з теки джерела): MODEL_URL=http://127.0.0.1:1234/v1 MODELS=м1 python ../аудит/проби/мова_вихід.py вхід.jsonl вихід.jsonl"""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.getcwd()); sys.stdout.reconfigure(encoding="utf-8")
from language_gate import російське
НАКАЗ = "Перепиши природною українською на «ти», нічого не додаючи й не прибираючи. Поверни лише переписаний текст, без пояснень.\n\n"
if os.environ.get("NAKAZ") == "мінімальний":   # варіант: правити лише мову — щоб відділити модель від наказу
    НАКАЗ = ("Виправ у тексті лише мовні помилки: російські слова й літери, суржик, зламані слова, звертання на «ви» "
             "(зроби «ти»). Усе інше лиши слово в слово: речі, кольори, числа, поради, порядок. Поверни лише текст.\n\n")
СТЕЛЯ = int(os.environ.get("MAX_SYMV", "2000"))    # зациклений текст (15 906 символів «Светлий светлий…») ріжемо до стелі
ЧИСЛА = re.compile(r"#[0-9A-Fa-f]{6}|\d+")
def основи(т): return {с.lower()[:5] for с in re.findall(r"[А-Яа-яІіЇїЄєҐґЫыЭэЁё'ʼ’]{5,}", т)}
def слова(т, без): return sorted({с for с in re.findall(r"[А-Яа-яІіЇїЄєҐґЫыЭэЁё'ʼ’]{5,}", т) if с.lower()[:5] not in без})
вих = open(sys.argv[2], "w", encoding="utf-8")
for м in [x for x in os.environ.get("MODELS", "").split(",") if x]:
    for р in open(sys.argv[1], encoding="utf-8"):
        з = json.loads(р); до = з["текст"][:СТЕЛЯ]; т0 = time.time()
        запит = urllib.request.Request(os.environ["MODEL_URL"].rstrip("/") + "/chat/completions", json.dumps(dict(model=м,
            max_tokens=3000, temperature=0.3, stream=False, reasoning_effort="none",
            messages=[dict(role="user", content=НАКАЗ + до)])).encode(), {"Content-Type": "application/json"})
        після = (json.load(urllib.request.urlopen(запит, timeout=1800))["choices"][0]["message"].get("content") or "").strip()
        с = time.time() - т0
        вих.write(json.dumps(dict(група="%s після (%s)" % (м, з["група"].split(": ")[-1]), мітка=з["мітка"], вид=з.get("вид"),
                                  текст=після, до=до, секунд=round(с, 1)), ensure_ascii=False) + "\n"); вих.flush()
        чд, чп = ЧИСЛА.findall(до), ЧИСЛА.findall(після)
        print("%s · %s · %s · %.1f с · %d→%d симв · R-LNG-UA %d→%d · числа/коди зникли %s з'явились %s\n   нема після: %s\n   нове:       %s" % (
            м, з["мітка"], з.get("вид"), с, len(до), len(після), len(російське(до)), len(російське(після)),
            sorted(set(чд) - set(чп)) or "—", sorted(set(чп) - set(чд)) or "—",
            ", ".join(слова(до, основи(після))[:12]) or "—", ", ".join(слова(після, основи(до))[:12]) or "—"))

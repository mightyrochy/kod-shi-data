"""Рядок 6753 (ЖИВІ-1016-3, Ж:02 `seed3_01`, MamayLM): replay записаного першого ходу «йога зранку, потім кава з
подругою» тим самим кодом (`прийняти_розмову` → сторож `_тримається` → `_шапка`), без моделі; промпт ходу на той самий
лист; «ви» в `says` усіх записаних ходів розмови ЖИВІ-1016-3 (слова рахує проба, не код, п.12).
Кращим: шапки зі словами поля, якого хід не записав, — 0; у формі `update` — `occasion_part`; мета — лише на її словах
про увагу. Чи модель так і напише (мета без опори 0, кава — нагодою, «ви» 0) — живий ПІСЛЯ.
Запуск: cd джерела && python3 проби/мова_хід_6753.py"""
import json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
Г, Т = "claude/zhyvi-1016-3", "аудит/живі_1016_3"
git("fetch", "-q", "origin", Г)
ВИ = re.compile(r"(?i)\b(ви|вас|вам|вами|ваш\w*|\w+[еи]те(сь|ся)?)\b")
ходів = з_ви = 0
for ф in sorted(git("ls-tree", "--full-tree", "-r", "--name-only", "origin/" + Г, Т).split("\n")):
    if "_мовний_шар_хід_розмови" not in ф:
        continue
    с = git("show", "origin/%s:%s" % (Г, ф))
    об, _ = М._обʼєкт(с.split("── ВІДПОВІДЬ", 1)[1].split("──\n", 1)[1])
    речення = [т.get("says") for т in (об or {}).get("text") or [] if isinstance(т, dict)] if isinstance(об, dict) else []
    ходів += 1; з_ви += any(ВИ.search(str(р)) for р in речення)
    if "02_ж2_спорт_коментар" in ф and "seed3_01" in ф:
        лист = json.loads(с.split("\n", 1)[1].split("── ВІДПОВІДЬ")[0])["her_new_message"]
        р = М.прийняти_розмову(с.split("── ВІДПОВІДЬ", 1)[1].split("──\n", 1)[1])
        в, вигадки = М._тримається(р["внутрішня"], [лист])
        шапка = М._шапка(об.get("header"), [], в)
        print("seed3_01: поля коду", sorted(к for к in в if к != "quotes"), "| goal:", в.get("goal"),
              "на уривку", json.dumps(в["quotes"].get("goal"), ensure_ascii=False), "| знято сторожем", len(вигадки))
        print("  шапка до неї: %d з %d ключів моделі | says: %s" % (len(шапка), len(об.get("header") or {}),
              json.dumps(р["частини"]["text"][:60], ensure_ascii=False)))
п = json.loads(М.промпт_розмови({"розмова": {"нове": лист, "історія": []}}))
т = json.dumps(п["task"], ensure_ascii=False)
print("промпт ходу: %d симв. | occasion_part у формі update: %s | мета «never as a default»: %d | «ви» в промпті: %d"
      % (len(json.dumps(п, ensure_ascii=False)), "occasion_part" in п["task"]["answer_schema"]["update"],
         т.count("never as a default"), len(re.findall(r"«ви»|\bвас\b|\bваш", т))))
print("ЖИВІ-1016-3: ходів розмови %d, з «ви» в says %d" % (ходів, з_ви))

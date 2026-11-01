"""Усі записані перші ходи кроку 3: нагоди, денна/вечірня смуга й відбиток прийнятих полів без виклику моделі.
Не тлумачить її слова заново: зміна промпту не виправляє старої відповіді. Запуск — із кореня репозиторію.
"""
import collections, hashlib, json, pathlib, re, subprocess, sys, warnings
warnings.filterwarnings("ignore")
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import мовний_шар as М, паспорт_нагоди as ПН, формальність as Ф


def головна():
    """Друкує обсяг повтору й відбиток усіх полів та смуг, зупиняється при неповному викладенні записів."""
    файли = subprocess.check_output(["git", "ls-files", "-z"], cwd=КОРІНЬ).decode("utf8").split("\0")
    файли = sorted(ф for ф in файли if re.search(r"/VIDPOVIDI/seed[^/]*_01_мовний_шар_хід_розмови\.txt$", ф))
    л, нагоди, побачення, відбиток = collections.Counter(), collections.Counter(), collections.Counter(), hashlib.sha256()
    for ф in файли:
        текст = (КОРІНЬ / ф).read_text(encoding="utf8", errors="replace")
        запит, відповідь = текст.split("── ВІДПОВІДЬ", 1)
        запит = json.loads(запит[запит.find("{"):запит.rfind("}") + 1])
        в = М.прийняти_розмову(відповідь[відповідь.find("{"):відповідь.rfind("}") + 1])["внутрішня"]
        п = М.паспорт_з_шару(в, {}, слова_ходу=[])["паспорт"]
        с = ПН.з_показу({}, п)[0]
        смуги = [Ф.смуга_ошатності(dict(с, пора=пора)) for пора in ("день", "вечір")]
        відбиток.update(json.dumps([ф, в, п, с, смуги], ensure_ascii=False, sort_keys=True, default=str).encode("utf8"))
        нагоди[в.get("occasion", "unknown")] += 1
        л["ходів"] += 1
        л["не date"] += в.get("occasion") != "date"
        if в.get("occasion") == "date":
            побачення[запит.get("her_new_message", "unknown")] += 1
    print("Обсяг:", dict(л))
    print("Нагоди:", dict(sorted(нагоди.items())))
    for слова, число in sorted(побачення.items()):
        print("date ×%d: %s" % (число, слова))
    print("Відбиток полів, паспортів, сцен і пар смуг:", відбиток.hexdigest())


if __name__ == "__main__":
    головна()

"""Повторює записані перші ходи розмови без моделі; argv[1] — коміт ДО, argv[2] — файл знімка."""
import glob, json, os, subprocess, sys
корінь = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(корінь, "джерела"))
import мовний_шар as М, паспорт_нагоди as ПН, пакет_моделі as ПМ, дріт_моделі as Д
if len(sys.argv) > 1 and sys.argv[1] != "ПІСЛЯ":
    for мод in (ПН, М):
        код = subprocess.check_output(["git", "show", sys.argv[1] + ":джерела/" + мод.__name__ + ".py"])
        exec(compile(код, мод.__file__, "exec"), мод.__dict__)
знімки = {}
for файл in sorted(glob.glob(os.path.join(корінь, "аудит/**/VIDPOVIDI/seed*_01_мовний_шар_хід_розмови.txt"), recursive=True)):
    with open(файл, encoding="utf8") as вхід:
        запис = вхід.read()
    відповідь = запис.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
    внутрішня = М.прийняти_розмову(відповідь)["внутрішня"]
    паспорт = М.паспорт_з_шару(внутрішня, {}, слова_ходу=[])["паспорт"]
    дріт = Д.випадок(ПМ.випадок_для_пакета(паспорт, "", {}))
    знімки[os.path.relpath(файл, корінь)] = дріт
assert знімки, "Нема записів для повтору"
print("Повторено записаних перших ходів: %d; винятків: 0" % len(знімки))
if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf8") as вихід:
        json.dump(знімки, вихід, ensure_ascii=False, sort_keys=True, default=str)

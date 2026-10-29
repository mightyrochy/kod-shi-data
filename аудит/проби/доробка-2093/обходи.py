"""Надрукувати адреси відомих окремих злиттів ДО й залишки ПІСЛЯ; не гейт продукту."""
import json
import pathlib
import subprocess


def main():
    """Звірити операції, знайдені читанням усіх шляхів повтору мовного шару."""
    корінь = pathlib.Path(__file__).resolve().parents[3]
    місця = {
        "джерела/мовний_шар.py": ["_ДМШ.доповнити(", "оновлення = dict(попередні"],
        "джерела/показ/мовний_шар.js": [
            "Object.assign(вих.тексти, ще.тексти)", "const кандидати = [(м.короткі",
            "Object.assign(вих.тексти, в.тексти)", "const заКлючем = new Map(р.заяви.filter",
            "Object.assign(м.тексти, м2.тексти)", "м.тексти[ключ] = перший[ключ]",
            "return чистий ? т2", "if (спроба === 2 && р2.причина && перша)"],
        "джерела/показ/оцінка.js": ["Object.assign(м.тексти, м2.тексти)"]}
    результат = {}
    for назва in ("ДО", "ПІСЛЯ"):
        знахідки = []
        for файл, ознаки in місця.items():
            текст = (subprocess.check_output(["git", "show", "1dfe0196adef1b8e8bd60488afc4fdf65215551d:" + файл],
                                            cwd=корінь).decode("utf8") if назва == "ДО"
                     else (корінь / файл).read_text(encoding="utf8"))
            for номер, рядок in enumerate(текст.splitlines(), 1):
                if any(ознака in рядок for ознака in ознаки):
                    знахідки.append(dict(адреса=файл + ":" + str(номер), операція=рядок.strip()))
        результат[назва] = dict(обходів=len(знахідки), місця=знахідки)
    print(json.dumps(результат, ensure_ascii=False, indent=2))
    (pathlib.Path(__file__).parent / "обходи.json").write_text(
        json.dumps(результат, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Тест приладу кореня ПК-межа-без-джерела на малому дереві: три види джерел, вердикти, рішення менеджера 31.10.

Запуск з кореня репозиторію: python3 -m unittest джерела/прилади/тест_корінь_пк_межа.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import корінь_пк_межа as К  # noqa: E402

ПРАВИЛО = """# Роль

- Зведення — не частіше ніж раз на 6 год (діагностика 26.10).
- Проба — до 40 рядків, друкує факт.
- Свіжа сесія раз на дві доби («так» власника 25.10).
- Наряд понад 30000 знаків — TASK_TOO_LONG.
- `HANG` після 120 хв без подій.
"""
СМУГИ = """{
  "v": 2,
  "slots": {"codex": {"n": 54, "джерело": "вимір: диск C: 29.10 — 54"}},
  "poll_minutes": {"n": 2, "джерело": ""},
  "claude_hang_minutes": {"n": 120, "джерело": "вимір 30.10 events.tsv: найдовший проміжок 97 хв"}
}
"""
КОД = """param(
    [double]$HangMinutes = 120,
    [int]$StatusIssue = 1856
)
# Межі коду.
$script:Defaults = @{ poll_minutes = 2; claude_hang_minutes = 120 }
$script:MaxRetakes = 5
function Get-Limits {
    <# Довідка: -gt 999 тут не код. #>
    if (-not (Test-LimitSource $s)) {
        $l.unsourced += $f
        $v = $prev
    }
    $x = Get-Limit $script:Limits 'HangMinutes' 'claude_hang_minutes'
}
function Invoke-Run {
    if ($text.Length -gt 30000) { return }  # жодного джерела
    Start-Sleep -Milliseconds 50
}
"""


def дерево(правило=ПРАВИЛО, код=КОД, вердикти=""):
    т = tempfile.mkdtemp(prefix="пк_межа_")
    for шлях, текст in (("аудит/КОД.md", правило), ("аудит/адаптери/gemini/смуги.json", СМУГИ),
                        ("аудит/адаптери/gemini/run.ps1", код), (К.ВЕРДИКТИ, вердикти)):
        os.makedirs(os.path.dirname(os.path.join(т, шлях)), exist_ok=True)
        with open(os.path.join(т, шлях), "w", encoding="utf-8") as ф:
            ф.write(текст)
    return т


def за_збігом(усі):
    return {(о.вид, о.збіг): о for о in усі}


class Прилад(unittest.TestCase):
    def test_правила_без_вердикту(self):
        о = за_збігом(К.зібрати(дерево())[0])
        self.assertEqual(о[("правила", "до 40")].пункт, 1)          # нема джерела в пункті
        self.assertEqual(о[("правила", "раз на 6 год")].пункт, 2)          # джерело-діагностика без числа
        self.assertEqual(о[("правила", "30000 знаків")].пункт, 1)   # додаткова регулярка
        self.assertEqual(о[("правила", "120 хв")].пункт, 1)         # HANG без помітки виміру

    def test_вердикт_за_текстом_а_не_рядком(self):
        усі = К.зібрати(дерево())[0]
        ключ = next(о.ключ for о in усі if о.збіг == "раз на дві доби")
        зсунуте = ПРАВИЛО.replace("# Роль\n", "# Роль\n\nНовий абзац без чисел.\n")
        о = за_збігом(К.зібрати(дерево(зсунуте, вердикти=ключ + "\tМС\t—\tтак 25.10\n"))[0])
        self.assertEqual(о[("правила", "раз на дві доби")].пункт, 0)
        змінене = зсунуте.replace("раз на дві доби (", "раз на дві доби, без поспіху (")
        о = за_збігом(К.зібрати(дерево(змінене, вердикти=ключ + "\tМС\t—\tтак 25.10\n"))[0])
        self.assertEqual(о[("правила", "раз на дві доби")].пункт, 2)  # текст пункту змінено — вердикт знову потрібен

    def test_конфіг_і_рішення_менеджера(self):
        о = за_збігом(К.зібрати(дерево())[0])
        self.assertEqual(о[("конфіг", "slots.codex = 54")].пункт, 0)        # слоти з поміткою виміру
        self.assertEqual(о[("конфіг", "poll_minutes = 2")].пункт, 1)        # порожнє «джерело»
        self.assertEqual(о[("конфіг", "claude_hang_minutes = 120")].пункт, 0)  # HANG з «вимір ДД.ММ»

    def test_код(self):
        усі = К.зібрати(дерево())[0]
        код = {о.збіг: о.пункт for о in усі if о.вид == "код"}
        self.assertEqual(код["HangMinutes 120"], 4)                # параметр, зв'язаний з полем через Get-Limit
        self.assertEqual(код["Defaults.poll_minutes 2"], 4)
        self.assertEqual(код["Defaults.claude_hang_minutes 120"], 4)
        self.assertEqual(код["без джерела — попереднє гілка"], 4)
        self.assertEqual(код["MaxRetakes 5"], 1)
        self.assertEqual(код["порівняння 30000"], 1)
        self.assertEqual(код["пауза 50"], 1)                         # без вердикту — місце
        self.assertNotIn("порівняння 999", код)                      # блок-коментар — не код
        self.assertEqual(код["StatusIssue 1856"], 1)

    def test_вердикти_коду_і_дубль(self):
        усі = К.зібрати(дерево())[0]
        ключі = {о.збіг: о.ключ for о in усі}
        дані = "\n".join((ключі["пауза 50"] + "\tНМ\t—\tповтор запису",
                          ключі["StatusIssue 1856"] + "\tНМ\t—\tномер issue",
                          ключі["Defaults.poll_minutes 2"] + "\tНМ\t—\tспроба зняти п.4 вердиктом",
                          ключі["30000 знаків"] + "\tДУБЛЬ\t—\tте саме число"))
        код = {о.збіг: о.пункт for о in К.зібрати(дерево(вердикти=дані))[0]}
        self.assertEqual(код["пауза 50"], 0)
        self.assertEqual(код["StatusIssue 1856"], 0)
        self.assertEqual(код["Defaults.poll_minutes 2"], 4)          # п.4 детермінований
        self.assertEqual(код["30000 знаків"], 0)
        зсунутий = КОД.replace("function Invoke-Run {", "# ще коментар\n\nfunction Invoke-Run {")
        код = {о.збіг: о.пункт for о in К.зібрати(дерево(код=зсунутий, вердикти=дані))[0]}
        self.assertEqual(код["пауза 50"], 0)                         # ключ — функція й текст рядка, не номер


if __name__ == "__main__":
    unittest.main()

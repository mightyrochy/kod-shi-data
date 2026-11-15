# -*- coding: utf-8 -*-
"""Тест приладу `живий_після_прогнано.py`.

1. Розбір рядка — випадки стенда обгортки (`сценарії_живий_рядок.ps1`, сценарій 2).
2. Штучна історія git: злиття до й після збірки звіту, сквош і коміт злиття, «не потрібен», сцена в кількох PR,
   сцена, чий id — префікс іншого, чужий автор, злиття до вікна, звіт без межі й межа не за форматом.
3. Прогнано за записами (`прогнані_записами` — повтор `Get-AutoRanPairs`): завершений запис, відмова питання й сцени, rc 2,
   сцена «функція», злиття не предок SHA запису, перенесений запис; паритет з `Get-AutoRanPairs` — на штучній історії
   й на справжньому дереві.
4. Паритет розбору з `Get-LiveAfterLines` обгортки (`queue_lanes.ps1`) — через `pwsh` на реєстрі, тілах комітів
   `main` і файлах `аудит/` з рядком `ЖИВИЙ ПІСЛЯ`. Нема `pwsh` — «не виміряно»; у CI (`CI` задано) це провал.

Прогін:  python3 джерела/прилади/тест_живий_після_прогнано.py   → останній рядок «OK» чи «ПРОВАЛ: N»
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ТУТ)
import живий_після_прогнано as прилад  # noqa: E402

КОРІНЬ = os.path.abspath(os.path.join(ТУТ, "..", ".."))
провалів = 0


def перевірити(назва, умова):
    global провалів
    print(("✓ " if умова else "✗ ") + назва)
    if not умова:
        провалів += 1


# --- 1. розбір ------------------------------------------------------------------------------------------------------
def розбір():
    реєстр = прилад.реєстр_сцен("# Поля: id|…\nж2_побачення_вечір|a|b|c|повне|\nж3_співбесіда|a|b|c|повне|\n"
                                 "ж7_прогулянка_субота|a|b|c|функція|\nкоротка|a|b\n")
    перевірити("реєстр: коментар і короткий рядок пропущено, режим — п'яте поле",
               реєстр == {"ж2_побачення_вечір": "повне", "ж3_співбесіда": "повне", "ж7_прогулянка_субота": "функція"})

    def р(тіло):
        return прилад.рядки_живий_після(тіло, реєстр)

    ок = р("ЖИВИЙ ПІСЛЯ: ж2_побачення_вечір — чи зник хибний ліміт → повне → main → ремонтів менше")
    перевірити("повний рядок: id, питання, режим",
               len(ок) == 1 and not ок[0]["error"] and ок[0]["id"] == "ж2_побачення_вечір"
               and ок[0]["question"].startswith("чи зник") and ок[0]["mode"] == "повне")
    перевірити("«серія 2 `id`» — id не голий", "не голий" in р("ЖИВИЙ ПІСЛЯ: серія 2 `б1_доречність` — у картці")[0]["error"])
    перевірити("без « — » — вада", "нема « — »" in р("ЖИВИЙ ПІСЛЯ: ж3_співбесіда (стенд) → повне")[0]["error"])
    перевірити("id поза реєстром — вада", "нема першим полем" in р("ЖИВИЙ ПІСЛЯ: ж9_нема — питання")[0]["error"])
    перевірити("id з урахуванням регістру", bool(р("ЖИВИЙ ПІСЛЯ: Ж3_співбесіда — питання")[0]["error"]))
    перевірити("порожнє питання — вада", bool(р("ЖИВИЙ ПІСЛЯ: ж3_співбесіда — ")[0]["error"]))
    перевірити("рядок у списку — вада маркера", "маркера списку" in р("- ЖИВИЙ ПІСЛЯ: ж3_співбесіда — п")[0]["error"])
    відступ = р("   ЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання\r")
    перевірити("пробіли й CR обрізано", len(відступ) == 1 and not відступ[0]["error"])
    глибоко = р("Опис\n\nТекст про ЖИВИЙ ПІСЛЯ у середині\nЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання")
    перевірити("згадка посеред рядка — не рядок", len(глибоко) == 1 and not глибоко[0]["error"])
    склеєно = р("ЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання\nпродовження абзацу\nЩо змінено: інше\n")
    перевірити("продовження абзацу склеєно, підпис поля — межа",
               len(склеєно) == 1 and склеєно[0]["question"] == "питання продовження абзацу" and склеєно[0]["last"] == 1)
    перевірити("«не потрібен» — вада, не питання", bool(р("ЖИВИЙ ПІСЛЯ: не потрібен — прилад")[0]["error"]))
    перевірити("тіло без рядка — нічого", р("Звичайний опис") == [] and р("") == [] and р(None) == [])


# --- 2. штучна історія ----------------------------------------------------------------------------------------------
def _git(тека, *аргументи, дата=None, автор="mightyrochy", вхід=None):
    оточення = dict(os.environ, GIT_AUTHOR_NAME=автор, GIT_AUTHOR_EMAIL="a@example.invalid",
                    GIT_COMMITTER_NAME="GitHub", GIT_COMMITTER_EMAIL="noreply@example.invalid")
    if дата:
        оточення.update(GIT_AUTHOR_DATE=дата, GIT_COMMITTER_DATE=дата)
    готово = subprocess.run(["git", "-C", тека, *аргументи], env=оточення, capture_output=True, text=True, input=вхід)
    if готово.returncode:
        raise RuntimeError(готово.stderr)
    return готово.stdout.strip()


def _коміт(тека, файли, повідомлення, дата, автор="mightyrochy"):
    for шлях, текст in файли.items():
        повний = os.path.join(тека, шлях)
        os.makedirs(os.path.dirname(повний), exist_ok=True)
        with open(повний, "w", encoding="utf-8") as ф:
            ф.write(текст)
    _git(тека, "add", "-A")
    _git(тека, "commit", "-q", "--allow-empty", "-m", повідомлення, дата=дата, автор=автор)
    return _git(тека, "rev-parse", "HEAD")


def історія():
    тека = tempfile.mkdtemp(prefix="живий-після-")
    стара = os.getcwd()
    try:
        _git(тека, "init", "-q", "-b", "main")
        реєстр = ("# Поля: id|жінка|CHAT_TEXT|вхід|режим\nж1_а|x|y|z|повне\nж1_а_б|x|y|z|розмова\n"
                  "ж2_в|x|y|z|повне +фото\nж3_г|x|y|z|функція\n")
        _коміт(тека, {"аудит/проби/живі_сцени.txt": реєстр}, "основа", "2026-11-01T00:00:00Z")
        _коміт(тека, {"а.txt": "0"}, "Давнє (#1)\n\nЖИВИЙ ПІСЛЯ: ж1_а — до вікна", "2026-11-02T00:00:00Z")
        _коміт(тека, {"б.txt": "1"},
               "Сквош (#10)\n\n* перший\n\nЖИВИЙ ПІСЛЯ: ж1_а — питання 1\n\n* другий\n\nЖИВИЙ ПІСЛЯ: ж1_а — питання 1\n"
               "ЖИВИЙ ПІСЛЯ: ж2_в — фото", "2026-11-06T10:00:00Z")
        _коміт(тека, {"в.txt": "2"},
               "Другий (#11)\n\nЖИВИЙ ПІСЛЯ: не потрібен — прилад без моделі\n\nЖИВИЙ ПІСЛЯ: ж1_а — інше питання\n"
               "ЖИВИЙ ПІСЛЯ: ж1_а_б — розмова", "2026-11-06T11:00:00Z")
        _коміт(тека, {"г.txt": "3"}, "Форк (#12)\n\nЖИВИЙ ПІСЛЯ: ж1_а — чуже", "2026-11-06T12:00:00Z", автор="хтось")
        # Коміт злиття PR з гілки: рядок — у коміті гілки, не в темі злиття.
        основа = _git(тека, "rev-parse", "HEAD")
        _git(тека, "checkout", "-q", "-b", "гілка")
        _коміт(тека, {"д.txt": "4"}, "крок гілки\n\nЖИВИЙ ПІСЛЯ: ж3_г — функція в хмарі", "2026-11-06T12:30:00Z")
        _git(тека, "checkout", "-q", "main")
        _git(тека, "merge", "-q", "--no-ff", "-m", "Merge pull request #13 from mightyrochy/гілка\n\nНазва", "гілка",
             дата="2026-11-06T13:00:00Z")
        assert _git(тека, "rev-parse", "HEAD^1") == основа
        збірка = _коміт(тека, {"index.html": "збірка"}, "збірка: x", "2026-11-06T14:00:00Z", автор="github-actions[bot]")
        _коміт(тека, {"е.txt": "5"}, "Після збірки (#14)\n\nЖИВИЙ ПІСЛЯ: ж1_а — після", "2026-11-06T15:00:00Z")
        звіт = ("# Звіт\n\n| ж1_а | повне |\n| ж1_а_б | розмова |\n\nПЕРЕВІРЕНО ЗБІРКУ: " + збірка + "\n")
        _коміт(тека, {"аудит/проби/автоживий-" + збірка + "/ЗВІТ.md": звіт,
                      "аудит/проби/автоживий-" + збірка + "/ж2_в/лог.txt": "лог"},
               "Звіт автоживий (#15)", "2026-11-06T16:00:00Z")
        _коміт(тека, {"аудит/проби/нічний/ЗВІТ.md": "Нічний: ж1_а, ж3_г\n\n## ПЕРЕВІРЕНО ЗБІРКУ\n\nРядка нема\n",
                      "аудит/проби/функція/ЗВІТ.md": "ПЕРЕВІРЕНО ЗБІРКУ `" + збірка + "` — сцена ж3_г\n"},
               "Звіти без межі (#16)", "2026-11-06T17:00:00Z")
        os.chdir(тека)
        від, зараз = прилад._час("2026-11-05T00:00:00Z"), прилад._час("2026-11-06T18:00:00Z")
        лічба = прилад.лічити("main", від, зараз)
        питання = лічба["питання"]
        перевірити("M: (PR × сцена) лише довірених злиттів вікна — 6",
                   sorted(питання) == sorted([(10, "ж1_а"), (10, "ж2_в"), (11, "ж1_а"), (11, "ж1_а_б"), (13, "ж3_г"),
                                              (14, "ж1_а")]))
        перевірити("повтор рядка в двох комітах сквошу — одне питання; рядків 8 з повтором",
                   лічба["рядків"] == 8 and лічба["pr_з_рядком"] == 4)
        непрогнані = sorted((п["pr"], п["сцена"]) for п in лічба["непрогнані"])
        перевірити("N = 4: злиття до збірки, сцену звіт згадує словом чи текою",
                   len(питання) - len(лічба["непрогнані"]) == 4)
        перевірити("злиття після збірки — непрогнане; функція, якої звіт не згадує, — непрогнана",
                   непрогнані == [(13, "ж3_г"), (14, "ж1_а")])
        перевірити("коміт злиття: питання з коміту гілки, час — злиття",
                   питання[(13, "ж3_г")]["час"] == прилад._час("2026-11-06T13:00:00Z")
                   and питання[(13, "ж3_г")]["режим"] == "функція")
        перевірити("«не потрібен» — вадний рядок, не питання",
                   [(в["pr"], в["не_потрібен"]) for в in лічба["вадні"]] == [(11, True)])
        перевірити("чужий автор — пропущено", лічба["чужі"] == [(12, "хтось")])
        перевірити("звіти без межі — не рахуються; згадано непрогнаних сцен, злитих раніше за звіт: 2 і 1",
                   sorted((з["шлях"], з["згадано"]) for з in лічба["без_межі"])
                   == [("аудит/проби/нічний/ЗВІТ.md", 2), ("аудит/проби/функція/ЗВІТ.md", 1)])
        перевірити("межа не за форматом — у переліку", лічба["не_за_форматом"] == ["аудит/проби/функція/ЗВІТ.md"])
        вивід = subprocess.run([sys.executable, os.path.join(ТУТ, "живий_після_прогнано.py"), "--main", "main",
                                "--від", "2026-11-05T00:00:00Z", "--зараз", "2026-11-06T18:00:00Z"],
                               capture_output=True, text=True, cwd=тека)
        рядки = вивід.stdout.strip().splitlines()
        перевірити("прилад без тіл: код 0, «прогнано: 4 з 6» з поміткою нижньої межі, години від злиття",
                   вивід.returncode == 0 and рядки[-1] == "прогнано: 4 з 6 (без тіл PR: M — нижня межа)"
                   and any(р.startswith("  #14\t2026-11-06 15:00Z\tж1_а\tповне\t3.0") for р in рядки))
        # Тіла PR — джерело плану обгортки: #10 у тілі має інше, ніж у комітах; #11 у файлі нема (лише повідомлення);
        # #20 влито пачкою (свого коміту нема) — злиття за часом merged_at, до збірки; дві відповіді пошуку підряд.
        тіла_шлях = os.path.join(тека, "тіла.json")
        with open(тіла_шлях, "w", encoding="utf-8") as ф:
            json.dump({"total_count": 5, "items": [
                {"number": 10, "body": "ЖИВИЙ ПІСЛЯ: ж2_в — лише фото", "user": {"login": "mightyrochy"},
                 "pull_request": {"merged_at": "2026-11-06T10:00:00Z"}},
                {"number": 13, "body": "ЖИВИЙ ПІСЛЯ: ж3_г — функція", "user": {"login": "mightyrochy"},
                 "pull_request": {"merged_at": "2026-11-06T13:00:00Z"}}]}, ф, ensure_ascii=False)
            json.dump({"total_count": 5, "items": [
                {"number": 14, "body": "ЖИВИЙ ПІСЛЯ: ж1_а — після", "user": {"login": "mightyrochy"},
                 "pull_request": {"merged_at": "2026-11-06T15:00:00Z"}},
                {"number": 20, "body": "ЖИВИЙ ПІСЛЯ: ж1_а_б — з пачки", "user": {"login": "mightyrochy"},
                 "pull_request": {"merged_at": "2026-11-06T11:30:00Z"}}]}, ф, ensure_ascii=False)
        тіла, попередження = прилад.прочитати_тіла([тіла_шлях])
        перевірити("файл тіл: дві відповіді пошуку підряд, неповнота — попередження",
                   sorted(тіла) == [10, 13, 14, 20] and len(попередження) == 1 and "5" in попередження[0])
        з_тіл = прилад.лічити("main", від, зараз, тіла)
        перевірити("з тілами: питання — з тіл PR, пачка — за часом злиття",
                   sorted(з_тіл["питання"]) == [(10, "ж2_в"), (13, "ж3_г"), (14, "ж1_а"), (20, "ж1_а_б")]
                   and з_тіл["за_часом"] == [20] and з_тіл["лише_в_повідомленні"] == [11])
        перевірити("з тілами: прогнано #10 (тека сцени) і #20 (злиття до збірки), не #13 і #14",
                   sorted((п["pr"], п["сцена"]) for п in з_тіл["непрогнані"]) == [(13, "ж3_г"), (14, "ж1_а")])
        вивід = subprocess.run([sys.executable, os.path.join(ТУТ, "живий_після_прогнано.py"), "--main", "main",
                                "--від", "2026-11-05T00:00:00Z", "--зараз", "2026-11-06T18:00:00Z", "--тіла", тіла_шлях],
                               capture_output=True, text=True, cwd=тека)
        перевірити("прилад з --тіла: «прогнано: 2 з 4»", вивід.stdout.strip().splitlines()[-1] == "прогнано: 2 з 4")
        записи_історії(тека, прилад, від, зараз)
    finally:
        os.chdir(стара)
        shutil.rmtree(тека, ignore_errors=True)


def запис_сцени(тека_запису, sha, rc=0, обмін=True, без=()):
    файли = {"результат.json": json.dumps({"rc": rc, "sha": sha}), "повтор.json": "{}", "лог.txt": "лог",
             "знімки/доказ.json": "{}"}
    if обмін:
        файли["VIDPOVIDI/обмін/1.json"] = "{}"
    return {тека_запису + "/" + ш: т for ш, т in файли.items() if ш not in без}


def записи_історії(тека, прилад, від, зараз):
    """Прогнано за записами: Е1-нічний-живий-20261106 прогнав (14, ж1_а) і (13, ж3_г) — друга сцена «функція»."""
    код = _git(тека, "rev-parse", "HEAD")
    д = "аудит/проби/Е1-нічний-живий-20261106"
    план = {"scenes": {"ж1_а": [{"pr": 14, "question": "q"}, {"pr": 10, "question": "q"}], "ж1_а_б": [{"pr": 11}],
                       "ж2_в": [{"pr": 10}], "ж3_г": [{"pr": 13}], "ж5_д": [{"pr": 14}]}, "cloud": {}, "build": код}
    done = "\n".join(json.dumps(р, ensure_ascii=False) for р in [
        {"сцена": "ж2_в", "відмова": "нема фото"}, {"сцена": "ж1_а", "pr": 10, "відмова_питання": "режим"}])
    файли = {д + "/ПЛАН.json": json.dumps(план, ensure_ascii=False), д + "/done.txt": done + "\n"}
    файли.update(запис_сцени(д + "/ж1_а", код))
    файли.update(запис_сцени(д + "/ж1_а_б", код, rc=2))
    файли.update(запис_сцени(д + "/ж2_в", код))
    файли.update(запис_сцени(д + "/ж3_г", код))
    файли.update(запис_сцени(д + "/ж5_д", код, обмін=False))
    _коміт(тека, файли, "Е1 нічний (#17)", "2026-11-06T17:30:00Z")
    ран = прилад.прогнані_записами("main")
    перевірити("записи: завершена сцена — пари плану, відмова питання й сцени, rc 2 і запис без обміну — ні",
               sorted(ран) == ["13|ж3_г", "14|ж1_а"])
    перевірити("записи: ключ — PR|сцена, SHA — коду запису", ран["14|ж1_а"] == [{"sha": код, "звіт": "Е1-нічний-живий-20261106"}])
    лічба = прилад.лічити("main", від, зараз)
    за_записами = sorted((п["pr"], п["сцена"]) for п in лічба["питання"].values() if п["записи"])
    перевірити("лічба: прогнано за записами — (14, ж1_а); «функція» (13, ж3_г) — ні; (10, ж1_а) — відмова питання",
               за_записами == [(14, "ж1_а")])
    перевірити("лічба: (14, ж1_а) не в непрогнаних, (13, ж3_г) — в непрогнаних",
               sorted((п["pr"], п["сцена"]) for п in лічба["непрогнані"]) == [(13, "ж3_г")])
    # Злиття після коду запису — не предок: запис його не прогнав.
    _коміт(тека, {"є.txt": "6"}, "Пізніше (#18)\n\nЖИВИЙ ПІСЛЯ: ж5_д — ще", "2026-11-06T17:40:00Z")
    пізній = прилад.лічити("main", від, прилад._час("2026-11-06T18:00:00Z"))
    перевірити("злиття PR після коду запису — не прогнано записом",
               not [п for п in пізній["питання"].values() if п["pr"] == 18 and п["записи"]])
    # Перенесений `нова_база.js` запис: теки сцени в наряді нема, шлях_запису називає її.
    д2 = "аудит/проби/Е1-нічний-живий-20261105"
    база = "аудит/проби/нічні/20261105/ж1_а_б"
    план2 = {"scenes": {"ж1_а_б": [{"pr": 11}]}, "cloud": {}}
    файли2 = {д2 + "/ПЛАН.json": json.dumps(план2), д2 + "/done.txt": "\n",
              база + "/походження.json": json.dumps({"шлях_запису": д2.replace("/", "\\") + "\\ж1_а_б"})}
    файли2.update(запис_сцени(база, код))
    _коміт(тека, файли2, "Е1 перенесений (#19)", "2026-11-06T17:50:00Z")
    ран2 = прилад.прогнані_записами("main", ["Е1-нічний-живий-20261105"])
    перевірити("перенесений запис — за походження.json", sorted(ран2) == ["11|ж1_а_б"])
    паритет_записів(тека, "HEAD", "штучна історія")


# --- 3. паритет з PowerShell ----------------------------------------------------------------------------------------
PS = r"""
# Імена змінних PowerShell нечутливі до регістру: параметр шляху реєстру не може зватися `$Registry`, бо `$registry`
# нижче — таблиця, і `[string]` параметра перетворив би її на рядок «System.Collections.Hashtable».
param([string]$Source, [string]$RegistryPath, [string]$BodiesPath, [string]$OutPath)
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($Source, [ref]$null, [ref]$errors)
if ($errors -and $errors.Count) { throw "queue_lanes.ps1 не розбирається" }
$names = @('Get-LiveSceneRegistry', 'Get-LiveAfterLines')
$found = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $names -ccontains $n.Name }, $true))
if ($found.Count -ne $names.Count) { throw 'нема функцій розбору' }
foreach ($function in $found) { . ([scriptblock]::Create($function.Extent.Text)) }
$registry = Get-LiveSceneRegistry ([IO.File]::ReadAllText($RegistryPath, $utf))
$lines = New-Object 'System.Collections.Generic.List[string]'
$lines.Add((ConvertTo-Json -InputObject $registry -Compress))
foreach ($body in @(ConvertFrom-Json ([IO.File]::ReadAllText($BodiesPath, $utf)))) {
    $items = @(Get-LiveAfterLines ([string]$body) $registry | ForEach-Object {
        [ordered]@{line=$_.line;first=$_.first;last=$_.last;id=$_.id;question=$_.question;mode=$_.mode;error=$_.error} })
    $lines.Add((ConvertTo-Json -InputObject @($items) -Compress -Depth 4))
}
[IO.File]::WriteAllLines($OutPath, $lines, $utf)
"""


PS_ЗАПИСИ = r"""
param([string]$Source, [string]$Repo, [string]$Head, [string]$DirsPath, [string]$OutPath)
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$script:AutoPlanMarginHours = 6
$script:Repo = $Repo
function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
    $psi = New-Object Diagnostics.ProcessStartInfo 'git'
    foreach ($a in (@('-C', $script:Repo, '-c', 'core.quotepath=false') + $GitArgs)) { [void]$psi.ArgumentList.Add($a) }
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.UseShellExecute = $false
    $psi.StandardOutputEncoding = [Text.Encoding]::UTF8
    $p = [Diagnostics.Process]::Start($psi)
    $err = $p.StandardError.ReadToEndAsync()
    $out = $p.StandardOutput.ReadToEnd(); $p.WaitForExit()
    [pscustomobject]@{Code=$p.ExitCode; Out=$out; Err=$err.Result}
}
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($Source, [ref]$null, [ref]$errors)
if ($errors -and $errors.Count) { throw "queue_lanes.ps1 не розбирається" }
$names = @('Get-JsonProp', 'ConvertTo-AutoTime', 'Get-AutoRanPairs')
$found = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $names -ccontains $n.Name }, $true))
if ($found.Count -ne $names.Count) { throw 'нема функцій запису' }
foreach ($function in $found) { . ([scriptblock]::Create($function.Extent.Text)) }
$reports = @(); $i = 0
foreach ($dir in @(ConvertFrom-Json ([IO.File]::ReadAllText($DirsPath, $utf)))) {
    $i++; $reports += @([pscustomobject]@{number=$i; head=@{ref=('claude/' + $dir); sha=$Head}})
}
$ran = Get-AutoRanPairs $reports ([datetimeoffset]::MinValue)
$lines = New-Object 'System.Collections.Generic.List[string]'
foreach ($key in @($ran.Keys | Sort-Object)) { $lines.Add($key + "`t" + ((@($ran[$key] | ForEach-Object { $_.sha }) | Sort-Object) -join ',')) }
[IO.File]::WriteAllLines($OutPath, $lines, $utf)
"""


def паритет_записів(тека, голова, назва):
    """`Get-AutoRanPairs` і `прогнані_записами` дають ті самі пари й SHA записів на одному дереві."""
    pwsh = shutil.which("pwsh")
    if not pwsh:
        print("— паритет записів (" + назва + "): не виміряно (нема pwsh)")
        if os.environ.get("CI"):
            перевірити("у CI pwsh є", False)
        return
    дерево = прилад._текст(прилад.git("-C", тека, "ls-tree", "-r", "--name-only", голова, "--", "аудит/проби").stdout)
    теки = sorted({ш.split("/")[2] for ш in дерево.splitlines() if ш.count("/") >= 3 and ш.split("/")[2]
                   and прилад.ТЕКА_ЗВІТУ.match(ш.split("/")[2])})
    стара = os.getcwd()
    тимч = tempfile.mkdtemp(prefix="паритет-записів-")
    try:
        скрипт, вхід, вихід = (os.path.join(тимч, і) for і in ("p.ps1", "теки.json", "вихід.txt"))
        with open(скрипт, "w", encoding="utf-8-sig") as ф:
            ф.write(PS_ЗАПИСИ)
        with open(вхід, "w", encoding="utf-8") as ф:
            json.dump(теки, ф, ensure_ascii=False)
        sha = прилад._текст(прилад.git("-C", тека, "rev-parse", голова).stdout).strip()
        готово = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File", скрипт, "-Source",
                                 os.path.join(КОРІНЬ, "аудит/адаптери/gemini/queue_lanes.ps1"), "-Repo", тека, "-Head", sha,
                                 "-DirsPath", вхід, "-OutPath", вихід], capture_output=True, text=True)
        if готово.returncode:
            перевірити("pwsh виконав Get-AutoRanPairs (" + назва + "): " + готово.stderr[-500:], False)
            return
        with open(вихід, encoding="utf-8") as ф:
            очікувано = {}
            for рядок in ф.read().split("\n"):
                if рядок:
                    ключ, _, шас = рядок.partition("\t")
                    очікувано[ключ] = шас.split(",")
        os.chdir(тека)
        мої = {к: sorted(з["sha"] for з in v) for к, v in прилад.прогнані_записами(sha, теки).items()}
        os.chdir(стара)
        перевірити(f"паритет Get-AutoRanPairs ({назва}): звітів {len(теки)}, пар {len(очікувано)}, моїх {len(мої)}",
                   {к: sorted(v) for к, v in очікувано.items()} == мої)
    finally:
        os.chdir(стара)
        shutil.rmtree(тимч, ignore_errors=True)


def паритет():
    pwsh = shutil.which("pwsh")
    if not pwsh:
        print("— паритет з PowerShell: не виміряно (нема pwsh)")
        if os.environ.get("CI"):
            перевірити("у CI pwsh є", False)
        return
    реєстр_шлях = os.path.join(КОРІНЬ, прилад.РЕЄСТР_ШЛЯХ)
    with open(реєстр_шлях, encoding="utf-8") as ф:
        реєстр = прилад.реєстр_сцен(ф.read())
    тіла = [
        "ЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання\nпродовження\n1. список",
        "ЖИВИЙ ПІСЛЯ: ж3_співбесіда — п\n\u00a0далі\u2003\nЗапис: поле",
        "  * ЖИВИЙ ПІСЛЯ: ж3_співбесіда — п",
        "ЖИВИЙ ПІСЛЯ:ж3_співбесіда — п\nЖИВИЙ ПІСЛЯ: ж3_співбесіда —\nЖИВИЙ ПІСЛЯ: Ж3_СПІВБЕСІДА — п",
        "ЖИВИЙ ПІСЛЯ: ж3_співбесіда — п\n|таблиця|\nЖИВИЙ ПІСЛЯ: ж1_оціни_образ_6б — 2\n`код`",
        "\ufeffЖИВИЙ ПІСЛЯ: ж3_співбесіда — п\r\n\r\nЖИВИЙ ПІСЛЯ: \U0001d400 — п",
        "",
    ]
    log = subprocess.run(["git", "-C", КОРІНЬ, "log", "-n", "2000", "--format=%B%x1e", "HEAD"],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    тіла += [т for т in log.split("\x1e") if "ЖИВИЙ ПІСЛЯ" in т]
    файли = subprocess.run(["git", "-C", КОРІНЬ, "-c", "core.quotepath=false", "grep", "-l", "-z", "ЖИВИЙ ПІСЛЯ",
                            "HEAD", "--", "аудит"], capture_output=True).stdout.decode("utf-8").split("\0")
    for шлях in [ш.split(":", 1)[1] for ш in файли if ":" in ш][:400]:
        with open(os.path.join(КОРІНЬ, шлях), encoding="utf-8", errors="replace") as ф:
            текст = ф.read()
        if len(текст) <= 300_000:  # великі зведення прогонів — не тіла PR, лише сповільнюють pwsh
            тіла.append(текст)
    тека = tempfile.mkdtemp(prefix="паритет-")
    try:
        скрипт, вхід, вихід = (os.path.join(тека, і) for і in ("p.ps1", "тіла.json", "вихід.txt"))
        with open(скрипт, "w", encoding="utf-8-sig") as ф:
            ф.write(PS)
        with open(вхід, "w", encoding="utf-8") as ф:
            json.dump(тіла, ф, ensure_ascii=False)
        готово = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File", скрипт, "-Source",
                                 os.path.join(КОРІНЬ, "аудит/адаптери/gemini/queue_lanes.ps1"), "-RegistryPath", реєстр_шлях,
                                 "-BodiesPath", вхід, "-OutPath", вихід], capture_output=True, text=True)
        if готово.returncode:
            перевірити("pwsh виконав розбір: " + готово.stderr[-500:], False)
            return
        with open(вихід, encoding="utf-8") as ф:
            # Лише «\n» (WriteAllLines на Linux): splitlines різав би й на U+2028, U+0085 у JSON без екранування.
            рядки = ф.read().rstrip("\n").split("\n")
        перевірити("паритет реєстру сцен (" + str(len(реєстр)) + " id)", json.loads(рядки[0]) == реєстр)
        розбіжних = []
        пунктів = 0
        for номер, (тіло, ps) in enumerate(zip(тіла, рядки[1:])):
            очікувано = json.loads(ps)
            мій = [{к: п[к] for к in ("line", "first", "last", "id", "question", "mode", "error")}
                   for п in прилад.рядки_живий_після(тіло, реєстр)]
            пунктів += len(мій)
            if мій != очікувано:
                розбіжних.append((номер, мій, очікувано))
        перевірити(f"паритет Get-LiveAfterLines: тіл {len(тіла)}, пунктів {пунктів}, розбіжних {len(розбіжних)}",
                   len(рядки) == len(тіла) + 1 and not розбіжних)
        for номер, мій, очікувано in розбіжних[:3]:
            print("   тіло", номер, "\n   Python:", json.dumps(мій, ensure_ascii=False)[:600],
                  "\n   PowerShell:", json.dumps(очікувано, ensure_ascii=False)[:600])
    finally:
        shutil.rmtree(тека, ignore_errors=True)


if __name__ == "__main__":
    розбір()
    історія()
    паритет()
    паритет_записів(КОРІНЬ, "HEAD", "дерево репозиторію")
    print("OK" if not провалів else f"ПРОВАЛ: {провалів}")
    sys.exit(1 if провалів else 0)

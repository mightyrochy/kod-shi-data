[Console]::OutputEncoding = [Text.UTF8Encoding]::new()
function Vodij($krok, $model, $godyn) {
  $d = "$env:USERPROFILE\proba-gemini\$krok"; if (-not (Test-Path "$d\НАРЯД_GEMINI.md")) { "нема $d"; return }
  Set-Location $d
  $br = "gemini/proba-$krok"
  git config --local --unset remote.origin.pushurl 2>$null
  # чекаємо, якщо в цій теці ще йде старий agy (11b)
  if ($krok -eq '11b') { Get-Process -Id 4652 -Name agy -ErrorAction SilentlyContinue | Wait-Process }   # старий прогін 11b, PID 4652 (якщо ще йде)
  git cat-file -e "HEAD:ЗВІТ_GEMINI.md" 2>$null
  if ($LASTEXITCODE -ne 0) {
    git stash push -u -m "перервано-до-повтору" 2>&1 | Out-Null   # незавершений стан зберігається в stash (не в гілці)
    $base = git rev-parse HEAD
    git config --local remote.origin.pushurl NE_PUSHYTY
    $t = Get-Date
    $prompt = "Прочитай НАРЯД_GEMINI.md у цій теці й виконай його до кінця. Працюй синхронно, без фонових завдань; не закінчуй хід, доки ЗВІТ_GEMINI.md не закомічено."
    & "$env:LOCALAPPDATA\agy\bin\agy.exe" -p $prompt --model $model --dangerously-skip-permissions --output-format json --print-timeout "$($godyn*60)s" > agy_вихід.json
    # якщо агент знову вийшов без звіту — до 2 разів продовжуємо ту саму розмову
    for ($i = 1; $i -le 2; $i++) {
      git cat-file -e "HEAD:ЗВІТ_GEMINI.md" 2>$null; if ($LASTEXITCODE -eq 0) { break }
      $id = try { (Get-Content agy_вихід.json -Raw | ConvertFrom-Json).conversation_id } catch { $null }; if (-not $id) { break }
      & "$env:LOCALAPPDATA\agy\bin\agy.exe" -p "Ти не закінчив: заверши наряд синхронно, без фонових завдань, напиши й закоміть ЗВІТ_GEMINI.md, виведи ГОТОВО з повним SHA." --conversation $id --model $model --dangerously-skip-permissions --output-format json --print-timeout 3600s > "agy_вихід_$i.json"
    }
    "RC=$LASTEXITCODE; хв=$([int]((Get-Date) - $t).TotalMinutes)" > agy_час.txt
    git config --local --unset remote.origin.pushurl
  } else { $base = (git rev-parse HEAD~1) }
  git add -A; git diff --cached --quiet; if ($LASTEXITCODE -ne 0) { git commit -q -m "Проба $krok`: незакомічене після прогону (водій)" }
  $gh = git diff --stat "$base..HEAD" -- .github/
  "=== $krok : diff .github/ відносно бази $base"; $gh
  if ($gh) { "!!! $krok : змінено .github/ — ПУШ НЕ ВИКОНАНО"; return }
  git push -u origin HEAD
  "=== $krok : " + (git ls-remote origin $br)
}
Vodij '13' 'gemini-3.8-flash-medium' 180
Vodij '25' 'gemini-4-argon-high' 180
Vodij '11b' 'gemini-4-argon-medium' 180
# проба 12 (вже готова): дифф без .github/, потім пуш
$d = "$env:USERPROFILE\proba-gemini\12"; Set-Location $d; git config --local --unset remote.origin.pushurl 2>$null
$gh = git diff --stat "HEAD~1..HEAD" -- .github/; if ($gh) { "!!! 12: змінено .github/ — ПУШ НЕ ВИКОНАНО"; $gh } else { git push -u origin HEAD; "=== 12 : " + (git ls-remote origin gemini/proba-12) }

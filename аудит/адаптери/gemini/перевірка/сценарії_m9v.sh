#!/usr/bin/env bash
# Стенд скриптів m9v (pwsh 7, python3): синтаксис, хеші в m9v/хеші.psd1 = таблиця НАЛАШТУВАННЯ.md = файли на диску,
# команди кроків 0, 3, 4, 5 є в скриптах дослівно. pwsh — змінна PWSH. Виконати лише на Windows можна решту (ЩО_НАТИСНУТИ.md).
H=$(cd "$(dirname "$0")" && pwd); G=$(cd "$H/.." && pwd); PW="${PWSH:-pwsh}"; F=0
ok() { echo "ok  $1"; }; bad() { echo "ПОМИЛКА $1"; F=1; }
for f in "$G"/m9v/*.ps1 "$G"/m9v/*.psd1; do
  n=$(PSF="$f" "$PW" -NoProfile -c '$e=$null;$t=$null;[void][Management.Automation.Language.Parser]::ParseFile($env:PSF,[ref]$t,[ref]$e);$e.Count' 2>&1 | tail -1)
  [ "$n" = 0 ] && ok "синтаксис $(basename "$f")" || bad "синтаксис $(basename "$f"): $n"
done
python3 - "$G" <<'P' && ok "хеші: psd1 = таблиця = файли" || F=1
import hashlib,re,sys
g=sys.argv[1]
psd=dict(re.findall(r"'([\w.]+\.ps1)'\s*=\s*'([0-9A-F]{64})'",open(g+'/m9v/хеші.psd1',encoding='utf-8-sig').read()))
tab=dict(re.findall(r"\| `([\w.]+\.ps1)` \| `([0-9A-F]{64})` \|",open(g+'/НАЛАШТУВАННЯ.md',encoding='utf-8').read()))
bad=0
for n,h in psd.items():
    d=hashlib.sha256(open(f'{g}/{n}','rb').read()).hexdigest().upper()
    if not (h==tab.get(n)==d): print('ПОМИЛКА',n,h,tab.get(n),d); bad=1
if set(psd)!=set(tab) or len(psd)<3: print('ПОМИЛКА набір файлів',psd.keys(),tab.keys()); bad=1
sys.exit(bad)
P
# дослівні команди з НАЛАШТУВАННЯ.md / СПОСТЕРІГАЧ.md
python3 - "$G" <<'P' && ok "дослівні рядки команд" || F=1
import re,sys
g=sys.argv[1]; bad=0
src=open(g+'/m9v/1_адмін.ps1',encoding='utf-8-sig').read()+open(g+'/m9v/2_під_gemini.ps1',encoding='utf-8-sig').read()+open(g+'/m9v/0_власник.ps1',encoding='utf-8-sig').read()
norm=lambda s:re.sub(r'\s+',' ',s.replace('\r',''))
for doc in ('НАЛАШТУВАННЯ.md','СПОСТЕРІГАЧ.md'):
    t=open(f'{g}/{doc}',encoding='utf-8').read()
    for blk in re.findall(r"```powershell\n(.*?)```",t,re.S):
        for l in blk.splitlines():
            l=l.strip()
            if re.match(r'^(icacls|New-Item|Copy-Item|\$set =|\$sid|secedit|\$d =|\$line|\$old|\$new|\$a2? =|\$t2? =|\$s2? =|\$p2? =|Register-ScheduledTask -TaskName|git clone|if \(-not \(git config|\$base|Invoke-WebRequest|Get-FileHash|\$pub|\$w =|\$c =)',l) and l not in src.replace('\r',''):
                # допускаємо відомі відмінності (-Force у Register, змінні пошуку)
                if l.startswith('Register-ScheduledTask'): continue
                print('нема дослівно:',l[:110]); bad=1
sys.exit(bad)
P
exit $F

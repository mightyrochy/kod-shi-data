#!/usr/bin/env bash
# Стенд скриптів m9v (pwsh 7, python3): синтаксис, хеші в m9v/хеші.psd1 = таблиця НАЛАШТУВАННЯ.md = файли на диску,
# команди кроків 0, 3, 4, 5 є в скриптах дослівно. pwsh — змінна PWSH. Виконати лише на Windows можна решту (ЩО_НАТИСНУТИ.md).
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"; G=$(cd "$H/.." && pwd); PW="${PWSH:-pwsh}"; F=0
ok() { echo "ok  $1"; }; bad() { echo "ПОМИЛКА $1"; F=1; }
for f in "$G"/m9v/*.ps1 "$G"/m9v/*.psd1; do
  n=$(PSF="$(wp "$f")" "$PW" -NoProfile -c '$e=$null;$t=$null;[void][Management.Automation.Language.Parser]::ParseFile($env:PSF,[ref]$t,[ref]$e);$e.Count' 2>&1 | tail -1)
  [ "$n" = 0 ] && ok "синтаксис $(basename "$f")" || bad "синтаксис $(basename "$f"): $n"
done
$PY "$(wp "$H/перевірити_хеші.py")" --диск && ok "хеші: psd1 = таблиця = файли" || F=1
# дослівні команди з НАЛАШТУВАННЯ.md / СПОСТЕРІГАЧ.md
$PY - "$G" <<'P' && ok "дослівні рядки команд" || F=1
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
# Codex під gemini (М.9-В PR-3, 9738/9741): інсталятор закріплено релізом і хешем; ключ -EnableCodex у 1_адмін.ps1; кроки власника
$PY - "$G" <<'P' && ok "Codex: закріплений інсталятор, ключ -EnableCodex, кроки власника" || F=1
import importlib.util,re,sys
from pathlib import Path
g=sys.argv[1]; bad=0
spec=importlib.util.spec_from_file_location('hash_check', Path(g)/'перевірка/перевірити_хеші.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
try: manifest=module.прочитати_маніфест(Path(g))
except Exception as e: print('ПОМИЛКА маніфест', e); sys.exit(1)
def rd(n): return open(f'{g}/{n}',encoding='utf-8-sig').read().replace('\r','')
tab,adm,sub,nat=rd('НАЛАШТУВАННЯ.md'),rd('m9v/1_адмін.ps1'),rd('m9v/2_під_gemini.ps1'),rd('m9v/ЩО_НАТИСНУТИ.md')
def chk(c,m):
    global bad
    if not c: print('ПОМИЛКА',m); bad=1
h=manifest.get("CodexInstaller"); v=manifest.get("CodexRelease")
h=isinstance(h,str) and re.fullmatch(r"[0-9A-F]{64}",h)
v=isinstance(v,str) and re.fullmatch(r"\d+\.\d+\.\d+",v)
chk(h and v,'хеші.psd1: CodexInstaller (64 hex верхнім регістром) і CodexRelease (x.y.z)')
if h and v:
    chk(re.search(r"\| `CodexInstaller`[^|]*\| `%s` \|"%h.group(0),tab),'таблиця «Хеші файлів» НАЛАШТУВАННЯ.md: рядок CodexInstaller = psd1')
chk("releases.openai.com/codex/releases/$rel/install.ps1" in sub,'2_під_gemini.ps1: інсталятор з URL релізу $rel')
chk('chatgpt.com/codex/install.ps1' not in re.sub(r'(?s)<#.*?#>','',sub),'2_під_gemini.ps1: рухомий URL лише в коментарі')
chk('-Release $rel' in sub and '$got -ne $want' in sub,'2_під_gemini.ps1: -Release $rel і звірка хешу')
chk('[switch]$EnableCodex' in adm and "$a.Arguments += ' -EnableCodex'" in adm,'1_адмін.ps1: ключ -EnableCodex дописує аргумент')
chk('1_адмін.ps1" -EnableCodex' in nat and '-WithCodex' in nat,'ЩО_НАТИСНУТИ.md: кроки 2 і 3 з -EnableCodex / -WithCodex')
chk('НЕ НАТИСКАТИ' not in nat,'ЩО_НАТИСНУТИ.md: розділ «НЕ НАТИСКАТИ» прибрано')
sys.exit(bad)
P
exit $F

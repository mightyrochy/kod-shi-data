#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [switch]$Before, [switch]$AccessBefore)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('end-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0; $lock = $null
function Check([string]$Name, [bool]$Ok) {
    <# Провал мірила визначає код завершення стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutboxDir "$tmp/out"
    $OutDir = "$tmp/gem-out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/seen", "$WorkDir/state", $OutboxDir, $OutDir, "$tmp/claude-run/slots", "$tmp/claude-run/state")) {
        [void][IO.Directory]::CreateDirectory($dir)
    }
    $script:Main = 'a' * 40; $script:Pulls = @(); $script:Markers = @(); $script:Logs = @()
    function Get-RefSha { <# Повертає сталий main синтетичного стенда. #> $script:Main }
    function Invoke-Git {
        <# Відтворює лише потрібні відповіді Git без зовнішніх процесів. #>
        param([string[]]$GitArgs, [switch]$AllowFail)
        $out = ''
        if ($GitArgs[0] -ceq 'cat-file' -and $GitArgs[-1] -like '*ланцюг.json') {
            $out = '{"v":1,"codex":"gpt-review","agy":"gemini-review","claude":"cc-claude-review"}'
        }
        [pscustomobject]@{Code=0;Out=$out;Err=''}
    }
    function Complete-EngineDrafts { <# Виключає створення зовнішніх PR зі стенда. #> }
    function Get-ChainPulls { <# Дає поточний знімок синтетичних PR. #> $script:Pulls }
    function Invoke-ChainApi([string]$Path) {
        <# Дає свіжу дату синтетичної голови для початкового знімка. #>
        [pscustomobject]@{sha=($Path -split '/')[-1];commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddMinutes(-1).ToString('o')}}}
    }
    function Test-LiveModels { <# Лишає GPU-прогони поза пробою автоперевірки. #> $false }
    function Test-ChainCodePull { <# Позначає синтетичні PR як зміни коду. #> $true }
    function Test-ReviewedMerge { <# Виключає окремий випадок чистого злиття main. #> $false }
    function Get-ReviewDiff { <# Повертає сталий diff для синтетичних голів. #> 'стенд-diff' }
    function Add-ChainMarker($Slug, $Model, $Main, [switch]$Gpu) { <# Рахує позначки без зовнішнього push. #> $script:Markers += [string]$Slug }
    function Write-WrapperLog([string]$Text) { <# Зберігає журнал і показує несподівані збої. #> $script:Logs += $Text; if ($Text -like "*CHAIN_*") { Write-Host $Text } }
    function Pull([int]$N, [string]$Branch, [string]$Head) {
        <# Довірений PR-чернетка з трьома послідовними головами. #>
        [pscustomobject]@{number=$N;title='Код';draft=$true;created_at=[datetimeoffset]::UtcNow.ToString('o');user=@{login='mightyrochy'};
            head=@{ref=$Branch;sha=$Head;repo=@{full_name=$GitHubRepo}};base=@{ref='main';repo=@{full_name=$GitHubRepo}}}
    }
    function Tick([string]$Head, [string]$Branch='claude/5.3-повний-обхід') {
        <# Один справжній прохід ланцюга з незмінним хмарним PR поруч. #>
        $script:Pulls = @((Pull 2386 $Branch $Head), (Pull 2400 'codex/хмара' ('e' * 40)))
        Invoke-WrapperChain
    }
    function CountReviews([string]$N) { <# Рахує всі перевірки одного PR. #> @($script:Markers | Where-Object { $_ -like "автоперевірка-$N-*" }).Count }
    $slug = '5.3-повний-обхід-каталогу'
    $marker = "gemini-queue/$slug/cc-claude-sonnet-5-5-medium/8/p1"
    $info = "$tmp/claude-run/slots/claude-1.json"
    Write-FileAtomic $info ((@{slug=$slug;marker=$marker}) | ConvertTo-Json -Compress)
    Write-FileAtomic ("$tmp/claude-run/state/branch-" + (Get-Sha256Hex $slug) + '.txt') 'claude/5.3-повний-обхід'
    $lock = [IO.File]::Open("$tmp/claude-run/slots/claude-1.lock", 'OpenOrCreate', 'ReadWrite', 'None')
    foreach ($head in @(('b'*40), ('c'*40), ('d'*40))) { Tick $head }
    $state = ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/chain.json"))
    Check 'активна голова лишається придатною в heads' ($state.heads.'2386'.sha -ceq ('d'*40) -and $state.heads.'2386'.eligible)
    Check "проміжних позначок: $(CountReviews 2386)" ((CountReviews 2386) -eq $(if ($Before) { 3 } else { 0 }))
    Check 'хмарний PR без смуги: рівно 1' ((CountReviews 2400) -eq 1)
    # Complete-Task записує кінець до звільнення слота; SHA3 вже є головою PR.
    Write-FileAtomic "$WorkDir/state/done.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО claude/5.3-повний-обхід $('d'*40) МОДЕЛЬ cc-claude-sonnet-5-5-medium"}) | ConvertTo-Json)
    $lock.Dispose(); $lock = $null
    Tick ('d'*40); Tick ('d'*40)
    Check "три голови й ГОТОВО: перевірок $(CountReviews 2386) (ДО 3 → ПІСЛЯ 1)" ((CountReviews 2386) -eq $(if ($Before) { 3 } else { 1 }))
    Check 'перевірка кінцевої SHA3' (@($script:Markers | Where-Object { $_ -ceq "автоперевірка-2386-$('d'*40)" }).Count -eq 1)
    Check 'PR без смуги: ДО 1 → ПІСЛЯ 1' ((CountReviews 2400) -eq 1)
    if (-not $Before) {
        Check 'пропуск і хмарний шлях видимі в журналі' (@($script:Logs | Where-Object { $_ -like '*смуга ще пише*' }).Count -eq 3 -and
            @($script:Logs | Where-Object { $_ -like '*#2400*активної смуги нема*' }).Count -gt 0)
        Check 'старий JSON слота з вільним замком не блокує' (-not (Get-ChainBranchWork 'claude/5.3-повний-обхід'))
        $lock = [IO.File]::Open("$tmp/claude-run/slots/claude-1.lock", 'Open', 'ReadWrite', 'None')
        # Перша спроба ще не має branch-<hash>: гілка вже видима в HEAD її робочої копії.
        $copy = "$tmp/claude-copy"; [void][IO.Directory]::CreateDirectory("$copy/repo/.git")
        Write-FileAtomic "$copy/repo/.git/HEAD" 'ref: refs/heads/claude/нова-гілка'
        Write-FileAtomic $info ((@{slug=$slug;marker=$marker;copy=$copy}) | ConvertTo-Json -Compress)
        Check 'HEAD копії першої спроби повʼязує іншу гілку' ((Get-ChainBranchWork 'claude/нова-гілка') -ceq $marker)
        # Worktree має .git-файл з gitdir, а не теку.
        Move-Item -LiteralPath "$copy/repo/.git" -Destination "$copy/meta"
        Write-FileAtomic "$copy/repo/.git" 'gitdir: ../meta'
        Check 'HEAD worktree читається через gitdir' ((Get-ChainBranchWork 'claude/нова-гілка') -ceq $marker)
        $lock.Dispose(); $lock = $null
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'gemini_run.ps1'), [ref]$tokens, [ref]$errors)
        $heartbeat = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Write-Heartbeat' }, $true)
        Invoke-Expression $heartbeat.Extent.Text
        function Get-UtcStamp($Date) { <# Форматує час справжнього Write-Heartbeat. #> $Date.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
        [void][IO.Directory]::CreateDirectory("$GeminiRunsDir/slots")
        foreach ($lane in @('codex','agy')) {
            $gm = "gemini-queue/спільний-$lane/gpt-test/2/p1"
            $head = $(if ($lane -ceq 'codex') { 'f'*40 } else { '1'*40 })
            Write-FileAtomic "$GeminiRunsDir/slots/$lane-1.json" ((@{slot="$lane-1";lane=$lane;slug="спільний-$lane";marker=$gm}) | ConvertTo-Json)
            $lock = [IO.File]::Open("$GeminiRunsDir/slots/$lane-1.lock", 'OpenOrCreate', 'ReadWrite', 'None')
            Write-Heartbeat 'TEST_ISOLATION'
            $hb = ConvertFrom-Json ([IO.File]::ReadAllText("$OutDir/heartbeat.json"))
            Check "${lane}: heartbeat ізоляції не має lanes" ($null -eq $hb.PSObject.Properties['lanes'])
            Check "${lane}: зайнятий слот повʼязує гілку без heartbeat.lanes" ((Get-ChainBranchWork "gemini/спільний-$lane") -ceq $gm)
            $n = CountReviews 2386
            Tick $head "gemini/спільний-$lane"
            Check "${lane}: активна голова — 0 перевірок" ((CountReviews 2386) -eq $n)
            Write-FileAtomic "$OutDir/heartbeat.json" ((@{lanes=@(@{lane=$lane;busy=@(@{marker=$gm})})}) | ConvertTo-Json -Depth 6)
            Write-FileAtomic "$WorkDir/state/done-$lane.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/спільний-$lane $head МОДЕЛЬ gpt-test"}) | ConvertTo-Json)
            $lock.Dispose(); $lock = $null
            Check "${lane}: старий busy з вільним замком не блокує" (-not (Get-ChainBranchWork "gemini/спільний-$lane"))
            Tick $head "gemini/спільний-$lane"; Tick $head "gemini/спільний-$lane"
            Check "${lane}: після ГОТОВО зі старим busy — 1 перевірка" ((CountReviews 2386) -eq ($n+1))
            $blockedHead = $(if ($lane -ceq 'codex') { '2'*40 } else { '3'*40 })
            $lock = [IO.File]::Open("$GeminiRunsDir/slots/$lane-1.lock", 'Open', 'ReadWrite', 'None')
            Tick $blockedHead "gemini/спільний-$lane"
            Check "${lane}: наступна активна голова — 0 перевірок" ((CountReviews 2386) -eq ($n+1))
            Write-FileAtomic "$WorkDir/state/blocked-$lane.json" ((@{line="GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/спільний-$lane BLOCKED"}) | ConvertTo-Json)
            $lock.Dispose(); $lock = $null
            Tick $blockedHead "gemini/спільний-$lane"; Tick $blockedHead "gemini/спільний-$lane"
            Check "${lane}: після ЗАБЛОКОВАНО — 1 перевірка" ((CountReviews 2386) -eq ($n+2))
        }
        if ($env:OS -eq 'Windows_NT' -and -not ('ChainFixtureToken' -as [type])) {
            # Обмежується лише токен потоку фікстури; вихідний токен та ACL робочих тек не змінюються.
            # https://learn.microsoft.com/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken
            Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32.SafeHandles;
public sealed class ChainFixtureToken {
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern bool CreateRestrictedToken(IntPtr token, uint flags, uint ns, IntPtr s, uint np, IntPtr p, uint nr, IntPtr r, out IntPtr result);
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr data, int length, out int needed);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool LookupPrivilegeName(string system, IntPtr luid, StringBuilder name, ref int length);
    public static object Run(Func<object> body) {
        IntPtr token;
        using (var identity = WindowsIdentity.GetCurrent()) {
            if (!CreateRestrictedToken(identity.Token, 1, 0, IntPtr.Zero, 0, IntPtr.Zero, 0, IntPtr.Zero, out token))
                throw new Win32Exception(Marshal.GetLastWin32Error());
        }
        using (var handle = new SafeAccessTokenHandle(token)) {
            return WindowsIdentity.RunImpersonated(handle, body);
        }
    }
    public static string Describe() {
        using (var identity = WindowsIdentity.GetCurrent()) {
            int needed;
            GetTokenInformation(identity.Token, 3, IntPtr.Zero, 0, out needed);
            IntPtr data = Marshal.AllocHGlobal(needed);
            try {
                if (!GetTokenInformation(identity.Token, 3, data, needed, out needed)) throw new Win32Exception(Marshal.GetLastWin32Error());
                var result = new StringBuilder("sid=" + identity.User + "; impersonation=" + identity.ImpersonationLevel);
                for (int i = 0; i < Marshal.ReadInt32(data); i++) {
                    IntPtr entry = IntPtr.Add(data, 4 + i * 12);
                    int size = 256;
                    var name = new StringBuilder(size);
                    if (!LookupPrivilegeName(null, entry, name, ref size)) throw new Win32Exception(Marshal.GetLastWin32Error());
                    result.Append("; " + name + "=0x" + Marshal.ReadInt32(entry, 8).ToString("x"));
                }
                Marshal.FreeHGlobal(data); data = Marshal.AllocHGlobal(4);
                foreach (int kind in new int[] { 18, 20 }) {
                    if (!GetTokenInformation(identity.Token, kind, data, 4, out needed)) throw new Win32Exception(Marshal.GetLastWin32Error());
                    result.Append("; " + (kind == 18 ? "elevationType=" : "elevated=") + Marshal.ReadInt32(data));
                }
                GetTokenInformation(identity.Token, 10, IntPtr.Zero, 0, out needed);
                Marshal.FreeHGlobal(data); data = Marshal.AllocHGlobal(needed);
                if (!GetTokenInformation(identity.Token, 10, data, needed, out needed)) throw new Win32Exception(Marshal.GetLastWin32Error());
                result.Append("; tokenId=" + Marshal.ReadInt64(data).ToString("x"));
                return result.ToString();
            } finally { Marshal.FreeHGlobal(data); }
        }
    }

}
'@
        }
        function Show-DirectoryAccess([string]$Path, [string]$Phase) {
            <# Друкує фактичний результат читача на ноутбуці й CI, включно з винятком та ефективним токеном. #>
            Write-Host "ACL ДІАГНОСТИКА $Phase $Path"
            Write-Host ("ACL ТОКЕН " + [ChainFixtureToken]::Describe())
            try {
                $items = @(Get-ChildItem -LiteralPath $Path -ErrorAction Stop)
                Write-Host "ACL ЧИТАННЯ Get-ChildItem: успіх, елементів $($items.Count)"
            } catch { Write-Host "ACL ЧИТАННЯ Get-ChildItem: $($_.Exception.GetBaseException().GetType().FullName), HResult=$($_.Exception.GetBaseException().HResult): $($_.Exception.Message)" }
            try {
                $items = [IO.Directory]::GetFiles($Path, '*.json')
                Write-Host "ACL ЧИТАННЯ Directory.GetFiles: успіх, файлів $($items.Count)"
            } catch { Write-Host "ACL ЧИТАННЯ Directory.GetFiles: $($_.Exception.GetBaseException().GetType().FullName), HResult=$($_.Exception.GetBaseException().HResult): $($_.Exception.Message)" }
        }

        function With-DeniedRead([string]$Path, [scriptblock]$Body, [string]$Rights='ReadData', [switch]$DirectoryOnly) {
            <# Тимчасово забороняє читання лише власної фікстури; відновлює ACL/режим у finally. #>
            function Read-FixtureAcl([string]$Entry) {
                <# Бере лише DACL; SACL та власника фікстура не змінює. #>
                if ([IO.Directory]::Exists($Entry)) { [IO.Directory]::GetAccessControl($Entry, 'Access') }
                else { [IO.File]::GetAccessControl($Entry, 'Access') }
            }
            function Write-FixtureAcl([string]$Entry, $Acl) {
                <# Відновлює DACL через WRITE_DAC, навіть коли READ_CONTROL заборонено. #>
                $isDirectoryAcl = $Acl -is [Security.AccessControl.DirectorySecurity]
                $copy = $(if ($isDirectoryAcl) { New-Object Security.AccessControl.DirectorySecurity } else { New-Object Security.AccessControl.FileSecurity })
                # SetAccessControl пише лише змінені секції: позначаємо DACL навіть у знімку.
                $copy.SetSecurityDescriptorSddlForm($Acl.GetSecurityDescriptorSddlForm('Access'), 'Access')
                if ($isDirectoryAcl) { [IO.Directory]::SetAccessControl($Entry, $copy) }
                else { [IO.File]::SetAccessControl($Entry, $copy) }
            }
            $full = [IO.Path]::GetFullPath($Path)
            if (-not $full.StartsWith(([IO.Path]::GetFullPath($tmp) + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) { throw 'ACL поза текою стенда' }
            if ($env:OS -eq 'Windows_NT') {
                $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
                $isDirectory = [IO.Directory]::Exists($full)
                # Явні дозволи дочірнього об'єкта можуть випереджати успадкований deny.
                # Ставимо явний deny на всю власну фікстуру й відновлюємо кожний ACL.
                $paths = @($full)
                if ($isDirectory -and -not $DirectoryOnly) { $paths += @(Get-ChildItem -LiteralPath $full -Recurse -Force | ForEach-Object { $_.FullName }) }
                $savedAcls = @()
                $changedAcls = @()
                try {
                    foreach ($entry in $paths) {
                        $acl = Read-FixtureAcl $entry
                        $savedAcls += @{path=$entry;acl=$acl}
                        $changed = Read-FixtureAcl $entry
                        $inherit = $(if ([IO.Directory]::Exists($entry) -and -not $DirectoryOnly) { 'ContainerInherit,ObjectInherit' } else { 'None' })
                        $rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, $Rights, $inherit, 'None', 'Deny')
                        $changed.AddAccessRule($rule)
                        $changedAcls += @{path=$entry;acl=$changed}
                    }
                    [array]::Reverse($changedAcls)
                    foreach ($entry in $changedAcls) { Write-FixtureAcl $entry.path $entry.acl }
                    if ($isDirectory) { Show-DirectoryAccess $full "вихідний токен, deny $Rights" }
                    $script:FixtureReaders = @{}; $script:TokenMismatches = 0
                    [ChainFixtureToken]::Run([Func[object]]{
                        $script:FixtureToken = [ChainFixtureToken]::Describe()
                        Check 'токен фікстури: привілеїв backup/restore немає' ($script:FixtureToken -notmatch 'SeBackupPrivilege|SeRestorePrivilege')
                        if ($isDirectory) { Show-DirectoryAccess $full "токен фікстури, deny $Rights" }
                        & $Body
                    })
                    Check 'читачі виконані під тим самим токеном, що й передумова' ($script:FixtureReaders.Count -gt 0 -and $script:TokenMismatches -eq 0)
                } finally {
                    $script:FixtureToken = $null
                    foreach ($entry in $savedAcls) { Write-FixtureAcl $entry.path $entry.acl }
                }
            } else {
                $mode = & stat -c '%a' -- $full
                if ($LASTEXITCODE) { throw 'stat фікстури' }
                try {
                    & chmod $(if ($DirectoryOnly) { '100' } else { '000' }) -- $full
                    if ($LASTEXITCODE) { throw 'chmod фікстури' }
                    & $Body
                } finally { & chmod $mode -- $full }
            }
        }
        function Assert-FixtureToken([string]$Reader) {
            <# Звіряє ефективний токен саме перед справжнім читанням, а не лише в передумові. #>
            if ($script:FixtureToken) {
                $actual = [ChainFixtureToken]::Describe()
                if ($actual -cne $script:FixtureToken) { $script:TokenMismatches++; throw "ACL TOKEN_MISMATCH ${Reader}: $actual" }
                if (-not $script:FixtureReaders.ContainsKey($Reader)) { Write-Host "ACL ЧИТАЧ $Reader $actual" }
                $script:FixtureReaders[$Reader] = $true
            }
        }
        foreach ($name in @('Get-ChainBusySlots', 'Get-ChainBranchWork', 'Read-ChainOptionalFile')) {
            $definition = (Get-Command $name).Definition.Replace("`r`n", "`n")
            $definition = [regex]::Replace($definition, '(?m)^([^\r\n]*(?:\[IO\.(?:File|Directory)\]::(?:GetFiles|GetAttributes|ReadAllText|Open))[^\r\n]*)$', {
                param($match)
                "Assert-FixtureToken '$name'`n" + $match.Value
            })
            Set-Item -LiteralPath "Function:$name" -Value ([scriptblock]::Create($definition))
        }
        # Кожна недоступна ділянка перевіряється справжнім ACL/chmod, без підміни читача.
        $claudeSlots = "$tmp/claude-run/slots"
        $saved = "$tmp/claude-run/state/branch-$(Get-Sha256Hex $slug).txt"
        $copy = "$tmp/access-copy"
        [void][IO.Directory]::CreateDirectory("$copy/repo/.git")
        Write-FileAtomic "$copy/repo/.git/HEAD" 'ref: refs/heads/claude/доступ'
        Write-FileAtomic $saved 'claude/доступ'
        Write-FileAtomic $info ((@{slug=$slug;marker=$marker;copy=$copy}) | ConvertTo-Json -Compress)
        $claudeLock = [IO.File]::Open("$claudeSlots/claude-1.lock", 'Open', 'ReadWrite', 'None')
        $held = @($claudeLock)
        try {
            foreach ($lane in @('codex','agy')) {
                Write-FileAtomic "$GeminiRunsDir/slots/$lane-1.json" ((@{slug="доступ-$lane";marker="gemini-queue/доступ-$lane/gpt-test/1/p1"}) | ConvertTo-Json)
                $held += [IO.File]::Open("$GeminiRunsDir/slots/$lane-1.lock", 'Open', 'ReadWrite', 'None')
            }
            $case = 0
            foreach ($path in @($claudeSlots, $info, $saved, "$copy/repo/.git", "$copy/repo/.git/HEAD")) {
                $case++
                With-DeniedRead $path {
                    # Передумова: користувач справді не може читати фікстуру.
                    $denied = $false
                    try {
                        if ([IO.Directory]::Exists($path)) { $null = Get-ChildItem -LiteralPath $path -ErrorAction Stop }
                        else { $null = [IO.File]::ReadAllText($path) }
                    } catch [UnauthorizedAccessException] { $denied = $true }
                    Check "ACL ${case}: читання справді заборонено" $denied
                    $n = CountReviews 2386; $logStart = $script:Logs.Count
                    $script:Pulls = @((Pull 2386 'claude/доступ' ($case.ToString('x') + ('a'*39))),
                        (Pull 2501 'gemini/доступ-codex' ('8'*40)), (Pull 2502 'gemini/доступ-agy' ('9'*40)))
                    Invoke-WrapperChain
                    $addedLogs = @($script:Logs | Select-Object -Skip $logStart)
                    $failed = @($addedLogs | Where-Object { $_ -like '*CHAIN_FAILED*' }).Count -gt 0
                    Check "ACL ${case}: падінь ланцюга $(if ($failed) { 1 } else { 0 }) (ДО 1 → ПІСЛЯ 0)" ($failed -eq [bool]$AccessBefore)
                    if (-not $AccessBefore) {
                        Check "ACL ${case}: журнал називає недоступну смугу" (@($addedLogs | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
                        Check "ACL ${case}: голова Claude перевіряється як звичайно" ((CountReviews 2386) -eq ($n+1))
                        Check "ACL ${case}: Codex і agy далі відкладають активні голови" ((CountReviews 2501) -eq 0 -and (CountReviews 2502) -eq 0 -and
                            @($addedLogs | Where-Object { $_ -like '*смуга ще пише*' }).Count -eq 2)
                    }
                }
            }
            With-DeniedRead "$copy/repo/.git" {
                $denied = $false
                try { $null = [IO.Directory]::GetFiles("$copy/repo/.git", 'HEAD') }
                catch { $denied = $_.Exception.GetBaseException() -is [UnauthorizedAccessException] }
                Check '.git без ListDirectory: перелік справді заборонено' $denied
                Check '.git без ListDirectory: HEAD окремо читається' ([IO.File]::ReadAllText("$copy/repo/.git/HEAD") -cmatch 'refs/heads/claude/доступ')
                $logStart = $script:Logs.Count
                Check '.git без ListDirectory: недоступна тека дає звичайну перевірку' (-not (Get-ChainBranchWork 'claude/доступ'))
                Check '.git без ListDirectory: причина у журналі' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
            } -DirectoryOnly
            # Недоступний lock перевіряється без чужого відкритого handle: це ACL, не sharing violation.
            $claudeLock.Dispose()
            With-DeniedRead "$claudeSlots/claude-1.lock" {
                if ($AccessBefore) {
                    $threw = $false
                    try { $null = Get-ChainBranchWork 'claude/доступ' } catch { $threw = $true }
                    Check 'ACL замка ДО: виняток виривається з читача' $threw
                } else {
                    $logStart = $script:Logs.Count
                    Check 'ACL замка: відмова доступу не означає зайнятість' (-not (Get-ChainBranchWork 'claude/доступ'))
                    Check 'ACL замка: виняток записаний у журнал' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
                }
            }
            # .git-файл worktree читається окремо від HEAD.
            Move-Item -LiteralPath "$copy/repo/.git" -Destination "$copy/meta"
            Write-FileAtomic "$copy/repo/.git" 'gitdir: ../meta'
            $claudeLock = [IO.File]::Open("$claudeSlots/claude-1.lock", 'Open', 'ReadWrite', 'None')
            $held += $claudeLock
            With-DeniedRead "$copy/repo/.git" {
                $logStart = $script:Logs.Count; $threw = $false; $work = ''
                try { $work = Get-ChainBranchWork 'claude/доступ' } catch { $threw = $true }
                Check 'ACL .git-файла: локальна обробка (ДО виняток → ПІСЛЯ журнал)' ($threw -eq [bool]$AccessBefore)
                if (-not $AccessBefore) {
                    Check 'ACL .git-файла: звичайний шлях і журнал' (-not $work -and @($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
                }
            }
            With-DeniedRead "$copy/meta" {
                $denied = $false
                try { $null = [IO.Directory]::GetFiles("$copy/meta", 'HEAD') }
                catch { $denied = $_.Exception.GetBaseException() -is [UnauthorizedAccessException] }
                Check 'gitdir без ListDirectory: перелік справді заборонено' $denied
                Check 'gitdir без ListDirectory: HEAD окремо читається' ([IO.File]::ReadAllText("$copy/meta/HEAD") -cmatch 'refs/heads/claude/доступ')
                $logStart = $script:Logs.Count
                Check 'gitdir без ListDirectory: звичайна перевірка' (-not (Get-ChainBranchWork 'claude/доступ'))
                Check 'gitdir без ListDirectory: причина у журналі' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
            } -DirectoryOnly
            # Відмова читання Codex не скасовує активність agy у спільній теці slots.
            if (-not $AccessBefore) {
                With-DeniedRead "$GeminiRunsDir/slots/codex-1.json" {
                    $logStart = $script:Logs.Count
                    Check 'ACL Codex: agy читається незалежно' ((Get-ChainBranchWork 'gemini/доступ-agy') -ceq 'gemini-queue/доступ-agy/gpt-test/1/p1')
                    Check 'ACL Codex: смуга названа в журналі' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги codex недоступний:*' }).Count -eq 1)
                }
                # Пошкоджений JSON також не має перетворюватись на активність.
                Write-FileAtomic $info '{'
                $logStart = $script:Logs.Count
                Check 'пошкоджений JSON: звичайний шлях' (-not (Get-ChainBranchWork 'claude/доступ'))
                Check 'пошкоджений JSON: причина у журналі' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
            }
        } finally { foreach ($handle in $held) { $handle.Dispose() } }

        # Контрольоване зникнення після справжнього переліку вправляє саме читач,
        # а не дублює його логіку у заглушці.
        $raceInfo = "$GeminiRunsDir/slots/codex-1.json"
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'wrapper_chain.ps1'), [ref]$tokens, [ref]$errors)
        $reader = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Get-ChainBusySlots' }, $true).Extent.Text
        $anchor = "$" + "lockPath = [IO.Path]::ChangeExtension($" + "file.FullName, '.lock')"
        if (-not $reader.Contains($anchor)) { throw 'Змінено межу відкриття замка' }
        Write-FileAtomic $raceInfo '{"slug":"гонка","marker":"gemini-queue/гонка/gpt-test/1/p1"}'
        $raceLock = [IO.File]::Open("$GeminiRunsDir/slots/codex-1.lock", 'Open', 'ReadWrite', 'None')
        $probe = $reader.Replace('function Get-ChainBusySlots(', 'function Test-GoneJson(').Replace($anchor, ($anchor + '; [IO.File]::Delete($file.FullName)'))
        Invoke-Expression $probe
        try {
            $threw = $false
            try { $null = @(Test-GoneJson $GeminiRunsDir '^codex-[1-9][0-9]*$') } catch { $threw = $true }
            Check '11566а: зниклий JSON (ДО виняток → ПІСЛЯ вільний слот)' ($threw -eq [bool]$AccessBefore)
        } finally { $raceLock.Dispose() }

        function Read-Case([scriptblock]$Read) {
            <# Фіксує виняток старого читача без зупинки решти вимірів ДО. #>
            try { & $Read } catch { Write-Host "ВИНЯТОК ЧИТАЧА: $($_.Exception.Message)" }
        }
        # Раніше один недоступний JSON/HEAD скасовував усі слоти смуги.
        if (-not $AccessBefore) {
            $previousRuns = $GeminiRunsDir; $previousWork = $WorkDir
            $handles = @()
            try {
                $GeminiRunsDir = "$tmp/multiple/gemini-runs"
                $WorkDir = "$tmp/multiple/pub"
                [void][IO.Directory]::CreateDirectory("$GeminiRunsDir/slots")
                [void][IO.Directory]::CreateDirectory("$tmp/multiple/claude-run/slots")
                foreach ($i in @(1,2,3)) {
                    Write-FileAtomic "$GeminiRunsDir/slots/codex-$i.json" ((@{slug="відомий-$i";marker="gemini-queue/відомий-$i/gpt-test/1/p1"}) | ConvertTo-Json)
                    $handles += [IO.File]::Open("$GeminiRunsDir/slots/codex-$i.lock", 'OpenOrCreate', 'ReadWrite', 'None')
                }
                Write-FileAtomic "$GeminiRunsDir/slots/codex-2.json" '{'
                $logStart = $script:Logs.Count
                $known = @(Read-Case { Get-ChainBusySlots $GeminiRunsDir '^codex-[1-9][0-9]*$' 'codex' })
                Check 'кілька JSON: збережено обидва справні слоти' ($known.Count -eq 2)
                Check 'кілька JSON: зіпсований слот журналюється' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги codex недоступний:*' }).Count -eq 1)
                Check 'кілька JSON: активна гілка не йде на перевірку' ((Get-ChainBranchWork 'gemini/відомий-3') -ceq 'gemini-queue/відомий-3/gpt-test/1/p1')
                foreach ($i in @(1,2)) {
                    $copy = "$tmp/multiple/copy-$i"
                    [void][IO.Directory]::CreateDirectory("$copy/repo/.git")
                    Write-FileAtomic "$copy/repo/.git/HEAD" "ref: refs/heads/claude/відома-$i"
                    Write-FileAtomic "$tmp/multiple/claude-run/slots/claude-$i.json" ((@{slug="слот-$i";marker="gemini-queue/слот-$i/cc-test/1/p1";copy=$copy}) | ConvertTo-Json)
                    $handles += [IO.File]::Open("$tmp/multiple/claude-run/slots/claude-$i.lock", 'OpenOrCreate', 'ReadWrite', 'None')
                }
                With-DeniedRead "$tmp/multiple/copy-1/repo/.git/HEAD" {
                    # Порядок файлової системи не є контрактом: впорядковуємо лише вихід
                    # справжнього читача, щоб недоступний HEAD гарантовано був першим.
                    $actualSlots = ${function:Get-ChainBusySlots}
                    function Get-ChainBusySlots($Dir, $Pattern, $Lane) {
                        <# Фіксує порядок реальних слотів для відтворення помилки другого читання. #>
                        & $actualSlots $Dir $Pattern $Lane | Sort-Object { [string]$_.slug }
                    }
                    $logStart = $script:Logs.Count
                    $found = Get-ChainBranchWork 'claude/відома-2'
                    Check 'кілька HEAD: справний слот після недоступного збережено' ($found -ceq 'gemini-queue/слот-2/cc-test/1/p1')
                    Check 'кілька HEAD: виняток першого слота у журналі' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
                }
                if ($env:OS -eq 'Windows_NT') {
                    # Явний дозвіл на slots не має зробити фікстуру залежною від успадкування.
                    $acl = Get-Acl -LiteralPath "$tmp/multiple/claude-run/slots"
                    $acl.SetAccessRuleProtection($true, $true)
                    Set-Acl -LiteralPath "$tmp/multiple/claude-run/slots" -AclObject $acl
                }
                With-DeniedRead "$tmp/multiple/claude-run" {
                    if ($env:OS -eq 'Windows_NT') { Show-DirectoryAccess "$tmp/multiple/claude-run/slots" 'дочірня тека, той самий токен читача' }
                    $denied = $false
                    try { $null = [IO.Directory]::GetFiles("$tmp/multiple/claude-run/slots", '*.json') }
                    catch { $denied = $_.Exception.GetBaseException() -is [UnauthorizedAccessException] }
                    Check 'батьківська тека: читання slots справді заборонено' $denied
                    $logStart = $script:Logs.Count
                    Check 'батьківська тека: звичайна перевірка без падіння' (-not (Get-ChainBranchWork 'claude/відома-2'))
                    Check 'батьківська тека: недоступність не прихована як відсутність' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги claude недоступний:*' }).Count -eq 1)
                } 'ReadAndExecute'
            } finally {
                foreach ($handle in $handles) { $handle.Dispose() }
                $GeminiRunsDir = $previousRuns; $WorkDir = $previousWork
            }

            # Клон AST підміняє лише результат системного Open; обробник помилок — справжній.
            $open = '$lock = [IO.File]::Open($lockPath, ''Open'', ''ReadWrite'', ''None'')'
            if (-not $reader.Contains($open)) { throw 'Змінено операцію відкриття замка' }
            $ioDir = "$tmp/io-case"
            [void][IO.Directory]::CreateDirectory("$ioDir/slots")
            Write-FileAtomic "$ioDir/slots/codex-1.json" '{"slug":"io","marker":"gemini-queue/io/gpt-test/1/p1"}'
            $probe = $reader.Replace('function Get-ChainBusySlots(', 'function Test-OtherIo(').Replace($open, 'throw (New-Object IO.IOException(''стенд: IO не 32''))')
            Invoke-Expression $probe
            $logStart = $script:Logs.Count
            Check 'IOException не 32: не означає зайнятість' (@(Read-Case { Test-OtherIo $ioDir '^codex-[1-9][0-9]*$' 'codex' }).Count -eq 0)
            Check 'IOException не 32: є причина у журналі' (@($script:Logs | Select-Object -Skip $logStart | Where-Object { $_ -like 'стан смуги codex недоступний:*IO*стенд: IO не 32*' }).Count -eq 1)
            $probe = $reader.Replace('function Get-ChainBusySlots(', 'function Test-GoneLockParent(').Replace($open, ('[IO.Directory]::Move($Dir, ($Dir + ''-moved'')); ' + $open))
            Invoke-Expression $probe
            $logStart = $script:Logs.Count
            Check 'PathNotFound замка: зникла тека не означає зайнятість' (@(Test-GoneLockParent $ioDir '^codex-[1-9][0-9]*$' 'codex').Count -eq 0)
            Check 'PathNotFound замка: зникнення без журналу недоступності' ($script:Logs.Count -eq $logStart -and [IO.Directory]::Exists("$ioDir-moved"))
        }

        # 11566б: відтворюємо точне вікно між Open і Dispose, вставляючи виклик
        # справжнього Open-Lock worker у копію AST-функції; робочий читач не підміняється.
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'wrapper_chain.ps1'), [ref]$tokens, [ref]$errors)
        $probe = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Get-ChainBusySlots' }, $true).Extent.Text
        $probe = $probe.Replace('function Get-ChainBusySlots(', 'function Test-ProbeRace(')
        $anchor = '$lock.Dispose(); continue'
        if (-not $probe.Contains($anchor)) { throw 'Змінено вікно проби замка' }
        $probe = $probe.Replace($anchor, 'try { $script:ProbeBusy = ($null -eq (Open-Lock $lockPath)) } finally { $lock.Dispose() }; continue')
        $queueAst = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'queue_lanes.ps1'), [ref]$tokens, [ref]$errors)
        Invoke-Expression ($queueAst.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Open-Lock' }, $true).Extent.Text)
        Invoke-Expression $probe
        Write-FileAtomic $raceInfo '{"slug":"гонка","marker":"gemini-queue/гонка/gpt-test/1/p1"}'
        $script:ProbeBusy = $false
        $null = @(Test-ProbeRace $GeminiRunsDir '^codex-[1-9][0-9]*$')
        Check '11566б: одночасний Open-Lock worker бачить зайнятий слот — гіпотезу доведено' $script:ProbeBusy
        $workerLock = Open-Lock "$GeminiRunsDir/slots/codex-1.lock"
        Check '11566б: після проби worker знову може взяти слот' ($null -ne $workerLock)
        if ($null -ne $workerLock) { $workerLock.Dispose() }

    }
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
    if (-not ([IO.Path]::GetFullPath($tmp)).StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase)) { throw 'Тека стенда поза TEMP' }
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
if ($bad) { "ПІДСУМОК: ✗ $bad"; exit 1 }
exit 0

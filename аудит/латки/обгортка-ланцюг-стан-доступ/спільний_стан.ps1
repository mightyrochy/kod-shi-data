function Initialize-SharedMarkerState {
    <# Переносить стан у наявну теку обміну під замком планувальника, дочекавшись старих процесів.

    Переписування байтів створює файли з ACL теки обміну; Copy/Move перенесли б приватну ACL.
    До ready читач не має права трактувати відсутність стану як NEW. Стару історію лишаємо на місці. #>
    $target = Join-Path $OutDir 'marker-state'
    $ready = Join-Path $target 'ready'
    if (Test-Path -LiteralPath $ready) { return $target }
    $locks = New-Object Collections.ArrayList
    try {
        # Штатна перевірка живого слота має бачити його справжнього власника, а не наш замок перенесення.
        Clear-OrphanClaims $RunsDir
        foreach ($file in @(Get-ChildItem -LiteralPath $script:SlotDir -Filter '*.lock' -File)) {
            $lock = Open-Lock $file.FullName
            if ($null -eq $lock) { Write-Log 'перенесення стану: старий процес ще тримає слот'; return '' }
            [void]$locks.Add($lock)
        }
        # Свіжий claim може ще не дійти до замка слота; його теж не обганяємо.
        $pending = @(foreach ($claim in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.claim' -File)) {
            $state = $claim.FullName -replace '\.claim$', '.txt'
            # STARTED без зайнятого слота відновить штатний Resume-Interrupted вже після перенесення.
            if (-not (Test-Path -LiteralPath $state) -or -not ([IO.File]::ReadAllText($state, $script:Utf8)).StartsWith('STARTED ')) { $claim }
        })
        if ($pending.Count) {
            Write-Log 'перенесення стану: чекаю завершення старих узятих позначок'
            return ''
        }
        [void][IO.Directory]::CreateDirectory($target)
        foreach ($file in @(Get-ChildItem -LiteralPath $script:StateDir -File)) {
            # part не є завершеним записом; усі кінцеві стани й бічні файли зберігаємо.
            if ($file.Extension -ceq '.part') { continue }
            Write-FileAtomic (Join-Path $target $file.Name) ([IO.File]::ReadAllText($file.FullName, $script:Utf8))
        }
        Write-FileAtomic $ready '1'
        Write-Log "стан позначок: $target"
        return $target
    } finally { foreach ($lock in $locks) { $lock.Dispose() } }
}


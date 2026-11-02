$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:NODE_PATH = 'C:\Users\gemini\kod-shi-test-node\node_modules'
$runDir = 'аудит/проби/автоживий-a5872364316e641813b47bd3c7bfef9c7180f917'
$sceneDir = "$runDir/б1_концерт_стримано"
$startUtc = [DateTime]::UtcNow.ToString('o')
python 'аудит/проби/записати_сцену.py' 'C:\Users\gemini\gemini-runs\w\20261030-181808-f31de84629ae\tmp\build-afe95d98' 'C:\Users\gemini\pyodide' $sceneDir --сцена 'б1_концерт_стримано' 2>&1 | Tee-Object -FilePath "$runDir/запуск.txt"
$sceneExit = $LASTEXITCODE
"$startUtc початок; $([DateTime]::UtcNow.ToString('o')) кінець; rc=$sceneExit" | Set-Content -LiteralPath "$runDir/done.txt" -Encoding UTF8
exit $sceneExit

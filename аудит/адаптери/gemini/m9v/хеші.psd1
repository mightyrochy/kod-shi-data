# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '0BF2519191E0B7F268BFF48648E044FAE68026CF51C40A788D903B24F4041A4A'
    'wrapper_health.ps1' = 'E31696F43FD64F9BC1EE3195B32A1A90F5A3AF795C4F84444390FFCFF5FD285C'
    'gemini_run.ps1'     = 'E118D095C208FBC3E2D3C2AF17CA1AD751632F06184EEA087E0EBD2CAD189CD6'
    'gemini_publish.ps1' = 'E80B5B5ECC597BDB5ED32447C95AADA96FEBFD4319E03840A6EEA2880379276C'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '2FFC5327126072A4254DCED8BC6E8D95A63091D48A839D38D5835FCAB2E86B6D'
    'claude_run.ps1'     = '8EE343A9178894AAF07AB14F6B7D1EF415ADD868E43A6F68F029E95866B69484'
}

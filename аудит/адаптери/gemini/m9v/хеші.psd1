# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '0BF2519191E0B7F268BFF48648E044FAE68026CF51C40A788D903B24F4041A4A'
    'wrapper_health.ps1' = '3586C0A2154B1D8DF825C88FF6A9DC10A8E3F97822925B5BF55DD20AA3B99732'
    'gemini_run.ps1'     = 'A7CA0D07B5CD97E2E3021FBB27DD948438EA357BAC11F60133E914B393CB06E7'
    'gemini_publish.ps1' = '651718F8227770B4D9BADF001719DDCA60604DEE8BFEB3C8D19B6FC3D2D32DF8'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'BF537CED95CA166D47ED374D771FF867B12B9735E1B628CE75992BB4B61BC33A'
    'claude_run.ps1'     = 'B0B4E003DC58820BD8B3F5F97C9C39600C2323DA3DD61BB9CC40E32F9E278B92'
}

# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '99C1766CD93D0935C1804275B75F09C32C377427F347B91432D82869FAE34194'
    'wrapper_health.ps1' = '55322A52016AB826AA935066B94ED2871A5DDA81998C5FC16E13D16273F14BEC'
    'gemini_run.ps1'     = '180A5AF9CCA7A790F27FE0A0BDA47CBAFDFAFE7AD6E4CFAFD97ECFB8108DBF65'
    'gemini_publish.ps1' = '535EB8AABE351D1657398BC0F560D13B0CC4B6B3D84949068B34007DDF489630'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '4D39AB1D8AC60D0F64CBB0260C74EAB9F9FC71DA0174E112B48A06647A45FBBC'
    'claude_run.ps1'     = 'C736132296FE356171DFD2EAEF69F0F6EDB9AF1E558DF875A75E641724F738BA'
}

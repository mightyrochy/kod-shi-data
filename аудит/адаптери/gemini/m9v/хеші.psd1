# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_health.ps1' = 'FCE45448539D53A6B5718319842FC845DA870F39453A6B716C7AF8A2DB65B88E'
    'gemini_run.ps1'     = 'AF5B33D322B3A040BD6B91E2A3D992C22068D1DED94CEAFB323A62891DAD6FDE'
    'gemini_publish.ps1' = '904ABCC5FE198EFF89B4BA956C7B58742AD54932CAE4A3F01673416B6E4506B2'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '23BF290032E38380132C44D94ECDB2AF2480BE7710C14CEB6799A9D482187407'
    'claude_run.ps1'     = '249CF4B2826B079F4B68B6BDC7A6DDF431EF3E2AE7D130490F72EC0D8DDDF094'
}

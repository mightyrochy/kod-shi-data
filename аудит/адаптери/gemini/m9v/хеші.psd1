# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '79BD08F866529B1C58FE57AF33252AA4F0F7B3D992352130A7824030F27A57CD'
    'wrapper_health.ps1' = 'FCE45448539D53A6B5718319842FC845DA870F39453A6B716C7AF8A2DB65B88E'
    'gemini_run.ps1'     = 'E2B429E5DFEB59FF7909331D57365BD3A55EC78C7257041CD3EAF133490A2C8E'
    'gemini_publish.ps1' = '09B2581BE33F68AA2FB3FDFDE680326E31F4140945D006EFD97C17CB69AEFA25'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'C06A78446762B98EF3D045EB16ADFF15EDBAF1068959F94E346FC3A0069B5918'
    'claude_run.ps1'     = '3A370295FFE2E96E1DF932AAE0E77AE635C185825A1E81CE9865F3507EF10876'
}

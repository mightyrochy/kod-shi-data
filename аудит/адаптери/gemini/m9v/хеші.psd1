# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '703D9753D9EF7273619F5BA28278088E99C24E1B0CA4A0F1E75B52D870A8DCBE'
    'wrapper_health.ps1' = 'D03E371F34B3AC2881B70047563260905CD2DEB343DCD8608257495E531B90EA'
    'gemini_run.ps1'     = 'B3874A2DAB481CB3B700AE75E2E8550B428539459A1B204164C20E7FFF0C42ED'
    'gemini_publish.ps1' = '37092D886DE05781E2236F8CD245BC762778D12D03B12E340674ABCDFFB59FDA'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '7BC137923E8DAF58A9D1804E0040AFA9668D6D47C0FC9D6019BC2E7BC167D295'
    'claude_run.ps1'     = '166EBEC2519F39B854CF7E3422C16C878C6E0EAF72571F3AFD8E2A16D0EA9956'
}

# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '806F6DD792213D702F7EF9079318C450AD4EEE651B88DA13E749F6DD5FE052D2'
    'wrapper_health.ps1' = 'D03E371F34B3AC2881B70047563260905CD2DEB343DCD8608257495E531B90EA'
    'gemini_run.ps1'     = 'B645BAEC41D3E92716B3A64220A7E5EF2991CE3F4EF9ED01E72E65C4484CB769'
    'gemini_publish.ps1' = 'E6A7383F68DFB42915ACED37F416F1BC83C2BE78E2BAB13233A7A13F6244C8E6'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '7E88FC8CE1F79069BD112681424F37EF6347E50135B20549C9BE3274AD68AD6A'
    'claude_run.ps1'     = '61C0730FA3F50B1D9F71ADE12CAC8E162DBCF8E7A874C38C06B28DEF5FAFE570'
}

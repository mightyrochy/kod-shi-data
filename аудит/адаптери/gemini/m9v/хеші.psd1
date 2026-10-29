# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '99C1766CD93D0935C1804275B75F09C32C377427F347B91432D82869FAE34194'
    'wrapper_health.ps1' = '55322A52016AB826AA935066B94ED2871A5DDA81998C5FC16E13D16273F14BEC'
    'gemini_run.ps1'     = '73E2F0DC92121EE7D9F9F0AEBCFF9B41C8F6E7188DCFCF9240C9CFFBD71E80B7'
    'gemini_publish.ps1' = 'CD73426B56339EBE29AC27C4118B74D4A607E7E170AD246D3B3BE848A78B6889'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '38CAADE81B6277F860D125A1DF83E3B6956D22220CBD97B57B033FF14D46F475'
    'claude_run.ps1'     = '887DF4ABC221AE78B947AB22B916BF13FD0591D80810094B26EBE0700E06723E'
}

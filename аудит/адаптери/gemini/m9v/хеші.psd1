# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'AC5AC68AFCB3E9C93DEDF20EAEC0466CF331C990CC93C8748D5B70D034E6DB88'
    'wrapper_health.ps1' = 'FCE45448539D53A6B5718319842FC845DA870F39453A6B716C7AF8A2DB65B88E'
    'gemini_run.ps1'     = '4E08FB22F7B4AC3BEC7ADD230F2BE0EA3788DC23030525DA98023C02E4CF1C78'
    'gemini_publish.ps1' = 'E542F2BECB9FEBE362219D1CE80548052F58B3154F37D92AD3F933A1DD51A5F5'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '1752616A6EB0F6B06803F7100E12E836D23C4674979EAFF41FF03D22C33E4B7A'
    'claude_run.ps1'     = 'B2D0C64BBBCD84583A8C9767AAC046BE51ACF25A2AAEB86D3F1A114DB39AD679'
}

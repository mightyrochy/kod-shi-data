# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '4156307A17BDAE3AF7249E532947F659E99AA1349D159239159FAE60CA7E4F2B'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'B3BEA77E947CEC3B9E5EA4427A6E25AC6438024273CA5F36270B9FD66A1282F4'
    'wrapper_health.ps1' = '4F68274011C4EB6FC1E560B4E181FCDED1355E998B8597BE10E6DFE775358B1E'
    'gemini_run.ps1'     = '1D1A800826AB2E2F8DEFAFD03FFBC57BB14785C7853243C3C7CFF2518588C094'
    'gemini_publish.ps1' = '5A5D4D2626B4244CD5F626BF4B1673AD313FFF7C3F12CD540DEF318AA62353AE'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '727A609FE6B078B84FEB2BC95C1972E56DF647218972EC279BB85DD63486DD5B'
    'claude_run.ps1'     = 'F4130248484B78131EAD1D0C9385ABE2FB45D516BE556308C398130073E9D1B9'
}

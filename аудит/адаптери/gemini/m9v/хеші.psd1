# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'FE90681BC87A2F4A94684ABC1B8000B1E2FA4468AD9DECABD84B3F741C2E13BC'
    'wrapper_health.ps1' = '4C3CF324647C66517B9A4018EEF3B0256C81822197C3EF015230DED8CF12D9E6'
    'gemini_run.ps1'     = 'FBB849D8F9E0F5FCC0524C9F3BE78E21F0098BB040FF64D2DBF74E43C8DE611E'
    'gemini_publish.ps1' = 'AABCA50535699147DC8E4DA139177AED74C20BB47BD61141D9B726B79DFFF695'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '60E561848F837B0256B645C79BFFB51424878DBD58A3F7A0EB0607FB2D3E7361'
    'claude_run.ps1'     = 'C6DF289AC00F7F617765A12E4B7A1D80DDFFF53D7F5863FAF9AD2B01988B81E7'
}

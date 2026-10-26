# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'gemini_run.ps1'     = '51AE7E1611A13419CDAB3CFC6FB7A9D45E027ECCE87175FD9A0B6CE08A3DE0BC'
    'gemini_publish.ps1' = '639D3AA7A7F1238FDA06B4E2145B5C429B917A1E99E17E2E58481FDE98D74D77'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = 'CEBCDD8FFEAFCDF29D9B4F5F624F00E8C8AE9A3811B49E87D3EB6B9B992C24ED'
    'claude_run.ps1'     = '16EDAFBC06A4212E3C7FB6173C60F7BAA38C0B901BF936DA1510B3969042DB22'
}

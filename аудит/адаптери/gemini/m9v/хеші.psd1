# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'gemini_run.ps1'     = '0C45CD2C2C43C5EE66D5C50DFECDA61DD32AAC34E829E7BAE2F8CDC68BEC3973'
    'gemini_publish.ps1' = '4CFFE78BB534AA02A8E5F5E9E27146D14B6A63437A3BB45D33B7045846C0FFFB'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = 'CEBCDD8FFEAFCDF29D9B4F5F624F00E8C8AE9A3811B49E87D3EB6B9B992C24ED'
    'queue_lanes.ps1'    = 'B1ED308B8517EF14D9F5FF9DEE29B8E66165F6C8CEBEE22997E25D08AFA12939'
    'claude_run.ps1'     = '46B9A157D8A46BE4C0251FCAD8EFB921ECBD990E7348E819E37C4DC47493B650'
}

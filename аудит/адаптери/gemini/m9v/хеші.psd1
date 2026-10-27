# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'gemini_run.ps1'     = '65FDD272EE6D6D3AFF2622D54174F9C1960C708AFDE57F83943AE90DAA16DD18'
    'gemini_publish.ps1' = '4CFFE78BB534AA02A8E5F5E9E27146D14B6A63437A3BB45D33B7045846C0FFFB'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = 'CEBCDD8FFEAFCDF29D9B4F5F624F00E8C8AE9A3811B49E87D3EB6B9B992C24ED'
    'queue_lanes.ps1'    = '0D2BE9DE68DEC2602E6671EEE50BA94008BD436619E9603A086A5BC3E03A5E20'
    'claude_run.ps1'     = '03F740987233B9C8BA9BF172957D03AC2447DD6911CE9C820BE3E7D95037A59F'
}

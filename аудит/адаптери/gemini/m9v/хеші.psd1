# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '9526C2BA3CB47ADAAB59D3DF8186D5EAF1140CBD09D734DF3A77C8B80E092AF5'
    'wrapper_health.ps1' = '1427DF6C7CF1A6D5EDBC66072B58ED085A34C15D3DC7463750F93FB06F5FA810'
    'gemini_run.ps1'     = '757DC88DA92037F530973410366A6EA89B4BD0787E0FA9EB0B16734A73A997C5'
    'gemini_publish.ps1' = '92B99FE4E0AF3D641524775BD714CB7F19A0EC4727E94BA095C4F026969427BF'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release), коли codex нема
    # чи `codex --version` не дорівнює CodexRelease.
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.169.1'
    CodexInstaller       = '365F40F3D0FE417388B8F75333D66657481D86769E2EAFED29967921B928484F'
    'gemini_watch.ps1'   = '951F0172A00D7FE577EE4B35CFC42D42B8D749F67349967ACA22CE4540EDE24C'
    'queue_lanes.ps1'    = '9D0FCC853E35AC53491F2624D6F469E12F9AC955BBD04A41ADA73BC68B6B56FF'
    'claude_run.ps1'     = '401C9CAACA01A412BD9292E73435CA064C719E9D01845DC93AB73F16E6A4B0FC'
}

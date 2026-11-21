# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '5DE1ED394386AD61A45414AAE03439B626A618C9F453529672462C193A855964'
    'wrapper_health.ps1' = '1427DF6C7CF1A6D5EDBC66072B58ED085A34C15D3DC7463750F93FB06F5FA810'
    'gemini_run.ps1'     = '68FF899249F14EDE958E990F6FB4210A7F7F264C166749126820E9F65978D26F'
    'gemini_publish.ps1' = 'D2436456B600DA072A295340695ED5FD289C273D1A4542066D701777C0EE9650'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release), коли codex нема
    # чи `codex --version` не дорівнює CodexRelease.
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.169.1'
    CodexInstaller       = '365F40F3D0FE417388B8F75333D66657481D86769E2EAFED29967921B928484F'
    'gemini_watch.ps1'   = '951F0172A00D7FE577EE4B35CFC42D42B8D749F67349967ACA22CE4540EDE24C'
    'queue_lanes.ps1'    = '99024755C7B7A059FF0E36FBFA97F76DCA898B7C712E45B5BF62877BB05F402E'
    'claude_run.ps1'     = '974889039A755DFA8F660BB85DFF72DAB71989A90DB2D1CE6C37291DBE8E36FC'
}

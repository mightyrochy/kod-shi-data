# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'DF8B975738046EC77BBBDF1CBB32F09ED18377D998798F327F80EE462042B528'
    'wrapper_health.ps1' = '42AE62063EC68CD336AD059F2E45BA0ECFFC781F0ADF138952F0DC8EE50A1CDC'
    'gemini_run.ps1'     = 'CFD445018C50059A17FC7397068546BB78B71DE8B006F29C43D8F5CAA1F64AFC'
    'gemini_publish.ps1' = '95152B7F6DE2772F80D14193C63214329EB467249D4A380818A6150787E4A4E1'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release), коли codex нема
    # чи `codex --version` не дорівнює CodexRelease.
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.169.1'
    CodexInstaller       = '365F40F3D0FE417388B8F75333D66657481D86769E2EAFED29967921B928484F'
    'gemini_watch.ps1'   = '3F02DC6D522166CD9580B579143E35C32A9931168C1B1191A7771A040E7ED920'
    'queue_lanes.ps1'    = 'C45309FF195BAA2E8295FB8AD2062BECF7BBF5BE7EC993E4694F3443B297584D'
    'claude_run.ps1'     = '63AF15771D18159D5CF06269B5D0D0B369BB94299F3B370918F1FEC146BBA46B'
}

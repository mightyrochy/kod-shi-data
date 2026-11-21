# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '46A19E7B859E2EFB1E3797317C5F001780E81D74FC19E74A309C807D4BEBB1AF'
    'wrapper_health.ps1' = '1427DF6C7CF1A6D5EDBC66072B58ED085A34C15D3DC7463750F93FB06F5FA810'
    'gemini_run.ps1'     = '1B327C84ED23848ED2F478BC841B6353AA387387914E2128AF21DB6D580709F8'
    'gemini_publish.ps1' = '02AA55FC7FE16F1A716BE2A1434EB838EF0477F50BC7D82FFBDACC4D69E1F78B'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release), коли codex нема
    # чи `codex --version` не дорівнює CodexRelease.
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.169.1'
    CodexInstaller       = '365F40F3D0FE417388B8F75333D66657481D86769E2EAFED29967921B928484F'
    'gemini_watch.ps1'   = '951F0172A00D7FE577EE4B35CFC42D42B8D749F67349967ACA22CE4540EDE24C'
    'queue_lanes.ps1'    = '622EE19387A82FB7FC93C530E5EA335D2FCA8A126E06AE235A991129AA2109E0'
    'claude_run.ps1'     = '5A23D70288B6B8A9817A0AA322492E0550E3A61421E72797FFA1FCA2C2FD22A7'
}

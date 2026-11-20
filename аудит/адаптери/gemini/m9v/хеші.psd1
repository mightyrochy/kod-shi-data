# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '4CD8538BB06AAAACCABDFBFBCE3C3D2434819E23380E679CD3D15A182BEF532F'
    'wrapper_health.ps1' = '1427DF6C7CF1A6D5EDBC66072B58ED085A34C15D3DC7463750F93FB06F5FA810'
    'gemini_run.ps1'     = 'FBF69B78BB4E85F92AB12192122F787FA36E7E38D9C24228F7252921BC52DB7E'
    'gemini_publish.ps1' = 'BE2F7BAF27F622EE7EC7DCCE196728F6AA962609F3C8180EE88AFB4E943CF442'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release), коли codex нема
    # чи `codex --version` не дорівнює CodexRelease.
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.169.1'
    CodexInstaller       = '365F40F3D0FE417388B8F75333D66657481D86769E2EAFED29967921B928484F'
    'gemini_watch.ps1'   = '951F0172A00D7FE577EE4B35CFC42D42B8D749F67349967ACA22CE4540EDE24C'
    'queue_lanes.ps1'    = 'D808F835436DFB1B6A1CB0240472C7273A1B44B44305E8DB49104BC471BB1DBE'
    'claude_run.ps1'     = 'AE640D0BA236225565CA8AC3FED519612371E6D4E7F61D03E26A39EC6E8C6678'
}

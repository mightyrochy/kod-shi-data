# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '51DBAF9DA89D5C0BCC704A9E32B7C6C974383385C40377079931EE81F8CF4068'
    'wrapper_health.ps1' = 'AD02D0BF5FF58AC4092370612DC7B13ED89F55270008F00F2888937C587456F3'
    'gemini_run.ps1'     = 'A80CB406404D02217BB9971858A414AC89DF048279EC05E7F92D68D30D921355'
    'gemini_publish.ps1' = '7D26FC42FE63E1A652E655BC804FB528FA828821D0FA380F98EC3DA9287B5907'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release), коли codex нема
    # чи `codex --version` не дорівнює CodexRelease.
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.169.1'
    CodexInstaller       = '365F40F3D0FE417388B8F75333D66657481D86769E2EAFED29967921B928484F'
    'gemini_watch.ps1'   = '4E2A6A0F16C41B9B4982CF9CC4D535E27D86138CEBD222FC529BA7CA926BBD0D'
    'queue_lanes.ps1'    = 'AC0E5A4381C1EBBD2AB2E4C48141F9948E4A186F1D09EDD7F862992213C598A0'
    'claude_run.ps1'     = '6B34380DCF75F2E91E5C796207F74EE2627915A58FFEA3E5B76FEAE84FEDDADF'
}

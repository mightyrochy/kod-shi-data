# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '457BB1DD87DCBF82027C42BD872E8F4A2B238E37090142756AEB02F61976BD94'
    'wrapper_health.ps1' = 'FFC6F4D0A7D261AA3D0DF6B9DA16B11C7B33C0832D48D4DDE5B04BA5F3302D27'
    'gemini_run.ps1'     = '00317B3F9DB9252E4B88557C6A8BEAEB403220F640AB0128A220B17502767D92'
    'gemini_publish.ps1' = '45610967E231F94731B97524EF74392EB23F8254C6249B61445E0DBF10AB5A0B'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '77FE75B2BC5AC2BF20B5ECE88892B52C1A2F660BEA0DD1038C73C088D6121C9A'
    'queue_lanes.ps1'    = '7452BD271202A9DE4F02FA6ECA9BFC7DF882AA4E796F0E7A482E8BB121821018'
    'claude_run.ps1'     = '65FB86B05672417F8A94A98961735C787D80BE39AEEACDDC850BE43E98368360'
}

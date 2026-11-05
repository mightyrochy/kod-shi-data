# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '0823C722AD4C3B1411C10663D6E82A98BD95B0E06E5E78437495C7B2271B251F'
    'wrapper_health.ps1' = 'AB85BBF974EA56281C2824C12CA11BF775013C6AD7F9C67AD4E8DC433931E817'
    'gemini_run.ps1'     = 'F023C3B7878F48F2D7C089323827C9652FB591B60D480FBC368DBD7AEBC05709'
    'gemini_publish.ps1' = 'CE38E29C0E7EC362F2ED5919311F4D89034DBD79DE39B2229ECC71802FC8CD7F'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '1EAF2B45A2095C5A81534059949AB4988E80676D86CCC195B1C2CFFB04F86A9C'
    'claude_run.ps1'     = 'F5E2423591ADF11908CFDAD37679A443308E73F255A7F7E9B845D9A4875181FC'
}

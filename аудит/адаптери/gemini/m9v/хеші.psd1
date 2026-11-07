# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '0823C722AD4C3B1411C10663D6E82A98BD95B0E06E5E78437495C7B2271B251F'
    'wrapper_health.ps1' = 'AB85BBF974EA56281C2824C12CA11BF775013C6AD7F9C67AD4E8DC433931E817'
    'gemini_run.ps1'     = '917AF4D22A073B84980ED974C41BBFDB070F7D650C9AF80F8019D61A75CF16AA'
    'gemini_publish.ps1' = 'A78CB04871CA82C6F44EEA09F8E841F746F40F0862FAA7FBFEF3DEFF290DC88A'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'C417E425861D4E687C8000636E3557E01015CA083C5CF4300066EC45F4D33F41'
    'claude_run.ps1'     = '3B135BDEF1E443690A338FFEDF18237632E795C4E7C1A2F46503923042BD8917'
}

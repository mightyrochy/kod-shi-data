# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'ACD29115A62A10E84A9BE1B4B829F5301739E0E3A8F854D01EB5DEDC9B38012F'
    'wrapper_health.ps1' = '4C3CF324647C66517B9A4018EEF3B0256C81822197C3EF015230DED8CF12D9E6'
    'gemini_run.ps1'     = '15BDA9DEB476FB47FC40A51562582357129834605C1835088C75E8FF5DC65AEA'
    'gemini_publish.ps1' = 'CE20359F291DCF1D0674E2AC826503DF86004B23C64793AFB20E22E9308B4893'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '09B0CA81B98F36CDC5194EF94D47501A84C7034EA062FDB77A0BE6EC0C2459AF'
    'claude_run.ps1'     = '71CDBED1D78C88A03FC3731A5E892D059E3E2F939B5879821FBF9F07DC2A67B9'
}

# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '52D6A12EB4A0B1E7FE98893752A292CD23F2746B12A97DEF34825D3DFEE58EFA'
    'wrapper_health.ps1' = 'F63CDFD76BCBE92440A843759BCD6CED4E49B4BCBAC19620CACA4B74B9D58AA5'
    'gemini_run.ps1'     = 'A237E8CAFC624DF3D062282D97142DCE1C9C85FDD1CBB16559FB1FCBC1F22ADA'
    'gemini_publish.ps1' = '0AF4A7E5833A5CB12E5A5C53E885B32E87791D863A95BCEFD8594396D5080598'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'B4A615F82FA9EE85740AAE13AE57A9D021AB1D2F3F1873A9E3F65B87D96DA935'
    'claude_run.ps1'     = '01422B679F230E2674A01CC74468C12781FA1E83528CAE4ECBB3F2BCD3B1A0A5'
}

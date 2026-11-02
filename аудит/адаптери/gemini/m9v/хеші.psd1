# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '52D6A12EB4A0B1E7FE98893752A292CD23F2746B12A97DEF34825D3DFEE58EFA'
    'wrapper_health.ps1' = 'F63CDFD76BCBE92440A843759BCD6CED4E49B4BCBAC19620CACA4B74B9D58AA5'
    'gemini_run.ps1'     = '8D30203E90DF003328A01D77426A7BD9C195516B86A6FFCE3C38EB239E6A9CAD'
    'gemini_publish.ps1' = '0AF4A7E5833A5CB12E5A5C53E885B32E87791D863A95BCEFD8594396D5080598'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'C2E168714A6968AB2BC06EE1000C513F8FDB035969E2DB6C519504FE058D7818'
    'claude_run.ps1'     = '8C0610B95775267963CE5B1FC6B6A3E73EA348994BF6428711CE6EA2690FEC8D'
}

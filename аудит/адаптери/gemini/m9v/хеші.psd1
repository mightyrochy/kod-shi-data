# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'ABE9238B05AB0EAB3E65912867159FC06EDE415188EC22E9C4D8DD2DD88487BA'
    'wrapper_health.ps1' = 'F63CDFD76BCBE92440A843759BCD6CED4E49B4BCBAC19620CACA4B74B9D58AA5'
    'gemini_run.ps1'     = 'ADC4A9549E85637C9ECF1E7EEE510CF44BD82EEC8553669B100DE02DA296F852'
    'gemini_publish.ps1' = '53D8542D7AC9FC822D7E75BA490E1EC3AA24CB4680E5887072749CC85076384D'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'FEAD267F76D269476E00F48C44366D4BA9D282B2BFC85CC64712968D430B4AFD'
    'claude_run.ps1'     = '54CEB63CD621ED319370CF830BA206D68D48973407E3A4DAA01F5F95EBDA8C55'
}

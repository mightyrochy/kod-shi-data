# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = 'BF788027E19C1ADEB64304CD3C29D68927FB7432421AA1E4984288977955BEE4'
    'wrapper_health.ps1' = '0186D5CDE98C3D4DB746E7AB6604DBEBE23ACA1BBE7E704EC4356B7558EBF7FE'
    'gemini_run.ps1'     = '63262440433E5549788571B7EF13F5E667001D2A452C8CEEF9E7EC7FC47EB520'
    'gemini_publish.ps1' = '6BA3002105259A6B7B232377E7D028DEBF3D6FD32FBD02F2475DF34C0E1A639A'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '5486191EC473DF871DD9139906FEA9CEDA6899A554C5902D6440F8253181F50E'
    'claude_run.ps1'     = '00C34978884D54B08B4EB20B141FCFA9C4513DCE20284C5E6CE4677572660FA7'
}

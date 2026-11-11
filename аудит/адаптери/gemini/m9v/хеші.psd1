# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '1E4E0C20AB8C88F586AE4D33F4A09F6F9CAAE923BF0A2D1B40276775997276D6'
    'wrapper_health.ps1' = '427A93D376A27296EC4601F0AD5D4E89215566B0911EF7F4F7297370ADC48D72'
    'gemini_run.ps1'     = '8CDF63285AB7E1445B95AFCBDEDAEC7B05712FDF06C15308A725ACD603385041'
    'gemini_publish.ps1' = 'EEEF2480781F8AD3B262B7811C62F84B4BA46984B5A0CB8423709F04AF6F5A89'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = 'BBFE0CE39ECE8792FC2B745904AD38424BC3BAB19941D57D1CD2F183536D2A7C'
    'claude_run.ps1'     = '199D01523182F0BBD46EA41D7515A3E44100BF8DD38B745336AB3DDC31000CCE'
}

# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '1E4E0C20AB8C88F586AE4D33F4A09F6F9CAAE923BF0A2D1B40276775997276D6'
    'wrapper_health.ps1' = '4C1C77CE88B6AA4866EF4E75127105CF2B5DE77D3230F67C4637511EE5897C11'
    'gemini_run.ps1'     = '8DB479794F4F3BB1D8ED17ACEE5BEE755728134E13356543F47F3DC6E8BFEE10'
    'gemini_publish.ps1' = '45E49ECEFE454C81D974284FC077F6AE7B81782684AFCCB7A657DA4CF0440AAC'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '842711D097692BB636C59C8C8983B55934729AFB17B5196BEFAA6D1B43771538'
    'claude_run.ps1'     = 'D9355FDF898444B540128B4DFBFDED40BC25050C4A0EC05652AF9D57D3D41F50'
}

# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '1E4E0C20AB8C88F586AE4D33F4A09F6F9CAAE923BF0A2D1B40276775997276D6'
    'wrapper_health.ps1' = 'AB85BBF974EA56281C2824C12CA11BF775013C6AD7F9C67AD4E8DC433931E817'
    'gemini_run.ps1'     = '9AA1C424DFA59A28B1E472C83CE20A4179CA55830C5BFCC54ECC7D6E3E33DC65'
    'gemini_publish.ps1' = 'CE20359F291DCF1D0674E2AC826503DF86004B23C64793AFB20E22E9308B4893'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '4800713F0AF53F7C58A6475E6F8639012E6CCC8867EE482074A374D6777AAC50'
    'claude_run.ps1'     = 'C43DC21F2F6449A94DB581999083892825BB640C91A152A3F6E9894B19E7EBDA'
}

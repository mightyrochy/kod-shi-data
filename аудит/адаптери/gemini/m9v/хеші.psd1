# Очікувані SHA-256 файлів обгортки — єдине місце для скриптів m9v. Рядки тут мають збігатися з таблицею «Хеші файлів»
# у ../НАЛАШТУВАННЯ.md (стенд `перевірка/сценарії_m9v.sh` звіряє). Міняється разом із таблицею (PR, що чіпає обгортку).
@{
    'wrapper_update.ps1' = '45F254E5CB2FB7D882BBB9CE7CA121988FDF23BACCFE65CB67A4CA3B3F426FE7'
    'wrapper_probe.ps1'  = '85116D04C22EB64CBFF52E66BCEAE9B1091577A889EDD58A8B634093A82BDBC6'
    'wrapper_chain.ps1'  = '2C44BD77A2180F47054212220BCD473DEEC088B7EACE2646B3B40047752C8785'
    'wrapper_health.ps1' = '60C5B00A3E986C387525BBF1DCDB4E0ED067E47A526D81748EA8FBAA1F9ABF22'
    'gemini_run.ps1'     = '3201B9494FF375A199FC542FF8A665487065A7E752A0081DCDB54E734E8A9AB3'
    'gemini_publish.ps1' = '651718F8227770B4D9BADF001719DDCA60604DEE8BFEB3C8D19B6FC3D2D32DF8'
    # Інсталятор Codex (9741) закріплено за релізом: install.ps1 — файл релізу https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1
    # (незмінний URL; той самий sha256 віддає https://chatgpt.com/codex/install.ps1 — редирект на releases.openai.com — і публікує реліз
    # openai/codex). 2_під_gemini.ps1 -WithCodex виконує його лише при збігу CodexInstaller і ставить саме цей реліз (-Release).
    # Оновити Codex = новий PR: нова версія, новий хеш (докази — у PR). Порожній хеш — інсталятор не виконується.
    CodexRelease         = '0.164.0'
    CodexInstaller       = 'A59CB66350098C33B021FF470D586AE8FE3B7CAF189CA7137B4FE3AF5D4DCE74'
    'gemini_watch.ps1'   = '69EFEBB07FF1AF51C382B753A95C50F3C1AC27B3008F2489992BEBE3FD0213AA'
    'queue_lanes.ps1'    = '12F0FBF86F7C4C481F3A39800B37E0E3D734BB3007C7F55D83D913B005A22414'
    'claude_run.ps1'     = '1E3A40E4ABD79169CBB183EC2AC6CE045A892DFB02C6DD98EC294B7AD510D420'
}

from pathlib import Path
p=Path('аудит/БЕКЛОГ.md'); raw=p.read_bytes()
lines=raw.splitlines(keepends=True)
indices=[i for i,line in enumerate(lines) if line.startswith(b'| 5190 |')]
assert len(indices)==1
i=indices[0]; before=lines[i]
sentence=(' Однорядковий повтор за новим прямим дозволом власника на SHA 4c400859: '
          'Mamay 97 викликів/366,676 с, 97/97 валідовані, 75 known/22 unknown (17 ambiguous/5 no_colour), '
          'відхилень і cache hits 0; Lapa не запускалась. Схема/промпт/строгий валідатор незмінні; '
          'усі 97 кешів незалежно звірені офлайн. Це підтверджує залежність спостереженої помилки '
          'від пакетування, не семантичне приймання кодів. Артефакти a469f6f4; ≥38/40 і товарний допуск не заявлено.').encode()
suffix=b' |\r\n' if before.endswith(b' |\r\n') else b' |\n'
assert before.endswith(suffix)
lines[i]=before[:-len(suffix)]+sentence+suffix
p.write_bytes(b''.join(lines))

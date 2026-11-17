// Той самий дим карток, прокручений до питань і поля коментаря.
const fs = require('fs');
const path = require('path');
const original = path.join(__dirname, '..', 'дані-4031', 'знімки.cjs');
let script = fs.readFileSync(original, 'utf8');
script = script.replace("['до', [], 0], ", '')
  .replace("['після',", "['після-низ',")
  .replace("['після-спідниця',", "['після-спідниця-низ',")
  .replace('.scrollIntoViewIfNeeded()', ".evaluate(el => el.scrollIntoView({block:'end'}))")
  .replace("'знімки.json'", "'знімки-низ.json'");
module._compile(script, __filename);

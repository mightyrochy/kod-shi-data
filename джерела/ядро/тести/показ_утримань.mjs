import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

// Приймає дві знеособлені Картки з пакета н2-суд-повтор-4e9b.
const paths = process.argv.slice(2);
assert.equal(paths.length, 2, "Передайте outputs/held-70/card.json та outputs/registered-mixed/card.json");

const extract = (file, name) => {
  const source = readFileSync(new URL("../../показ/" + file, import.meta.url), "utf8");
  const match = new RegExp("^function " + name + "\\([\\s\\S]*?^\\}", "m").exec(source);
  assert.ok(match, name);
  return match[0];
};
const { project, merge, count } = vm.runInNewContext([
  extract("ядро.js", "карткаЯдраНаЕкранП"),
  extract("мовний_шар.js", "звестиПитанняП"),
  extract("мовний_шар.js", "чекаютьРозгортанняП"),
  "({project: карткаЯдраНаЕкранП, merge: звестиПитанняП, count: чекаютьРозгортанняП})",
].join("\n"), {
  МОДЕЛЬ_МОВИ_П: true,
  повідомленняОписуБезФотоП: () => ({ fixture: "description_without_photos" }),
});

for (const [index, path] of paths.entries()) {
  const card = JSON.parse(readFileSync(path, "utf8"));
  const held = card.невідоме.filter(z => z.утримано);
  assert.equal(held.length, index === 0 ? 1 : 3);
  assert.deepEqual(project(card, 37).невідоме.filter(z => z.утримано), held);
  const withRepeats = {...card, невідоме: [...card.невідоме, ...held]};
  const display = project(withRepeats, 37);
  const questions = merge(display.питання);
  const lazy = questions.filter(q => q.на_розгортання && !q.для_всіх && !q.текст
    && q.повідомлення?.kind);
  assert.equal(count(display), lazy.length);
  for (const z of held) {
    const matches = lazy.filter(q => q.ід === z.ід);
    assert.equal(matches.length, 1, z.ід);
    const [q] = matches;
    assert.equal(q.правило, z.правило);
    assert.deepEqual(q.речі, z.речі);
    assert.deepEqual(JSON.parse(JSON.stringify(q.повідомлення)), {
      kind: "card_unchecked",
      statements: [{code: z.код, values: z.значення, item_ids: z.речі}],
    });
  }
  const codes = questions.flatMap(q => q.повідомлення.statements.map(z => z.code));
  assert.ok(codes.includes("rule_input_missing"));
  const rawCodes = display.питання.flatMap(q => q.повідомлення.statements.map(z => z.code));
  if (index === 1) assert.equal(rawCodes.filter(code => code === "fabric_out_of_season").length, 4);
  console.log(JSON.stringify({fixture: index === 0 ? "held-70" : "registered-mixed",
    held: held.map(z => ({id: z.ід, rule: z.правило, code: z.код, items: z.речі})),
    lazy: lazy.length, ordinary: rawCodes.filter(code => code === "fabric_out_of_season").length}));
}

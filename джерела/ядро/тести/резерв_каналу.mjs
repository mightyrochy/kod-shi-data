import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const [старийВоркер, складенийВоркер] = process.argv.slice(2);
assert.ok(старийВоркер && складенийВоркер, "Передайте worker.js з бази та результат складання кандидата");
const джерела = new URL("../../", import.meta.url);
const міст = readFileSync(new URL("показ/міст.js", джерела), "utf8");
const політика = JSON.parse(readFileSync(new URL("резерв_каналу.json", джерела), "utf8"));
const функція = імʼя => {
  const код = new RegExp("^(?:async )?function " + імʼя + "\\([\\s\\S]*?^\\}", "m").exec(міст);
  assert.ok(код, імʼя);
  return код[0];
};
const адреса = /^const ТИПОВИЙ_МІСТ_П = "([^"]+)";/m.exec(міст)[1];
const порт = /^const ПОРТ_ЛОКАЛЬНОГО_ВОРКЕРА_П = '([^']+)';/m.exec(міст)[1];
const МІСТ_П = {адреса, токен: "fixture"};
const сторінка = vm.runInNewContext([
  ..."адресаВоркераП автоматичноДозволенаАдресаМостаП резервВиходуКаналуП _дзвінокП".split(" ").map(функція),
  "({резерв: резервВиходуКаналуП, дзвінок: _дзвінокП})",
].join("\n").replace("__РЕЗЕРВ_КАНАЛУ__", JSON.stringify(політика)), {
  URL, МІСТ_П, ТИПОВИЙ_МІСТ_П: адреса, ПОРТ_ЛОКАЛЬНОГО_ВОРКЕРА_П: порт,
  location: {origin: "http://localhost:7777"}, МАКС_ТОКЕНІВ_П: 4_000,
  fetch: (url, {body}) => ({url, body: JSON.parse(body)}),
});

const безМережі = () => { throw new Error("Unexpected network call"); };
const до = readFileSync(старийВоркер, "utf8");
const після = readFileSync(складенийВоркер, "utf8");
assert.equal(після, до, "Зібраний Worker має збігатися побайтово");
const конвертер = код => vm.runInNewContext(код.replace(/^export default/m, "const Worker =")
  + "\n(т => JSON.stringify(ПРОВАЙДЕРИ.find(п => т.model.startsWith(п.префікс)).запит(т)))",
  {fetch: безМережі});
const [старе, нове] = [до, після].map(конвертер);
const повідомлення = [{role: "user", content: [{type: "text", text: "offline fixture"}]}];
const вибірка = {temperature: 0};

for (const [модель, стеля, повний, overhead] of [
  ["claude-sonnet-5-5", 4_000, 16_000, 12_000],
  ["claude-haiku-5-5", 2_800, 14_800, 12_000],
  ["gemini-3.5-flash-lite", 4_000, 4_000, 0],
]) {
  const {body} = await сторінка.дзвінок(повідомлення, модель, вибірка, стеля);
  assert.equal(body.max_tokens, стеля);
  const {канал, надбавка_каналу} = сторінка.резерв(модель, адреса);
  assert.equal(канал, "worker");
  assert.equal(надбавка_каналу, overhead);
  for (const _думки of [null, {effort: "low"}]) {
    const вхід = {...body, _думки};
    const текст = нове(вхід);
    assert.equal(текст, старе(вхід));
    const тіло = JSON.parse(текст);
    const межа = тіло.max_tokens ?? тіло.generationConfig.maxOutputTokens;
    assert.equal(межа, повний);
    assert.equal(межа, стеля + надбавка_каналу);
    console.log(JSON.stringify({модель, стеля, межа, overhead, _думки,
      sha256: createHash("sha256").update(текст).digest("hex")}));
  }
}

for (const [url, канал, overhead] of [
  ["", "direct_anthropic", 0],
  [`http://127.0.0.1:${порт}/`, "worker", 12_000],
  ["http://localhost:7777/міст", "unconfirmed_bridge", 0],
  ["https://other.example/bridge", "unconfirmed_bridge", 0],
]) {
  const дані = сторінка.резерв("claude-sonnet-5-5", url);
  assert.equal(дані.канал, канал);
  assert.equal(дані.надбавка_каналу, overhead);
}
МІСТ_П.адреса = "";
const прямий = await сторінка.дзвінок(повідомлення, "claude-sonnet-5-5", вибірка, 4_000);
assert.equal(прямий.url, "https://api.anthropic.com/v1/messages");
assert.equal(прямий.body.max_tokens, 4_000);

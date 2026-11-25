const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2] || __dirname + '/worker.js', 'utf8');
assert.equal((source.match(/export default/g) || []).length, 1);
const context = vm.createContext({TextEncoder, TextDecoder, URL, URLSearchParams,
  fetch: () => { throw new Error('Network forbidden in this offline probe'); }});
vm.runInContext(source.replace('export default', 'globalThis.worker =') + '\n' +
  'globalThis.makeAnthropicRequest = ПРОВАЙДЕРИ.find(x => x.ім === "anthropic").запит;', context);
const rows = [2800, 4000].map(max_tokens => {
  const input = {model:'claude-sonnet-5-5', max_tokens, _думки:{effort:'low'},
    messages:[{role:'user',content:'synthetic request'}]};
  const output = context.makeAnthropicRequest(input);
  assert.equal(output.max_tokens, max_tokens + 12000);
  assert.equal(input.max_tokens, max_tokens);
  assert.equal(output.output_config.effort, 'low');
  return {page_max_tokens:max_tokens, upstream_max_tokens:output.max_tokens,
    addition:output.max_tokens-max_tokens, effort:output.output_config.effort};
});
console.log(JSON.stringify({sha:'9f632353ec20d986d61d52c0436e7bc981ee397a',
  kind:'pure provider request conversion; no request sent', rows},null,2));

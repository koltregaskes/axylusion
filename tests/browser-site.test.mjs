import {test} from 'node:test';
import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {browserSite} from '../scripts/browser-site.mjs';
test('explicit artifact selects that root instead of source', async () => {
  assert.equal(await browserSite(['--site','images']), resolve('images'));
});
test('missing artifact fails without source fallback', async () => {
  await assert.rejects(browserSite(['--site','missing-artifact-negative-control']), /Site directory does not exist/);
});
test('malformed arguments fail closed', async () => {
  for (const args of [['--site'], ['--other','images'], ['--site','images','extra']]) await assert.rejects(browserSite(args), /Usage/);
});

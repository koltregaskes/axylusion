import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const refresh=readFileSync('.github/workflows/refresh-routed-feed.yml','utf8');
const pages=readFileSync('.github/workflows/pages.yml','utf8');

test('the feed refresh no longer requests a legacy Pages build', () => {
  // GITHUB_TOKEN pushes do not start push-triggered workflows, so pages.yml
  // deploys when the refresh finishes on main.
  assert.doesNotMatch(refresh,/pages\/builds/);
  assert.doesNotMatch(refresh,/pages:\s*write/);
  assert.doesNotMatch(refresh,/actions\/deploy-pages|actions\/upload-pages-artifact/);
  assert.match(refresh,/^name: Refresh routed feed$/m);
});

test('pages.yml deploys after every finished refresh on main, including partial coverage', () => {
  const trigger=pages.slice(pages.indexOf('workflow_run:'),pages.indexOf('\npermissions:'));
  assert.match(trigger,/workflows: \["Refresh routed feed"\]/);
  assert.match(trigger,/types: \[completed\]/);
  assert.match(trigger,/branches: \["main"\]/);
  assert.match(pages,/contains\(fromJSON\('\["success", "failure"\]'\), github\.event\.workflow_run\.conclusion\)/);
});

test('pages.yml publishes only the allowlisted build', () => {
  assert.match(pages,/python scripts\/build-public\.py --output "\$RUNNER_TEMP\/_site"/);
  assert.match(pages,/tar --dereference --hard-dereference --directory "\$RUNNER_TEMP\/_site"/);
  assert.match(pages,/chmod -R \+rX "\$RUNNER_TEMP\/_site"/);
  assert.match(pages,/actions\/deploy-pages@/);
  assert.doesNotMatch(pages,/--directory \.\s/);
});

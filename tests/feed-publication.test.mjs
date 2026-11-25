import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

test('bot feed commits are published by the allowlisted Pages workflow', () => {
  const refresh=readFileSync('.github/workflows/refresh-routed-feed.yml','utf8');
  // GITHUB_TOKEN pushes do not start push-triggered workflows, so pages.yml
  // deploys when the refresh finishes on main instead of a legacy build request.
  assert.doesNotMatch(refresh,/pages\/builds/);
  assert.doesNotMatch(refresh,/actions\/deploy-pages|actions\/upload-pages-artifact/);

  const pages=readFileSync('.github/workflows/pages.yml','utf8');
  assert.match(pages,/workflow_run:\s*\n\s*workflows: \["Refresh routed feed"\]/);
  assert.match(pages,/branches: \["main"\]/);
  assert.match(pages,/github\.event\.workflow_run\.conclusion == 'success'/);
  assert.match(pages,/python scripts\/build-public\.py --output/);
  assert.match(pages,/actions\/deploy-pages@/);
  assert.doesNotMatch(pages,/path: \.\s*$/m);
});

test('the refresh workflow is named as pages.yml expects', () => {
  const refresh=readFileSync('.github/workflows/refresh-routed-feed.yml','utf8');
  assert.match(refresh,/^name: Refresh routed feed$/m);
});

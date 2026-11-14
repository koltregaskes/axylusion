import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

test('bot feed commits explicitly request the existing legacy Pages build', () => {
  const workflow=readFileSync('.github/workflows/refresh-routed-feed.yml','utf8');
  assert.match(workflow,/pages: write/);
  const request=workflow.slice(workflow.indexOf('- name: Request the existing Pages build'));
  assert.match(request,/steps\.commit\.outputs\.committed == 'true' && github\.ref == 'refs\/heads\/main'/);
  assert.match(request,/gh api --method POST "repos\/\$\{GITHUB_REPOSITORY\}\/pages\/builds"/);
  assert.ok(workflow.indexOf('- name: Push the refreshed feed')<workflow.indexOf('- name: Request the existing Pages build'));
  assert.doesNotMatch(workflow,/actions\/deploy-pages|actions\/upload-pages-artifact/);
});

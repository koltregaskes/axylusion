import {test} from 'node:test';
import assert from 'node:assert/strict';
import {assessSample,summarize} from '../scripts/performance-result.mjs';
test('missing measurements cannot pass as zero',()=>{
  for(const lcpMs of [null,undefined,0,NaN]) assert.equal(assessSample({lcpMs,cls:0}).status,'unverified');
  assert.equal(assessSample({lcpMs:2000,cls:null}).status,'unverified');
  assert.equal(summarize([]),'unverified');
});
test('thresholds and failed resources block a passing receipt',()=>{
  const clean={lcpMs:2500,cls:0.1,failedRequests:0,httpErrors:0};
  assert.equal(assessSample(clean).status,'passed');
  for(const delta of [{lcpMs:2501},{cls:0.101},{failedRequests:1},{httpErrors:1}]) assert.equal(assessSample({...clean,...delta}).status,'failed');
  assert.equal(summarize([{status:'passed'},{status:'unverified'}]),'unverified');
  assert.equal(summarize([{status:'passed'},{status:'failed'}]),'failed');
});

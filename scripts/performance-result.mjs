export function assessSample(sample) {
  const complete = Number.isFinite(sample.lcpMs) && sample.lcpMs > 0 && Number.isFinite(sample.cls) && sample.cls >= 0;
  return {...sample, status: !complete ? 'unverified' : sample.failedRequests || sample.httpErrors || sample.lcpMs > 2500 || sample.cls > 0.1 ? 'failed' : 'passed'};
}
export function summarize(samples) {
  if (!samples.length) return 'unverified';
  return samples.some(s => s.status === 'failed') ? 'failed' : samples.some(s => s.status !== 'passed') ? 'unverified' : 'passed';
}

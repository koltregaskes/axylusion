// Explicit, bounded final-host measurement. No server, schedule or publication.
import {assessSample, summarize} from './performance-result.mjs';
const args = process.argv.slice(2);
if (args.length !== 2 || args[0] !== '--base-url') throw Error('Usage: node scripts/measure-mobile-performance.mjs --base-url https://axylusion.com');
const base = new URL(args[1]);
if (base.protocol !== 'https:' || !['axylusion.com','www.axylusion.com'].includes(base.hostname) || base.username || base.password || base.port || base.search || base.hash || base.pathname !== '/') throw Error('Use the approved HTTPS site origin only');
const {chromium} = await import('playwright');
const browser = await chromium.launch({channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge'});
const samples = [];
try {
  for (const path of ['index.html','gallery.html','news.html']) for (let run = 1; run <= 3; run++) {
    const context = await browser.newContext({viewport:{width:390,height:844}, deviceScaleFactor:1, isMobile:true, hasTouch:true, serviceWorkers:'block'});
    try {
      const page = await context.newPage();
      const cdp = await context.newCDPSession(page);
      await cdp.send('Network.enable');
      await cdp.send('Network.emulateNetworkConditions', {offline:false,latency:150,downloadThroughput:200000,uploadThroughput:93750});
      await cdp.send('Emulation.setCPUThrottlingRate', {rate:4});
      await page.addInitScript(() => {
        window.__performanceSample = {lcpMs:null,cls:0,supported:[]};
        for (const type of ['largest-contentful-paint','layout-shift']) {
          if (!PerformanceObserver.supportedEntryTypes.includes(type)) continue;
          window.__performanceSample.supported.push(type);
          new PerformanceObserver(list => {
            for (const entry of list.getEntries()) {
              if (type === 'largest-contentful-paint') window.__performanceSample.lcpMs = entry.startTime;
              else if (!entry.hadRecentInput) {
                const state = window.__performanceSample;
                if (!state.windowStart || entry.startTime - state.lastShift > 1000 || entry.startTime - state.windowStart > 5000) {state.windowStart=entry.startTime;state.windowScore=0;}
                state.windowScore += entry.value; state.lastShift=entry.startTime;
                state.cls = Math.max(state.cls, state.windowScore);
              }
            }
          }).observe({type, buffered:true});
        }
      });
      let failedRequests=0, httpErrors=0;
      page.on('requestfailed', () => failedRequests++);
      page.on('response', response => {if (response.status() >= 400) httpErrors++;});
      try {
        await page.goto(new URL(path,base).href, {waitUntil:'load',timeout:60000});
        // Fixed bounded observation window; no network-idle loop or user interaction.
        await page.waitForTimeout(5000);
        const metrics = await page.evaluate(() => {
          const state=window.__performanceSample;
          const resources=performance.getEntriesByType('resource').map(r=>({host:new URL(r.name).host,type:r.initiatorType,transferBytes:r.transferSize || null,encodedBytes:r.encodedBodySize || null}));
          const nav=performance.getEntriesByType('navigation')[0];
          return {lcpMs:state.lcpMs,cls:state.supported.includes('layout-shift')?state.cls:null,documentTransferBytes:nav?.transferSize || null,resources,images:[...document.images].map(i=>({loaded:i.complete&&i.naturalWidth>0,loading:i.loading,srcset:!!i.srcset,sizes:!!i.sizes,width:i.naturalWidth,height:i.naturalHeight}))};
        });
        samples.push(assessSample({path,run,...metrics,failedRequests,httpErrors}));
      } catch { samples.push({path,run,status:'unverified',reason:'Navigation or measurement failed',failedRequests,httpErrors}); }
    } finally {await context.close();}
  }
} finally {await browser.close();}
const status=summarize(samples);
console.log(JSON.stringify({measuredAt:new Date().toISOString(),origin:base.origin,status,profile:{viewport:'390x844',latencyMs:150,downloadBytesPerSecond:200000,cpuSlowdown:4,postLoadObservationMs:5000,coldContext:true},limits:'Lab samples, not field Core Web Vitals. Cross-origin sizes without Timing-Allow-Origin are null/unknown. Lazy offscreen images are not required to load. No scroll or gallery-interaction coverage.',samples},null,2));
if(status !== 'passed') process.exitCode=1;

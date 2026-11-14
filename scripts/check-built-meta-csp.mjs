import {chromium} from 'playwright';
import {execFileSync} from 'node:child_process';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
import assert from 'node:assert/strict';
import {installCspCapture,readCspViolations} from './csp-check.mjs';
const root=resolve('.'), file=resolve('music.html'), original=await readFile(file,'utf8');
const meta=/<meta\b(?=[^>]*http-equiv=["']Content-Security-Policy["'])[^>]*>/gi;
assert.equal([...original.matchAll(meta)].length,1,'Built music page must contain exactly one meta CSP');
const planted=original.replace('</body>','<script>globalThis.__builtInlineRan=true</script></body>');
const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'msedge'});
try {
 for(const mode of ['clean','planted','without-meta']){
  // Change the actual built file, not a synthetic CSP header or harness-only HTML response.
  await writeFile(file,mode==='clean'?original:mode==='planted'?planted:planted.replace(meta,''));
  if(mode==='without-meta')assert.throws(()=>execFileSync('python',['scripts/meta_csp.py'],{stdio:'pipe'}),error=>error.status!==0&&String(error.stderr).includes('music.html'),'Coverage gate must reject a built page without meta CSP');
  const context=await browser.newContext();
  await context.addInitScript(installCspCapture);
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.origin!=='https://axylusion.com')return route.abort();
   const asset=resolve(root,'.'+url.pathname);
   if(!asset.startsWith(root+sep))return route.abort();
   try {await route.fulfill({body:await readFile(asset),contentType:({'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.json':'application/json'})[extname(asset)]||'application/octet-stream'});}
   catch {await route.fulfill({status:404,body:''});}
  });
  try {
   const page=await context.newPage();
   const response=await page.goto('https://axylusion.com/music.html',{waitUntil:'networkidle',timeout:20000});
   assert.equal(response.headers()['content-security-policy'],undefined,'Test must not inject a CSP header');
   if(mode==='planted')await page.waitForFunction(()=>globalThis.__launchCspViolations.length>0,null,{timeout:5000});
   const violations=await page.evaluate(readCspViolations);
   const ran=await page.evaluate(()=>globalThis.__builtInlineRan===true);
   assert.equal(ran,mode==='without-meta',mode+': inline script execution');
   assert.equal(violations.length>0,mode==='planted',mode+': CSP listener');
   if(mode==='planted')assert(violations.some(v=>v.blocked==='inline'&&v.directive.startsWith('script-src')));
   console.log('Built music.html '+mode+': script ran='+ran+', CSP violations='+violations.length+', no response CSP header.');
  } finally {await context.close();}
 }
} finally {await writeFile(file,original);await browser.close();}
assert.equal(await readFile(file,'utf8'),original,'Restore built page after planted controls');

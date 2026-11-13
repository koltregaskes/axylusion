import { chromium } from 'playwright';
import { readFile, readdir } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
const root = resolve('.');
async function pages(dir = '') {
  const found = [];
  for (const entry of await readdir(resolve(root, dir), { withFileTypes: true })) {
    if (entry.name.startsWith('.') || ['node_modules', 'docs', 'tests', 'scripts'].includes(entry.name)) continue;
    const name = dir + entry.name;
    if (entry.isDirectory()) found.push(...await pages(name + '/'));
    else if (name.endsWith('.html')) found.push(name);
  }
  return found;
}
const routes = await pages();
if (!routes.length) throw Error('No routes discovered');
const axe = await readFile('node_modules/axe-core/axe.min.js', 'utf8');
const browser = await chromium.launch(process.env.LAUNCH_BROWSER_PATH ? { executablePath: process.env.LAUNCH_BROWSER_PATH } : {});
const failures = [];
try {
  for (const width of [320, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, serviceWorkers: 'block' });
    await context.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== 'https://axylusion.com') return route.abort();
      if (url.pathname === '/__launch-axe.js') return route.fulfill({ body: axe, contentType: 'text/javascript' });
      const file = resolve(root, '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
      if (!file.startsWith(root + sep) || url.pathname.split('/').some(p => p.startsWith('.'))) return route.fulfill({ status: 403, body: '' });
      const mime = { '.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.json':'application/json', '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.webp':'image/webp' };
      try { await route.fulfill({ body: await readFile(file), contentType: mime[extname(file)] || 'application/octet-stream' }); }
      catch { await route.fulfill({ status: 404, body: '' }); }
    });
    for (const path of routes) {
      const page = await context.newPage();
      await page.goto('https://axylusion.com/' + path, { waitUntil: 'networkidle' });
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all(document.getAnimations().filter(a => a.effect.getTiming().iterations !== Infinity).map(a => a.finished.catch(() => {}))); });
      await page.addScriptTag({ url: 'https://axylusion.com/__launch-axe.js' });
      const serious = await page.evaluate(async () => (await axe.run()).violations.filter(v => ['serious', 'critical'].includes(v.impact)).map(v => ({ id: v.id, count: v.nodes.length, nodes: v.nodes.map(n => ({ target: n.target, reason: n.failureSummary })) })));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (serious.length || overflow) failures.push({ path, width, serious, overflow, wide: overflow ? await page.evaluate(() => [...document.querySelectorAll('*')].filter(e => e.getBoundingClientRect().right > innerWidth + 1).slice(0,10).map(e => ({ tag: e.tagName, cls: e.className }))) : [] });
      await page.close();
    }
    await context.close();
  }
} finally { await browser.close(); }
console.log(JSON.stringify({ routes: routes.length, widths: [320,1280], failures }, null, 2));
if (failures.length) process.exitCode = 1;
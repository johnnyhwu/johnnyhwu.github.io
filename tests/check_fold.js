#!/usr/bin/env node
/*
 * Browser check for the site's `fold` shortcode (layouts/_shortcodes/fold.html): every .details block that is
 * NOT an open admonition must start collapsed, expand on a click on its title, and collapse again on a second
 * click, in both languages at a desktop and a phone width.
 *
 * Usage (after a build into .tools/public, see hugo-build.md):
 *   .claude/skills/hugo-publisher/scripts/node.sh tests/check_fold.js <section>/<slug> [--root .tools/public]
 * Exit 0 = pass, 1 = fail, 2 = Playwright missing (fold NOT checked).
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function loadPlaywright() {
  const tries = ['playwright'];
  try { tries.push(path.join(execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(), 'playwright')); } catch (e) {}
  tries.push('/opt/node22/lib/node_modules/playwright');
  for (const t of tries) { try { return require(t); } catch (e) {} }
  return null;
}

const args = process.argv.slice(2);
const rootIdx = args.indexOf('--root');
const root = path.resolve(rootIdx >= 0 ? args[rootIdx + 1] : '.tools/public');
const slugPath = args.find((a, i) => !a.startsWith('--') && (rootIdx < 0 || i !== rootIdx + 1));
if (!slugPath) { console.error('usage: check_fold.js <section>/<slug> [--root dir]'); process.exit(2); }
const pw = loadPlaywright();
if (!pw) { console.error('SKIPPED: playwright is not installed; fold NOT checked.'); process.exit(2); }

const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf' };
const server = http.createServer((req, res) => {
  let p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (p.endsWith(path.sep) || (fs.existsSync(p) && fs.statSync(p).isDirectory())) p = path.join(p, 'index.html');
  fs.readFile(p, (err, buf) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); res.end(buf);
  });
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await pw.chromium.launch({ args: ['--no-sandbox'] });
  let failed = 0, checked = 0;
  for (const [lang, prefix] of [['zh-tw', ''], ['en', '/en']]) {
    for (const [label, width] of [['desktop', 1280], ['phone', 390]]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.goto(`${base}${prefix}/${slugPath}/`, { waitUntil: 'networkidle' });
      const n = await page.locator('.details.admonition').count();
      for (let i = 0; i < n; i++) {
        const box = page.locator('.details.admonition').nth(i);
        const wasOpen = await box.evaluate(el => el.classList.contains('open'));
        if (wasOpen) continue;                       // a normal open admonition, not a fold
        checked++;
        const content = box.locator('.details-content');
        const h = async () => (await content.boundingBox())?.height ?? 0;
        const tag = `${lang} ${label} fold #${i + 1}`;
        const h0 = await h();
        if (h0 > 2) { console.log(`FAIL ${tag}: not collapsed at load (height ${h0}px)`); failed++; continue; }
        await box.locator('.details-summary').click();
        await page.waitForTimeout(600);
        const h1 = await h();
        const open1 = await box.evaluate(el => el.classList.contains('open'));
        if (!open1 || h1 < 10) { console.log(`FAIL ${tag}: did not expand on click (open=${open1}, height ${h1}px)`); failed++; continue; }
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
        if (overflow) { console.log(`FAIL ${tag}: horizontal overflow after expanding`); failed++; continue; }
        await box.locator('.details-summary').click();
        await page.waitForTimeout(600);
        const h2 = await h();
        if (h2 > 2) { console.log(`FAIL ${tag}: did not collapse on second click (height ${h2}px)`); failed++; continue; }
        console.log(`ok   ${tag}: collapsed -> ${Math.round(h1)}px -> collapsed`);
      }
      await page.close();
    }
  }
  await browser.close(); server.close();
  if (!checked) { console.log('FAIL: no fold blocks found on the page'); process.exit(1); }
  process.exit(failed ? 1 : 0);
})();

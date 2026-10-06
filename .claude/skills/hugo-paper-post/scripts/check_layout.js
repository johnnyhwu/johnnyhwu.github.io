#!/usr/bin/env node
/*
 * Render a built post in a real browser and fail on layout breakage that
 * verify_post.py and `hugo build` cannot see, because it only happens
 * client-side (KaTeX auto-render runs in the browser, after Hugo is done).
 *
 * What it checks, for BOTH languages at a desktop and a phone width:
 *   - the page scrolls horizontally (documentElement.scrollWidth > viewport)
 *     -> FAIL, and names the elements poking out of the column
 *   - any KaTeX render error (.katex-error)                        -> FAIL
 *   - an inline formula wider than the text column, or past the viewport  -> FAIL
 *     (math with no operators has no break points, which is how a stray
 *     "$ ... $" pair turns a sentence into one unbroken run)
 *
 * Usage (after a build into .tools/public, see hugo-build.md):
 *   node .claude/skills/hugo-paper-post/scripts/check_layout.js <section>/<slug> [--root .tools/public]
 * e.g. node .claude/skills/hugo-paper-post/scripts/check_layout.js paper-intro/jev-as-a-judge
 *
 * Needs Playwright + a Chromium. It is NOT a project dependency: it is looked
 * up from the global node_modules (cloud sessions ship both, with
 * PLAYWRIGHT_BROWSERS_PATH set). If either is missing the script exits 2 with
 * a message, so a missing browser is never mistaken for a pass.
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
const slugPath = args.find((a, i) => !a.startsWith('--') && i !== rootIdx + 1);
if (!slugPath) { console.error('usage: check_layout.js <section>/<slug> [--root dir]'); process.exit(2); }

const pw = loadPlaywright();
if (!pw) { console.error('SKIPPED: playwright is not installed (npm i -g playwright); layout NOT checked.'); process.exit(2); }

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
  const launch = { args: ['--no-sandbox'] };
  const alt = process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium';
  let browser;
  try { browser = await pw.chromium.launch(launch); }
  catch (e) {
    try { browser = await pw.chromium.launch({ ...launch, executablePath: alt }); }
    catch (e2) { console.error('SKIPPED: could not launch Chromium (' + e2.message.split('\n')[0] + '); layout NOT checked.'); server.close(); process.exit(2); }
  }

  const problems = [];
  const notes = new Set();
  const pages = [['zh-tw', `/${slugPath}/`], ['en', `/en/${slugPath}/`]];
  for (const [lang, url] of pages) {
    if (!fs.existsSync(path.join(root, url, 'index.html'))) { problems.push(`${lang}: ${url} was not built under ${root}`); continue; }
    for (const width of [1280, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());   // CDNs are blocked in sandboxes; the theme bundles KaTeX locally
      await page.goto(base + url, { waitUntil: 'load' });
      await page.waitForTimeout(1500);
      const r = await page.evaluate(() => {
        // Mermaid is rendered client-side from a CDN, which this run blocks. An unrendered
        // <pre class="mermaid"> is its raw source on one very long line, so it would read as
        // a page overflow that does not exist on the live site (a mermaid post measured
        // 2880px wide here and fit the 358px phone column once mermaid really ran).
        // Hide those and report them; render-check diagrams per hugo-conventions.md.
        const unrendered = [...document.querySelectorAll('pre.mermaid')].filter(m => !m.querySelector('svg'));
        unrendered.forEach(m => { m.style.display = 'none'; });
        const vw = document.documentElement.clientWidth;
        const col = (document.querySelector('.content') || document.querySelector('article')).getBoundingClientRect().width;
        const out = { unrendered: unrendered.length, vw, scrollW: document.documentElement.scrollWidth, col, katexErrors: document.querySelectorAll('.katex-error').length, wideInline: [], poking: [] };
        for (const k of document.querySelectorAll('.content .katex')) {
          if (k.closest('.katex-display, table, pre')) continue;   // tables/code scroll on their own
          const kb = k.getBoundingClientRect();
          // wider than the column, or running past the viewport's right edge (the page
          // itself may not scroll when the theme clips it, so scrollWidth alone misses this)
          if (kb.width > col + 1 || kb.right > vw + 2) out.wideInline.push(Math.round(kb.width) + 'px: ' + k.textContent.replace(/\s+/g, ' ').slice(0, 70));
        }
        if (out.scrollW > vw + 1) {
          for (const el of document.querySelectorAll('.content *')) {
            const b = el.getBoundingClientRect();
            if (b.right > vw + 2 && !el.closest('table, pre, .katex-display, .table-wrapper, .highlight')) { out.poking.push(el.tagName.toLowerCase() + ': ' + (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60)); if (out.poking.length >= 4) break; }
          }
        }
        return out;
      });
      const tag = `${lang} @${width}px`;
      if (r.unrendered) notes.add(`${r.unrendered} mermaid diagram(s) NOT checked (CDN blocked): verify them in a browser per hugo-conventions.md, "Diagrams"`);
      if (r.scrollW > r.vw + 1) problems.push(`${tag}: page scrolls horizontally (${r.scrollW}px > ${r.vw}px). Elements past the edge: ${JSON.stringify(r.poking)}`);
      if (r.katexErrors) problems.push(`${tag}: ${r.katexErrors} KaTeX render error(s)`);
      for (const w of r.wideInline) problems.push(`${tag}: inline formula wider than the text column or past the viewport edge (${w}) -- promote to a block formula, or check for a stray literal $`);
      await page.close();
    }
  }
  await browser.close(); server.close();
  for (const n of notes) console.log('NOTE: ' + n);
  if (problems.length) { console.log('FAILED:\n' + problems.map(p => '  - ' + p).join('\n')); process.exit(1); }
  console.log(`OK: ${slugPath} has no horizontal overflow, KaTeX errors or over-wide inline formulas (zh-tw + en, 1280px + 390px)`);
})();

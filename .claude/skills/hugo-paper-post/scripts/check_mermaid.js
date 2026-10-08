#!/usr/bin/env node
/*
 * Render a built post's mermaid diagrams in a real browser and fail if any
 * does not turn into an SVG (a syntax error leaves the raw source, or a
 * "Syntax error in graph" box) or is wider than the text column.
 *
 * Why this exists: `hugo build` cannot validate mermaid (it renders client
 * side), and check_layout.js cannot either in a sandbox, because the theme
 * lazy-loads mermaid@10 from cdn.jsdelivr.net, which is blocked there (it
 * prints "N mermaid diagram(s) NOT checked"). This script fetches the same
 * mermaid major once with `npm pack` into .tools/mermaid/ and serves it to
 * the page in place of the CDN, then checks every <pre class="mermaid">.
 *
 * Usage (after a build into .tools/public, see hugo-build.md):
 *   node .claude/skills/hugo-paper-post/scripts/check_mermaid.js <section>/<slug> [--root .tools/public] [--shots dir]
 *
 * --shots <dir> also saves one PNG per diagram per language/width, so a human
 * (or you, viewing one at a time) can read the rendered labels: a clipped
 * subgraph title is a valid, error-free SVG that only a screenshot shows.
 *
 * Exit codes: 0 ok (or the post has no mermaid), 1 a diagram failed,
 * 2 could not check (no Playwright/Chromium, or mermaid could not be fetched).
 * Needs Playwright + Chromium like check_layout.js, plus `npm` for the one-time fetch.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const MERMAID_VERSION = '10.9.3'; // the theme loads mermaid@10; any 10.x serves the same API

function loadPlaywright() {
  const tries = ['playwright'];
  try { tries.push(path.join(execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(), 'playwright')); } catch (e) {}
  tries.push('/opt/node22/lib/node_modules/playwright');
  for (const t of tries) { try { return require(t); } catch (e) {} }
  return null;
}

const args = process.argv.slice(2);
const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
const root = path.resolve(opt('--root') || '.tools/public');
const shots = opt('--shots') ? path.resolve(opt('--shots')) : null;
const slugPath = args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--root' && args[i - 1] !== '--shots');
if (!slugPath) { console.error('usage: check_mermaid.js <section>/<slug> [--root dir] [--shots dir]'); process.exit(2); }

const pw = loadPlaywright();
if (!pw) { console.error('SKIPPED: playwright is not installed (npm i -g playwright); mermaid NOT checked.'); process.exit(2); }

// One-time fetch of mermaid's dist/ (kept under .tools/, which is gitignored).
const cache = path.resolve('.tools/mermaid');
const dist = path.join(cache, 'package', 'dist');
if (!fs.existsSync(path.join(dist, 'mermaid.esm.min.mjs'))) {
  try {
    fs.mkdirSync(cache, { recursive: true });
    execSync(`npm pack mermaid@${MERMAID_VERSION} --silent`, { cwd: cache, stdio: ['ignore', 'pipe', 'pipe'] });
    execSync(`tar xzf mermaid-${MERMAID_VERSION}.tgz`, { cwd: cache, stdio: 'ignore' });
  } catch (e) { console.error('SKIPPED: could not fetch mermaid with npm (' + String(e.message).split('\n')[0] + '); mermaid NOT checked.'); process.exit(2); }
}

const MIME = { '.html': 'text/html', '.js': 'application/javascript', '.mjs': 'application/javascript', '.css': 'text/css', '.json': 'application/json',
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
    catch (e2) { console.error('SKIPPED: could not launch Chromium (' + e2.message.split('\n')[0] + '); mermaid NOT checked.'); server.close(); process.exit(2); }
  }
  if (shots) fs.mkdirSync(shots, { recursive: true });

  const problems = [];
  let total = 0;
  for (const [lang, url] of [['zh-tw', `/${slugPath}/`], ['en', `/en/${slugPath}/`]]) {
    if (!fs.existsSync(path.join(root, url, 'index.html'))) { problems.push(`${lang}: ${url} was not built under ${root}`); continue; }
    for (const width of [1280, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      // Serve the theme's jsDelivr mermaid@10 requests (the entry module and its chunks) from the local copy.
      await page.route(/cdn\.jsdelivr\.net\/npm\/mermaid@10[^?#]*\/dist\//, (route) => {
        const rel = route.request().url().split('/dist/')[1].split(/[?#]/)[0];
        const f = path.join(dist, rel);
        if (!f.startsWith(dist) || !fs.existsSync(f)) return route.fulfill({ status: 404, body: '' });
        route.fulfill({ body: fs.readFileSync(f), contentType: 'application/javascript' });
      });
      await page.goto(base + url, { waitUntil: 'networkidle' });
      await page.waitForFunction(() => [...document.querySelectorAll('pre.mermaid')].every(m => m.querySelector('svg') || /error/i.test(m.textContent)), null, { timeout: 15000 }).catch(() => {});
      const info = await page.$$eval('pre.mermaid', els => els.map(e => {
        const col = e.closest('.content, article, main') || document.body;
        return { svg: !!e.querySelector('svg'), syntaxError: /syntax error/i.test(e.textContent) || !!e.querySelector('svg[aria-roledescription="error"]'), width: Math.round(e.getBoundingClientRect().width), scrollW: e.scrollWidth, col: Math.round(col.getBoundingClientRect().width), vw: window.innerWidth };
      }));
      total += info.length;
      info.forEach((d, i) => {
        const tag = `${lang} @${width}px diagram #${i + 1}`;
        // A syntax error still yields an <svg> (mermaid's "bomb" error graphic), so test for it first.
        if (d.syntaxError) problems.push(`${tag}: mermaid syntax error`);
        else if (!d.svg) problems.push(`${tag}: did not render to an SVG`);
        else if (d.scrollW > d.width + 1) problems.push(`${tag}: content wider than its box (${d.scrollW}px > ${d.width}px)`);
      });
      if (shots) {
        const els = await page.$$('pre.mermaid');
        for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: path.join(shots, `${slugPath.replace(/\//g, '-')}-${lang}-${width}-${i + 1}.png`) });
      }
      await page.close();
    }
  }
  await browser.close(); server.close();
  if (problems.length) { console.log('FAILED:\n' + problems.map(p => '  - ' + p).join('\n')); process.exit(1); }
  console.log(total ? `OK: ${slugPath}: every mermaid diagram renders (zh-tw + en, 1280px + 390px; ${total / 4} per language)` : `OK: ${slugPath} has no mermaid diagrams`);
  if (total && !shots) console.log('NOTE: no clipping/legibility check without --shots <dir>; view one screenshot per diagram (see hugo-conventions.md, "Diagrams").');
})();

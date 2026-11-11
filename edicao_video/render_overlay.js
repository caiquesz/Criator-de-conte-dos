// Renderiza o overlay (legendas + motion) quadro a quadro em PNG com transparência.
// uso: node render_overlay.js <outDir> [workers] [frames separados por vírgula]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const outDir = process.argv[2];
  const workers = parseInt(process.argv[3] || '4', 10);
  const only = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
  fs.mkdirSync(outDir, { recursive: true });
  const tl = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
  fs.writeFileSync(path.join(__dirname, 'timeline.js'), 'window.TL = ' + JSON.stringify(tl) + ';');
  const frames = only || [...Array(tl.nframes).keys()];
  const browser = await chromium.launch();
  const url = 'file://' + path.join(__dirname, 'overlay.html');
  let next = 0, done = 0;
  const t0 = Date.now();
  async function worker() {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    await page.goto(url);
    await page.evaluate(() => window.__ready);
    const stage = await page.$('#stage');
    while (next < frames.length) {
      const f = frames[next++];
      await page.evaluate(fr => render(fr), f);
      await stage.screenshot({ path: path.join(outDir, String(f).padStart(5, '0') + '.png'), omitBackground: true });
      done++;
      if (done % 100 === 0) console.log(`${done}/${frames.length}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    }
    await page.close();
  }
  await Promise.all([...Array(workers)].map(worker));
  await browser.close();
  console.log(`ok ${frames.length} frames em ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})();

// Renderiza o motion quadro a quadro.  uso: node render.js <feed|reels> <outDir> [workers] [frames,separados]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const fmt = process.argv[2] || 'feed', outDir = process.argv[3];
  const workers = parseInt(process.argv[4] || '4', 10);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const url = 'file://' + path.join(__dirname, 'index.html') + '?fmt=' + fmt + (process.env.BG ? '&bg=' + process.env.BG : '');
  const probe = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await probe.goto(url);
  const info = await probe.evaluate(() => window.__ready);
  await probe.close();
  const FPS = 30, total = Math.round(info.dur * FPS);
  const frames = process.argv[5] ? process.argv[5].split(',').map(Number) : [...Array(total).keys()];
  let next = 0;
  async function worker() {
    const page = await browser.newPage({ viewport: { width: info.W, height: info.H } });
    await page.goto(url);
    await page.evaluate(() => window.__ready);
    const stage = await page.$('#stage');
    while (next < frames.length) {
      const f = frames[next++];
      await page.evaluate(t => render(t), f / FPS);
      await stage.screenshot({ path: path.join(outDir, String(f).padStart(5, '0') + '.png') });
    }
    await page.close();
  }
  await Promise.all([...Array(workers)].map(worker));
  await browser.close();
  console.log(`ok ${fmt}: ${frames.length} quadros ${info.W}x${info.H}`);
})();

// Efeito de papel amassando: tira o "print" da folha no instante do efeito e renderiza a bola 3D quadro a quadro.
// uso: node render_crumple.js <outDir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const outDir = process.argv[2];
  fs.mkdirSync(outDir, { recursive: true });
  const tl = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
  fs.writeFileSync(path.join(__dirname, 'timeline.js'), 'window.TL = ' + JSON.stringify(tl) + ';');
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const f0 = Math.round(tl.crStart * tl.fps);
  // 1) print da folha (estado no instante do amassado, sem legenda)
  const pg = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto('file://' + path.join(__dirname, 'overlay.html'));
  await pg.evaluate(() => window.__ready);
  await pg.evaluate(fr => render(fr, { paperOnly: true }), f0);
  const snap = path.join(outDir, 'print_folha.png');
  await (await pg.$('#stage')).screenshot({ path: snap });
  await pg.close();
  // 2) bola de papel
  const cp = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await cp.goto('file://' + path.join(__dirname, 'crumple.html'));
  await cp.evaluate(() => window.__ready);
  await cp.evaluate(u => setTexture(u), 'file://' + snap);
  const n1 = Math.round((tl.crDur + tl.tossDur) * tl.fps) + 1;
  const canvas = await cp.$('#c');
  for (let k = 0; k <= n1; k++) {
    const t = k / tl.fps;
    const p = Math.min(1, t / tl.crDur);
    const toss = Math.max(0, (t - tl.crDur) / tl.tossDur);
    await cp.evaluate(([a, b]) => draw(a, b), [p, toss]);
    await canvas.screenshot({ path: path.join(outDir, String(f0 + k).padStart(5, '0') + '.png'), omitBackground: true });
  }
  await browser.close();
  console.log(`ok amassado: frames ${f0}..${f0 + n1}`);
})();

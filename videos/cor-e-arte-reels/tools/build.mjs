// Gera a edição HyperFrames a partir de edit.json + transcrição por palavra.
//   node tools/build.mjs [pasta-do-projeto]
// Escreve: index.html, compositions/titles.html, compositions/captions.html, compositions/fx.html
//
// Estilo medido nas referências (ver STYLE.md):
//   legendas  — Poppins 600, pequenas, corte seco (sem animação), 2–4 palavras, na altura do peito
//   títulos   — Poppins Bold com tracking bem fechado + Playfair Display Italic grande, entrelinha
//               negativa; cada palavra entra com desfoque (blur-rise / blur) ou máquina de escrever
//   zoom      — punch-in seco no vídeo junto com a entrada do título
//   cortes    — flash branco de 1–2 frames, flash de luz quente, ou silhueta branca + flash
//   som       — clique duplo de mouse em cada entrada de título e nos flashes; whoosh nas transições
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const dir = path.resolve(process.argv[2] || ".");
const edit = JSON.parse(fs.readFileSync(path.join(dir, "edit.json"), "utf8"));
const words = JSON.parse(fs.readFileSync(path.join(dir, edit.transcript), "utf8"));

const W = 1080;
const H = 1920;
const FPS = 30;
const F = 1 / FPS;
const r3 = (n) => Math.round(n * 1000) / 1000;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const fix = edit.fix || {};
const wordById = new Map(words.map((w, i) => [w.id, { ...w, i, text: fix[w.id] ?? w.text }]));
const wordAt = (id) => {
  const w = wordById.get(id);
  if (!w) throw new Error(`palavra ${id} não existe na transcrição`);
  return w;
};

const probe = (file) =>
  parseFloat(
    execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path.join(dir, file)])
      .toString()
      .trim(),
  );
const videoDur = edit.video.duration ?? probe(edit.video.src);
const D = Math.floor(videoDur * FPS) / FPS; // nunca passar do fim do arquivo
const clampEnd = (t) => Math.min(t, D);

// ---------- fontes (cada arquivo precisa declarar as suas) ----------
const FONT_FACES = `
      @font-face { font-family: "Poppins"; font-weight: 500; src: url("assets/fonts/Poppins-500.woff2") format("woff2"); }
      @font-face { font-family: "Poppins"; font-weight: 600; src: url("assets/fonts/Poppins-600.woff2") format("woff2"); }
      @font-face { font-family: "Poppins"; font-weight: 700; src: url("assets/fonts/Poppins-700.woff2") format("woff2"); }
      @font-face { font-family: "Poppins"; font-weight: 800; src: url("assets/fonts/Poppins-800.woff2") format("woff2"); }
      @font-face { font-family: "Playfair Display"; font-style: normal; font-weight: 400 900; src: url("assets/fonts/PlayfairDisplay-VF.woff2") format("woff2"); }
      @font-face { font-family: "Playfair Display"; font-style: italic; font-weight: 400 900; src: url("assets/fonts/PlayfairDisplay-Italic-VF.woff2") format("woff2"); }`;

// ---------- sons ----------
// pico de cada arquivo (medido com `hyperframes audio --json`): o som entra 1 frame depois da imagem
const SFX = {
  click: [
    { src: "assets/sfx/click-1.mp3", peak: 0.077 },
    { src: "assets/sfx/click-2.mp3", peak: 0.069 },
    { src: "assets/sfx/click-3.mp3", peak: 0.076 },
  ],
  whoosh: [
    { src: "assets/sfx/whoosh-1.mp3", peak: 0.162 },
    { src: "assets/sfx/whoosh-2.mp3", peak: 0.176 },
    { src: "assets/sfx/whoosh-3.mp3", peak: 0.15 },
  ],
  pop: [{ src: "assets/sfx/pop.mp3", peak: 0.12 }],
};
const VOL = { click: 1, whoosh: 0.6, pop: 0.5, ...(edit.sfxVolume || {}) };
const rot = { click: 0, whoosh: 0, pop: 0 };
const cues = [];
const cue = (name, t, vol) => {
  if (cues.some((c) => c.name === name && Math.abs(c.t - t) < 0.12)) return; // sem cliques empilhados
  const take = SFX[name][rot[name]++ % SFX[name].length];
  take.dur ??= probe(take.src);
  const start = r3(Math.max(0, t + F - take.peak));
  cues.push({ name, t, src: take.src, start, end: Math.min(D, start + take.dur), vol: vol ?? VOL[name] });
};

// ---------- títulos (gancho, destaques, seções) ----------
const ENTER = {
  // referência 3: sobe de baixo, desfocado → nítido
  "blur-rise": (sel, t, size) =>
    `tl.fromTo(${sel}, { opacity: 0, y: ${Math.round(size * 0.32)}, filter: "blur(16px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.24, ease: "power3.out" }, ${r3(t)});`,
  // referência 2: só desfoque, sem deslocamento
  blur: (sel, t) =>
    `tl.fromTo(${sel}, { opacity: 0, scale: 1.06, filter: "blur(14px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "power2.out" }, ${r3(t)});`,
  cut: (sel, t) => `tl.set(${sel}, { opacity: 1 }, ${r3(t)});`,
};
const STYLE_CLASS = { sans: "sans", "sans-sm": "sans sm", serif: "serif", "serif-up": "serif up" };

const titles = (edit.titles || []).map((ti, n) => {
  const id = ti.id || `t${n}`;
  const enter = ti.enter || "blur-rise";
  const lead = ti.lead ?? 0.04; // a palavra aparece um tiquinho antes de ser falada
  const tokens = [];
  ti.lines.forEach((line, li) =>
    line.tokens.forEach((tk, ki) => {
      const appear = tk.at ?? wordAt(tk.w).start - lead;
      tokens.push({ ...tk, li, ki, appear: Math.max(0.05, appear), kid: `${id}-${li}-${ki}` });
    }),
  );
  const first = Math.min(...tokens.map((t) => t.appear));
  const lastWord = ti.to ? wordAt(ti.to).end : Math.max(...tokens.map((t) => (t.w ? wordAt(t.w).end : t.appear + 0.4)));
  const start = ti.start ?? first;
  const end = clampEnd(ti.end ?? lastWord + (ti.hold ?? 0.45));
  return { ...ti, id, enter, tokens, start: r3(start), end: r3(end) };
});

// palavras que viram título não aparecem como legenda
const suppressed = new Set();
for (const ti of titles) {
  if (!ti.from || !ti.to) continue;
  for (let i = wordAt(ti.from).i; i <= wordAt(ti.to).i; i++) suppressed.add(words[i].id);
}

const titleMarkup = [];
const titleScript = [];
titles.forEach((ti, n) => {
  const lines = ti.lines
    .map((line, li) => {
      const toks = line.tokens
        .map((tk, ki) => {
          const t = ti.tokens.find((x) => x.li === li && x.ki === ki);
          const cls = STYLE_CLASS[tk.s || "sans"];
          const style = [`font-size:${tk.size}px`];
          if (tk.dx) style.push(`margin-left:${tk.dx}px`);
          if (tk.dy) style.push(`top:${tk.dy}px`);
          if (tk.opacity) style.push(`--tk-o:${tk.opacity}`);
          const text = tk.t ?? wordAt(tk.w).text;
          const inner =
            ti.enter === "type"
              ? [...text].map((ch, ci) => `<span class="ch" id="${t.kid}-c${ci}">${ch === " " ? "&nbsp;" : esc(ch)}</span>`).join("")
              : esc(text);
          return `<span class="tk ${cls}" id="${t.kid}" style="${style.join(";")}">${inner}</span>`;
        })
        .join("");
      const ls = [`justify-content:${line.justify || ti.align || "center"}`];
      if (li > 0) ls.push(`margin-top:${line.gap ?? -18}px`);
      if (line.gapX != null) ls.push(`gap:${line.gapX}px`);
      if (line.width) ls.push(`width:${line.width}px`, "margin-left:auto", "margin-right:auto");
      return `          <div class="tl-line" style="${ls.join(";")}">${toks}</div>`;
    })
    .join("\n");
  const pad = ti.padX ?? 80;
  titleMarkup.push(`      <div id="${ti.id}" class="clip title" data-start="${ti.start}" data-duration="${r3(ti.end - ti.start)}" data-track-index="${n % 4}" data-layout-allow-overlap>
        <div class="title-in" id="${ti.id}-in" style="top:${ti.y}px;padding:0 ${pad}px">
${lines}
        </div>
      </div>`);

  titleScript.push(`      // ${ti.id}`);
  const appearTimes = [];
  for (const tk of ti.tokens) {
    const sel = `"#${tk.kid}"`;
    if (ti.enter === "type") {
      const text = tk.t ?? wordAt(tk.w).text;
      const per = ti.typeSpeed ?? 0.045;
      titleScript.push(`      tl.set("#${tk.kid}", { opacity: 1 }, ${r3(tk.appear)});`);
      [...text].forEach((_, ci) =>
        titleScript.push(`      tl.set("#${tk.kid}-c${ci}", { opacity: 1 }, ${r3(tk.appear + ci * per)});`),
      );
    } else {
      titleScript.push(`      ${ENTER[ti.enter](sel, tk.appear, tk.size)}`);
    }
    appearTimes.push(tk.appear);
  }
  if ((ti.exit || "blur") === "blur") {
    titleScript.push(
      `      tl.to("#${ti.id}-in", { opacity: 0, filter: "blur(10px)", duration: 0.16, ease: "power2.in" }, ${r3(ti.end - 0.18)});`,
    );
  }
  // sons: clique em cada entrada (refs 2 e 3) ou só na primeira (ref 1)
  const mode = ti.sfx ?? "each";
  const uniq = [...new Set(appearTimes.map((t) => r3(t)))].sort((a, b) => a - b);
  if (mode === "each") uniq.forEach((t) => cue("click", t));
  else if (mode === "first") cue("click", uniq[0]);
  else if (mode === "whoosh") cue("whoosh", uniq[0]);
});

// ---------- legendas ----------
const C = { y: 1210, size: 44, maxWords: 4, maxChars: 24, pause: 0.25, ...(edit.captions || {}) };
const titleWindows = titles.map((t) => [t.start, t.end]);
const insideTitle = (t) => titleWindows.some(([a, b]) => t >= a - 0.05 && t < b);
const groups = [];
let cur = null;
words.forEach((raw, i) => {
  const w = wordAt(raw.id);
  if (suppressed.has(raw.id) || insideTitle(w.start)) {
    cur = null;
    return;
  }
  const prev = i > 0 ? wordAt(words[i - 1].id) : null;
  const text = cur ? `${cur.text} ${w.text}` : w.text;
  const breakHere =
    !cur ||
    cur.words.length >= C.maxWords ||
    text.length > C.maxChars ||
    /[.,!?;:…]$/.test(prev?.text || "") ||
    w.start - prev.end >= C.pause ||
    (edit.breakBefore || []).includes(raw.id);
  if (breakHere) {
    cur = { words: [w], text: w.text };
    groups.push(cur);
  } else {
    cur.words.push(w);
    cur.text = text;
  }
});
groups.forEach((g, i) => {
  g.start = Math.max(0.1, g.words[0].start - 0.03);
  const lastEnd = g.words[g.words.length - 1].end;
  const next = groups[i + 1];
  let end = lastEnd + 0.35;
  if (next && next.words[0].start - lastEnd < 0.7) end = next.words[0].start - 0.03; // emenda sem buraco
  const nextTitle = titles.find((t) => t.start > g.start);
  if (nextTitle) end = Math.min(end, nextTitle.start);
  g.end = clampEnd(end);
});
const capGroups = groups.filter((g) => g.end - g.start > 0.06);
const captionMarkup = capGroups
  .map(
    (g, i) =>
      `      <div id="cap-${i}" class="clip cap" data-start="${r3(g.start)}" data-duration="${r3(g.end - g.start)}" data-track-index="${i % 2}"><span class="cap-t">${esc(g.text)}</span></div>`,
  )
  .join("\n");

// ---------- transições ----------
const fxMarkup = [];
const fxScript = [];
const camScript = [];
(edit.transitions || []).forEach((tr, i) => {
  const t = tr.t; // instante do corte no vídeo
  const id = `fx-${i}`;
  if (tr.type === "flash" || tr.type === "silhouette") {
    // ref 2: 1 frame branco antes do corte e meio frame depois
    const s = r3(t - 2 * F);
    fxMarkup.push(`      <div id="${id}" class="clip fx-flash" data-start="${s}" data-duration="${r3(4 * F)}" data-track-index="${i % 2}"><div class="fx-fill" id="${id}-f"></div></div>`);
    fxScript.push(`      tl.set("#${id}-f", { opacity: ${tr.type === "silhouette" ? 0 : 0.55} }, ${s});`);
    fxScript.push(`      tl.set("#${id}-f", { opacity: 1 }, ${r3(t - F)});`);
    fxScript.push(`      tl.set("#${id}-f", { opacity: 0.45 }, ${r3(t)});`);
    fxScript.push(`      tl.set("#${id}-f", { opacity: 0 }, ${r3(t + F)});`);
    if (tr.type === "silhouette") {
      // ref 3: a pessoa vira silhueta branca por 1 frame antes do flash
      camScript.push(`      tl.set("#cam-cut", { filter: "brightness(0) invert(1)" }, ${s});`);
      camScript.push(`      tl.set("#cam-cut", { filter: "none" }, ${r3(t - F)});`);
    }
    cue("click", t - F);
    if (tr.whoosh !== false) cue("whoosh", t);
  } else if (tr.type === "leak") {
    // ref 1: estouro de luz quente (~8 frames) atravessando o corte
    const s = r3(t - 0.16);
    fxMarkup.push(`      <div id="${id}" class="clip fx-leak" data-start="${s}" data-duration="${r3(0.42)}" data-track-index="${i % 2}"><div class="fx-glow" id="${id}-g"></div><div class="fx-core" id="${id}-c"></div></div>`);
    fxScript.push(`      tl.fromTo("#${id}-g", { opacity: 0 }, { opacity: 1, duration: 0.14, ease: "power2.in" }, ${s});`);
    fxScript.push(`      tl.fromTo("#${id}-c", { opacity: 0 }, { opacity: 0.85, duration: 0.08, ease: "power2.in" }, ${r3(t - 0.08)});`);
    fxScript.push(`      tl.to("#${id}-c", { opacity: 0, duration: 0.12, ease: "power2.out" }, ${r3(t + 0.02)});`);
    fxScript.push(`      tl.to("#${id}-g", { opacity: 0, duration: 0.22, ease: "power2.out" }, ${r3(t + 0.04)});`);
    cue("whoosh", t - 0.04);
  }
});

// ---------- zoom (punch-in seco, como na ref 3) ----------
const focus = edit.video.focus || "50% 30%";
camScript.unshift(`      tl.set(["#cam", "#cam-cut"], { scale: 1, transformOrigin: "${focus}" }, 0);`);
for (const z of edit.zooms || []) {
  const props = `{ scale: ${z.scale}${z.x ? `, x: ${z.x}` : ""}${z.y ? `, y: ${z.y}` : ""}${z.origin ? `, transformOrigin: "${z.origin}"` : ""}`;
  if (z.dur) camScript.push(`      tl.to(["#cam", "#cam-cut"], ${props}, duration: ${z.dur}, ease: "${z.ease || "power2.inOut"}" }, ${r3(z.t)});`);
  else camScript.push(`      tl.set(["#cam", "#cam-cut"], ${props} }, ${r3(z.t)});`);
}

for (const s of edit.sfx || []) cue(s.name, s.t, s.vol);
cues.sort((a, b) => a.start - b.start);

// ---------- escrita ----------
const cut = edit.cutout;
// cada som numa faixa livre (sons sobrepostos na mesma faixa geram aviso)
const laneEnds = [];
const audioMarkup = cues
  .map((c, i) => {
    let lane = laneEnds.findIndex((e) => e <= c.start);
    if (lane < 0) lane = laneEnds.push(0) - 1;
    laneEnds[lane] = c.end;
    return `      <audio id="sfx-${i}" src="${c.src}" data-start="${c.start}" data-duration="${r3(c.end - c.start)}" data-track-index="${6 + lane}" data-volume="${c.vol}"></audio>`;
  })
  .join("\n");

const index = `<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: ${W}px; height: ${H}px; overflow: hidden; background: #000; }
      #cam, #cam-cut { position: absolute; inset: 0; overflow: hidden; }
      #cam { z-index: 1; }
      #cam-cut { z-index: 3; }
      #main-video, #cutout { position: absolute; left: 0; top: 0; width: ${W}px; height: ${H}px; object-fit: cover; }
    </style>
  </head>
  <body>
    <!-- gerado por tools/build.mjs a partir de edit.json -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="${r3(D)}" data-width="${W}" data-height="${H}">
      <div id="cam">
        <video id="main-video" class="clip" src="${edit.video.src}" data-start="0" data-duration="${r3(D)}" data-track-index="0" data-has-audio="true" playsinline></video>
      </div>
      <div id="titles" data-composition-id="titles" data-composition-src="compositions/titles.html" data-start="0" data-duration="${r3(D)}" data-track-index="1" data-track-kind="graphics" data-width="${W}" data-height="${H}" style="z-index: 2"></div>
      <div id="cam-cut">${
        cut
          ? `
        <video id="cutout" class="clip" src="${cut.src}" data-start="0" data-media-start="0" data-duration="${r3(cut.end)}" data-track-index="2" muted playsinline data-layout-allow-occlusion></video>
      `
          : ""
      }</div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="${r3(D)}" data-track-index="3" data-track-kind="captions" data-width="${W}" data-height="${H}" style="z-index: 4"></div>
      <div id="fx" data-composition-id="fx" data-composition-src="compositions/fx.html" data-start="0" data-duration="${r3(D)}" data-track-index="4" data-track-kind="graphics" data-width="${W}" data-height="${H}" style="z-index: 5"></div>
${audioMarkup}
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
${camScript.join("\n")}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
`;

const titlesHtml = `<template>
  <style>${FONT_FACES}
      #root { position: absolute; inset: 0; overflow: visible; }
      .title { position: absolute; inset: 0; }
      .title-in { position: absolute; left: 0; right: 0; }
      .tl-line { display: flex; align-items: baseline; white-space: nowrap; gap: 0.18em; }
      .tk { display: inline-block; position: relative; color: #fff; opacity: 0; will-change: transform, filter, opacity;
            text-shadow: 0 4px 28px rgba(0, 0, 0, 0.22); }
      .ch { opacity: 0; }
      .sans { font-family: "Poppins", sans-serif; font-weight: 700; letter-spacing: -0.055em; line-height: 0.86; }
      .sans.sm { font-weight: 600; letter-spacing: -0.03em; }
      .serif { font-family: "Playfair Display", serif; font-style: italic; font-weight: 400; letter-spacing: -0.035em; line-height: 0.82;
               color: rgba(255, 255, 255, var(--tk-o, 0.94)); }
      .serif.up { font-style: normal; letter-spacing: -0.045em; }
  </style>
  <div id="root" data-composition-id="titles" data-width="${W}" data-height="${H}">
${titleMarkup.join("\n")}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
${titleScript.join("\n")}
      window.__timelines["titles"] = tl;
    })();
  </script>
</template>
`;

const captionsHtml = `<template>
  <style>${FONT_FACES}
      #root { position: absolute; inset: 0; }
      .cap { position: absolute; left: 0; right: 0; top: ${C.y}px; padding: 0 ${Math.round(W * 0.1)}px; text-align: center; }
      .cap-t { display: inline-block; font-family: "Poppins", sans-serif; font-weight: 600; font-size: ${C.size}px; line-height: 1.04;
               letter-spacing: -0.02em; color: #fff;
               text-shadow: 0 2px 6px rgba(0, 0, 0, 0.38), 0 0 22px rgba(0, 0, 0, 0.2); }
  </style>
  <div id="root" data-composition-id="captions" data-width="${W}" data-height="${H}">
${captionMarkup}
  </div>
  <script>
    (function () {
      // legendas entram e saem no corte seco, como nas referências
      window.__timelines["captions"] = gsap.timeline({ paused: true });
    })();
  </script>
</template>
`;

const fxHtml = `<template>
  <style>
      #root { position: absolute; inset: 0; pointer-events: none; }
      .fx-flash, .fx-leak { position: absolute; inset: 0; }
      .fx-fill { position: absolute; inset: 0; background: #f7f3ef; opacity: 0; }
      .fx-glow { position: absolute; inset: 0; opacity: 0; mix-blend-mode: screen;
                 background: radial-gradient(120% 80% at 70% 30%, rgba(255, 214, 140, 1) 0%, rgba(255, 170, 80, 0.85) 45%, rgba(255, 140, 60, 0.35) 100%); }
      .fx-core { position: absolute; inset: 0; opacity: 0; background: #fff6e4; }
  </style>
  <div id="root" data-composition-id="fx" data-width="${W}" data-height="${H}">
${fxMarkup.join("\n")}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
${fxScript.join("\n")}
      window.__timelines["fx"] = tl;
    })();
  </script>
</template>
`;

fs.mkdirSync(path.join(dir, "compositions"), { recursive: true });
fs.writeFileSync(path.join(dir, "index.html"), index);
fs.writeFileSync(path.join(dir, "compositions/titles.html"), titlesHtml);
fs.writeFileSync(path.join(dir, "compositions/captions.html"), captionsHtml);
fs.writeFileSync(path.join(dir, "compositions/fx.html"), fxHtml);

console.log(`duração ${r3(D)}s · ${titles.length} títulos · ${capGroups.length} legendas · ${(edit.transitions || []).length} transições · ${cues.length} efeitos sonoros`);
for (const g of capGroups) console.log(`  ${r3(g.start).toFixed(2)}–${r3(g.end).toFixed(2)}  ${g.text}`);

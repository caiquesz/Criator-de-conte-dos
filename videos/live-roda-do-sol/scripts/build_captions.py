"""Gera compositions/captions.html a partir de assets/transcript-words.json.

Legenda contínua minimalista: uma palavra por vez, branca, centralizada.
Os destaques (data, marca, produtos, horário) aparecem agrupados e um pouco
maiores. Rodar de novo depois de editar o transcript ou a lista de destaques:

    python3 scripts/build_captions.py
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORDS = json.loads((ROOT / "assets/transcript-words.json").read_text())
DURATION = 21.63

# Sequências faladas que viram um único bloco de destaque (por posição no transcript).
HIGHLIGHTS = [
    ["11", "de", "novembro"],
    ["Roda", "do", "Sol"],
    ["tapetes", "de", "sala"],
    ["capas", "de", "almofada"],
    ["mantas", "de", "sofá"],
    ["jogos", "de", "passadeira"],
    ["7", "horas"],
]


def clean(w: str) -> str:
    return re.sub(r"[.,!?;:]+$", "", w.strip())


words = [{"text": clean(w["w"]), "start": w["s"], "end": w["e"]} for w in WORDS]

entries = []
i = 0
while i < len(words):
    matched = None
    for seq in HIGHLIGHTS:
        n = len(seq)
        if [w["text"] for w in words[i : i + n]] == seq:
            matched = n
            break
    if matched:
        chunk = words[i : i + matched]
        entries.append(
            {"text": " ".join(w["text"] for w in chunk), "start": chunk[0]["start"], "end": chunk[-1]["end"], "hl": True}
        )
        i += matched
    else:
        w = words[i]
        entries.append({"text": w["text"], "start": w["start"], "end": w["end"], "hl": False})
        i += 1

# Janela de cada legenda: do início da palavra até o início da próxima;
# numa pausa (>= 0.3 s) some 0.2 s depois do fim da palavra.
for k, e in enumerate(entries):
    nxt = entries[k + 1]["start"] if k + 1 < len(entries) else DURATION
    gap = nxt - e["end"]
    e["show"] = max(0.1, e["start"]) if k == 0 else e["start"]
    e["hide"] = nxt if gap < 0.3 else min(nxt, e["end"] + 0.2)
    if k + 1 == len(entries):
        e["hide"] = min(DURATION - 0.02, e["end"] + 0.25)

items = []
tweens = []
for k, e in enumerate(entries):
    cid = f"cap-{k:02d}"
    dur = round(e["hide"] - e["show"], 3)
    cls = "cap clip hl" if e["hl"] else "cap clip"
    items.append(
        f'    <div id="{cid}" class="{cls}" data-start="{e["show"]:.3f}" data-duration="{dur}">'
        f'<span class="w">{e["text"]}</span></div>'
    )
    tweens.append(
        f'    tl.fromTo("#{cid} .w", {{ opacity: 0, y: 6, scale: 0.94 }}, '
        f'{{ opacity: 1, y: 0, scale: 1, duration: {0.12 if e["hl"] else 0.08}, ease: "power2.out" }}, {e["show"]:.3f});'
    )

html = f"""<template>
  <style>
    #root {{
      position: absolute;
      inset: 0;
      pointer-events: none;
    }}
    #root .cap {{
      position: absolute;
      left: 0;
      right: 0;
      top: 1236px;
      text-align: center;
      overflow: visible;
      z-index: 1;
    }}
    #root .cap .w {{
      display: inline-block;
      font-family: "Inter", sans-serif;
      font-weight: 700;
      font-size: 44px;
      line-height: 1.1;
      letter-spacing: -0.01em;
      color: var(--caption-color, #ffffff);
      text-shadow: 0 0 22px rgba(0, 0, 0, 0.55), 0 2px 6px rgba(0, 0, 0, 0.45);
      white-space: nowrap;
      transform-origin: 50% 60%;
    }}
    #root .cap.hl .w {{
      font-size: 54px;
      letter-spacing: -0.015em;
    }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(items)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tweens)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""

(ROOT / "compositions/captions.html").write_text(html)
print(f"{len(entries)} legendas -> compositions/captions.html")
for e in entries:
    print(f'{e["show"]:6.2f}-{e["hide"]:6.2f} {"*" if e["hl"] else " "} {e["text"]}')

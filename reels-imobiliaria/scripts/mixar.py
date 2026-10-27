"""Monta o áudio final sem mexer na voz: áudio original (ganho 1,0) + efeitos sonoros (+ trilha).

Uso: python3 scripts/mixar.py PASTA_DO_PROJETO VIDEO_RENDERIZADO SAIDA.mp4

Nada de normalização, compressão, limitador ou mudança de tom: o áudio que veio no
vídeo entra exatamente como está e os efeitos são somados por cima, nos mesmos
instantes e volumes que o gerador usa. A imagem do vídeo renderizado é copiada
sem recompressão. Com "trilha" no plano, a música entra por baixo da voz no nível
da referência; só a música (e os efeitos) são ajustados, e se a soma passar do
pico que o original já tinha, abaixam só eles naquele instante. No fim, tira os
extras do arquivo final e confere que o que sobra é a voz original.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from gerar import DURACAO_SFX, FPS, PICO_SFX, eventos_sfx  # noqa: E402

TAXA = 48000


def pcm(arquivo):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arquivo), "-vn", "-ac", "2", "-ar", str(TAXA),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def lufs(audio):
    """Loudness integrada (LUFS) de um trecho, medida pelo ffmpeg (ebur128)."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-",
                          "-af", "ebur128", "-f", "null", "-"], input=audio.astype(np.float32).tobytes(),
                         capture_output=True).stderr.decode()
    valores = [float(l.split()[1]) for l in log.splitlines() if l.strip().startswith("I:")]
    return valores[-1] if valores else -70.0


def trilha(pasta, plano, original):
    """Música por baixo da voz, no nível da referência (cerca de 12 dB abaixo da fala),
    subindo um pouco nas pausas longas. Só a música é ajustada; a voz fica intacta."""
    from sincronizar import trechos_de_fala
    t = plano["trilha"]
    musica = pcm(pasta / t["src"])
    a = int(t.get("inicio_trilha", 0) * TAXA)
    musica = musica[a:a + len(original)]
    if len(musica) < len(original):
        musica = np.pad(musica, ((0, len(original) - len(musica)), (0, 0)))

    trechos = trechos_de_fala(pasta / plano.get("video_original", plano["video"]))
    fala = np.concatenate([original[int(i * TAXA):int(f * TAXA)] for i, f in trechos]) if trechos else original
    alvo_fala = lufs(fala) - t.get("abaixo_da_voz_db", 12)
    ganho = 10 ** ((alvo_fala - lufs(musica)) / 20)

    # envelope: nível de fala; +sobe_db nas pausas com mais de 1,5 s, com rampas suaves
    env = np.ones(len(original))
    pausas, fim_ant = [], 0.0
    for i, f in trechos + [(len(original) / TAXA + 1, None)]:
        if i - fim_ant > 1.5:
            pausas.append((fim_ant + 0.35, i - 0.3))
        fim_ant = f if f is not None else fim_ant
    sobe = 10 ** (t.get("sobe_nas_pausas_db", 4) / 20)
    rampa = int(0.4 * TAXA)
    for i, f in pausas:
        a, b = int(i * TAXA), int(f * TAXA)
        if b - a < 2 * rampa:
            continue
        env[a:a + rampa] = np.maximum(env[a:a + rampa], np.linspace(1, sobe, rampa))
        env[a + rampa:b - rampa] = sobe
        env[b - rampa:b] = np.maximum(env[b - rampa:b], np.linspace(sobe, 1, rampa))
    fi, fo = int(t.get("fade_in", 0.5) * TAXA), int(t.get("fade_out", 2.0) * TAXA)
    env[:fi] *= np.linspace(0, 1, fi)
    env[-fo:] *= np.linspace(1, 0, fo)
    print(f"trilha: {t['src']} a partir de {t.get('inicio_trilha', 0)} s, alvo {alvo_fala:.1f} LUFS sob a fala")
    return musica * ganho * env[:, None]


def fator_teto(voz, extra, teto):
    """Ganho (0–1) só para os extras, para que voz + extras nunca passem do teto."""
    soma = np.abs(voz + extra).max(1)
    f = np.ones(len(voz))
    estoura = soma > teto
    if estoura.any():
        v = np.abs(voz[estoura]).max(1)
        e = np.abs(extra[estoura]).max(1)
        f[estoura] = np.clip((teto - v) / np.maximum(e, 1e-9), 0, 1)
        # mínimo numa janela de 10 ms seguido de média em 5 ms: suave e nunca acima do necessário
        from numpy.lib.stride_tricks import sliding_window_view as janela
        w = int(0.01 * TAXA) | 1
        f = janela(np.pad(f, w // 2, mode="edge"), w).min(1)
        k = w // 2 | 1
        f = np.convolve(np.pad(f, k // 2, mode="edge"), np.ones(k) / k, "valid")
    return f


def main():
    pasta, renderizado, saida = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3])
    plano = json.loads((pasta / "plano.json").read_text())
    original = pcm(pasta / plano.get("video_original", plano["video"]))
    extra = np.zeros_like(original)          # tudo o que é somado por cima da voz
    tem_efeito = np.zeros(len(original), bool)

    for t, som, vol in eventos_sfx(plano):
        ini = max(0.0, t - PICO_SFX.get(som, 0.08) + 1 / FPS)
        efeito = pcm(pasta / "assets" / "sfx" / f"{som}.mp3")[: int(DURACAO_SFX.get(som, 1.0) * TAXA)] * vol
        a = int(round(ini * TAXA))
        b = min(len(extra), a + len(efeito))
        extra[a:b] += efeito[: b - a]
        tem_efeito[a:b] = True

    if plano.get("trilha"):
        extra += trilha(pasta, plano, original)
        tem_efeito[:] = True

    # teto: se voz + extras passarem do pico que o original já tinha, abaixa só os extras
    pico_original = float(np.abs(original).max())
    teto = max(0.995, pico_original)
    extra *= fator_teto(original, extra, teto)[:, None]
    mix = original + extra

    pico = float(np.abs(mix).max())
    if pico > max(0.97, pico_original * 1.001):
        print(f"atenção: um efeito leva o pico a {20 * np.log10(pico):.1f} dBFS (original: "
              f"{20 * np.log10(pico_original):.1f}); baixe o volume dele em vez de comprimir")
    wav = saida.with_suffix(".mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", str(wav)], input=mix.astype(np.float32).tobytes(), check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(renderizado), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                    "-ar", str(TAXA), "-movflags", "+faststart", "-shortest", str(saida)], check=True)
    wav.unlink()

    # prova: tirando os extras, o que sobra é a voz original (só o erro do codificador AAC)
    final = pcm(saida)
    n = min(len(final), len(original))
    voz_final = final[:n] - extra[:n]
    sinal = np.sqrt(np.mean(original[:n] ** 2))
    resto = np.sqrt(np.mean((voz_final - original[:n]) ** 2))
    ganho_voz = float(np.dot(voz_final.ravel(), original[:n].ravel()) / np.dot(original[:n].ravel(), original[:n].ravel()))
    print(f"pico do mix: {20 * np.log10(pico):.1f} dBFS (original: {20 * np.log10(pico_original):.1f} dBFS)")
    print(f"voz no arquivo final: ganho {20 * np.log10(ganho_voz):+.3f} dB, "
          f"diferença para o original {20 * np.log10(resto / sinal):.1f} dB abaixo da voz")
    print("ok:", saida)


if __name__ == "__main__":
    main()

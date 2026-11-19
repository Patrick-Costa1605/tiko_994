#!/usr/bin/env python3
"""«Como surgiu o Escutismo nas Caxinas»: vídeo desenhado à mão, em tempo real, sincronizado com a voz.

    python src/render.py guioes/como_surgiu.json              # -> output/como_surgiu.mp4
    python src/render.py guioes/como_surgiu.json --png 3 12   # só imagens de teste (segundos)
"""
import argparse
import bisect
import json
import math
import multiprocessing as mp
import re
import subprocess
import sys
import time
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audio import SR, decode, ffmpeg_exe, folha, risco, tratar_voz, trim_silence, write_wav  # noqa: E402
from musica import gerar as gerar_musica  # noqa: E402
from cenas import CENAS  # noqa: E402
from config import *  # noqa: E402
from desenho import clamp, desenha_elemento, desenha_mao, ease, largura_texto, ponto_em, h01  # noqa: E402
from voz import falado, norm, sintetizar, silabas  # noqa: E402

SLIDE = 0.75                   # duração do virar de página
PRE = 0.15                     # a página nova fica visível 0,3 s antes de a voz e a mão começarem
GAP_PAG, GAP_CONT = 1.9, 0.75  # pausa entre páginas (a página fica parada ~0,7 s depois de desenhada)
PAUSA_FRASE = 0.30


# ------------------------------------------------------------------ guião -> tempos
def palavras_do_bloco(texto, pron, pal_edge, dur, off):
    ws = [{"text": w} for w in texto.split()]
    toks = [falado(w["text"], pron).split() for w in ws]
    n = sum(len(t) for t in toks)
    if len(pal_edge) == n:
        k = 0
        for w, tk in zip(ws, toks):
            a, b = pal_edge[k], pal_edge[k + len(tk) - 1]
            k += len(tk)
            w["t0"], w["t1"] = max(0.0, a["t0"] - off), min(dur, b["t1"] - off)
    else:
        print(f"  ! «{texto[:30]}…»: {len(pal_edge)} marcas vs {n} palavras; estimado por sílabas", file=sys.stderr)
        pesos = np.array([silabas(" ".join(t)) for t in toks], float)
        e = np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum()
        for w, s, t in zip(ws, e[:-1], e[1:]):
            w["t0"], w["t1"] = 0.04 + (dur - 0.08) * s, 0.04 + (dur - 0.08) * t
    last = 0.0
    for w in ws:
        w["t0"] = max(w["t0"], last)
        w["t1"] = max(w["t1"], w["t0"] + 0.08)
        last = w["t0"]
    return ws


def agenda(elems, t_ini, t_fim, palavras):
    """Distribui os elementos em sequência (uma só mão), ajustando a velocidade para acabarem com a fala."""
    def bruto(e):
        if e["k"] == "path":
            return max(0.12, e["len"] / 1700.0) * e["peso"]
        if e["k"] == "texto":
            return max(0.35, 0.065 * len(e["txt"])) * e["peso"]
        return 0.5 * e["peso"]

    anc = []
    for e in elems:
        a = e.get("ancora")
        tt = None
        if a:
            for w in palavras:
                if norm(a) in norm(w["text"]):
                    tt = w["t0"]
                    break
        anc.append(tt)

    def corre(f):
        cur, out = t_ini, []
        for j, (e, a) in enumerate(zip(elems, anc)):
            if a is not None and j > 0:                 # o 1.º elemento (o título) nunca espera pela voz
                cur = max(cur, a - 0.10)
            d = bruto(e) * f
            out.append((cur, cur + d))
            cur += d + 0.05
        return out, cur

    lo, hi = 0.25, 1.9
    for _ in range(14):
        mid = (lo + hi) / 2
        _, fim = corre(mid)
        if fim <= t_fim:
            lo = mid
        else:
            hi = mid
    return corre(lo)[0]


def construir(caminho_guiao):
    cfg = json.loads(Path(caminho_guiao).read_text(encoding="utf-8"))
    voz, pron = cfg["voz"], cfg.get("pronuncia", {})
    blocos, partes = [], []
    cur, livre = 0.35, 0.0
    for i, rb in enumerate(cfg["blocos"]):
        nova = i > 0 and not rb.get("continua")
        start = cur if i == 0 else (max(cur + GAP_PAG, livre) if nova else cur + GAP_CONT)
        frases = re.split(r"(?<=[.!?])\s+", rb["texto"].strip())
        ws, x_all, t_loc = [], [], 0.0
        for fr in frases:                                     # uma síntese por frase: entoação mais natural, pausas controladas
            spoken = " ".join(falado(w, pron) for w in fr.split())
            mp3, pal = sintetizar(spoken, voz["nome"], rb.get("velocidade", voz["velocidade"]), rb.get("tom", voz["tom"]))
            x, off = trim_silence(decode(mp3))
            dur = len(x) / SR
            for w in palavras_do_bloco(fr, pron, pal, dur, off):
                w["t0"] += start + t_loc
                w["t1"] += start + t_loc
                ws.append(w)
            partes.append((start + t_loc, x))
            t_loc += dur + (PAUSA_FRASE + (0.12 if fr.endswith("?") else 0.0))
        end = start + t_loc - PAUSA_FRASE
        folga = rb.get("folga", 0.30 if (i + 1 < len(cfg["blocos"]) and not cfg["blocos"][i + 1].get("continua")) else 0.2)
        elems = CENAS[rb["cena"]](rb.get("parte"))
        tempos = agenda(elems, start + 0.05, end + folga, ws)
        livre = max(t1 for _, t1 in tempos) + PRE + SLIDE + 0.7        # a página seguinte espera que o desenho acabe
        blocos.append({"cena": rb["cena"], "parte": rb.get("parte"), "nova": nova or i == 0, "start": start, "end": end, "words": ws,
                       "folga": folga, "elems": elems, "tempos": tempos,
                       "texto": rb["texto"], "legenda_n": rb.get("legenda_n")})
        cur = end

    # páginas e elementos agendados
    paginas = []
    for b in blocos:
        if b["nova"]:
            paginas.append({"start": b["start"], "els": []})
        for e, (t0, t1) in zip(b["elems"], b["tempos"]):
            e["t0"], e["t1"] = t0, t1
            paginas[-1]["els"].append(e)
    ultimo = max(e["t1"] for p in paginas for e in p["els"])
    total = max(blocos[-1]["end"], ultimo) + 2.2           # o cartão final fica parado ~2 s, com a música a esvanecer
    segs = sorted(((e["t0"], e["t1"], e, k) for k, p in enumerate(paginas) for e in p["els"] if e["k"] in ("path", "texto")), key=lambda s: s[0])
    return {"blocos": blocos, "paginas": paginas, "segs": segs, "total": total, "n_frames": int(math.ceil(total * FPS)), "cfg": cfg}, partes


# ------------------------------------------------------------------ áudio
def mistura(tl, partes):
    n = int(math.ceil(tl["total"] * SR)) + SR
    voz = np.zeros(n, np.float32)
    for start, x in partes:
        a = int(start * SR)
        voz[a:a + len(x)] += x
    voz = tratar_voz(voz)                                      # compressão suave, brilho e uma pitada de sala
    fx = np.zeros(n, np.float32)
    for k, (t0, t1, e, pg) in enumerate(tl["segs"]):           # o riscar do marcador: quase impercetível
        s = risco(max(t1 - t0, 0.1), seed=k) * 0.16
        a = int(t0 * SR)
        fx[a:a + len(s)] += s[: n - a]
    for p in tl["paginas"][1:]:
        s = folha() * 0.045
        a = int(max(p["start"] - PRE - SLIDE, 0) * SR)
        fx[a:a + len(s)] += s
    musica = gerar_musica(n / SR, voz)
    musica = np.pad(musica, (0, max(0, n - len(musica))))[:n]
    mix = voz + fx + musica
    mix *= 0.72 / (float(np.percentile(np.abs(mix), 99.7)) + 1e-9)      # normalização linear (mantém as diferenças de nível)
    mix = np.tanh(mix * 1.15) / np.tanh(1.15) * 0.89                    # limitador suave para os picos
    return mix[: int(tl["total"] * SR)]


# ------------------------------------------------------------------ imagem
def papel():
    r = np.random.default_rng(994)
    base = np.array([PAPER[2], PAPER[1], PAPER[0]], np.float32) * 255
    img = np.empty((H, W, 3), np.float32)
    img[:] = base
    img += r.normal(0, 2.2, (H, W, 1)).astype(np.float32)
    coarse = r.normal(0, 2.0, (H // 6, W // 6, 1)).astype(np.float32)
    img += np.kron(coarse, np.ones((6, 6, 1), np.float32))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2)
    img *= (1 - 0.13 * np.clip(d - 0.4, 0, 1))[..., None]
    out = np.empty((H, W, 4), np.uint8)
    out[..., :3] = np.clip(img, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return cairo.ImageSurface.create_for_data(out, cairo.FORMAT_ARGB32, W, H, W * 4), out


def chunks(palavras):
    out, cur = [], []
    for w in palavras:
        if cur:
            gap = w["t0"] - cur[-1]["t1"]
            if len(cur) >= 4 or sum(len(x["text"]) + 1 for x in cur) + len(w["text"]) > 24 or gap > 0.4 or cur[-1]["text"][-1] in ".!?:" \
                    or (cur[-1]["text"][-1] == "," and len(cur) >= 2):
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.bg, self._buf = papel()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.ctx = cairo.Context(self.surface)
        self.imgs = {"logo": cairo.ImageSurface.create_from_png(str(ROOT / "assets" / "logo-994.png"))}
        self.starts = [p["start"] for p in tl["paginas"]]
        self.chunks = [(b, chunks(b["words"][:b["legenda_n"]] if b.get("legenda_n") else b["words"])) for b in tl["blocos"]]
        self.segt0 = [s[0] for s in tl["segs"]]

    # ---- posição da mão
    def _ponta(self, e, p):
        if e["k"] == "path":
            return ponto_em(e, clamp(p))
        wt = largura_texto(self.ctx, e["txt"], e["size"])
        x0 = e["x"] - {"c": wt / 2, "l": 0, "r": wt}[e["align"]]
        return (x0 + wt * clamp(p), e["y"] - e["size"] * 0.25)

    def mao(self, t):
        REST = (W + 260.0, 420.0)
        segs = self.tl["segs"]
        i = bisect.bisect_right(self.segt0, t) - 1          # último segmento já começado
        prev = nxt = None
        if i >= 0:
            t0, t1, e, _ = segs[i]
            if t <= t1:
                return self._ponta(e, (t - t0) / max(t1 - t0, 1e-6))
            prev = (t1, self._ponta(e, 1.0))
        if i + 1 < len(segs):
            nxt = (segs[i + 1][0], self._ponta(segs[i + 1][2], 0.0))
        lerp = lambda a, b, k: (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        pos = lerp(prev[1], REST, ease((t - prev[0]) / 0.55)) if prev else REST
        if nxt and nxt[0] - t < 0.55:
            pos = lerp(pos, nxt[1], ease(1 - (nxt[0] - t) / 0.55))
        return pos

    # ---- legendas
    def legendas(self, ctx, t):
        for b, chs in self.chunks:
            if not (b["start"] - 0.1 <= t <= b["end"] + 1.0):
                continue
            for ci, ch in enumerate(chs):
                a = ch[0]["t0"] - 0.05
                nx = chs[ci + 1][0]["t0"] - 0.05 if ci + 1 < len(chs) else 1e9
                z = min(ch[-1]["t1"] + 0.7, nx)
                if a <= t < z:
                    self._chunk(ctx, ch, t)
                    return

    def _chunk(self, ctx, ch, t):
        size, ymid = 64, SUB_Y + 0
        sp = largura_texto(ctx, "a a", size) - largura_texto(ctx, "aa", size) + 12
        ws = [largura_texto(ctx, w["text"], size) for w in ch]
        tot = sum(ws) + sp * (len(ch) - 1)
        lines = [list(range(len(ch)))]
        if tot > SUB_W and len(ch) > 1:
            k = min(range(1, len(ch)), key=lambda k: abs(sum(ws[:k]) - sum(ws[k:])))
            lines = [list(range(k)), list(range(k, len(ch)))]
        for li, idx in enumerate(lines):
            lw = sum(ws[i] for i in idx) + sp * (len(idx) - 1)
            x = SUB_CX - lw / 2
            y = ymid + (li - (len(lines) - 1) / 2) * 72
            for i in idx:
                w = ch[i]
                if t >= w["t0"] - 0.02:
                    ativo = w["t0"] - 0.02 <= t < w["t1"] + 0.06
                    if ativo:                                    # sublinhado de marcador amarelo
                        ctx.save()
                        ctx.rotate(0)
                        ctx.rectangle(x - 8, y - size * 0.62, ws[i] + 16, size * 0.78)
                        ctx.set_source_rgba(*AMARELO, 0.78)
                        ctx.fill()
                        ctx.restore()
                    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                    ctx.set_font_size(size)
                    ctx.move_to(x, y)
                    ctx.set_source_rgb(*INK)
                    ctx.show_text(w["text"])
                x += ws[i] + sp

    # ---- frame
    def render(self, f):
        tl, ctx = self.tl, self.ctx
        t = f / FPS
        step = f // STEP
        ctx.set_source_surface(self.bg, 0, 0)
        ctx.paint()

        # marca d'água (dentro da zona segura)
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(44)
        ctx.move_to(SAFE[0], MARCA_Y + 50)
        ctx.set_source_rgba(*VERDE, 1.0)
        ctx.show_text("@994caxinas")

        # páginas (o caderno desliza ao mudar de página)
        ps = tl["paginas"]
        for k_, pg in enumerate(ps):
            e_in = clamp((t - (pg["start"] - PRE - SLIDE)) / SLIDE)
            off = W * (1 - ease(e_in)) if k_ > 0 else 0.0
            if k_ + 1 < len(ps):
                off -= W * ease(clamp((t - (ps[k_ + 1]["start"] - PRE - SLIDE)) / SLIDE))
            if off >= W - 1 or off <= -W + 1:
                continue
            ctx.save()
            ctx.translate(off, 0)
            ctx.rectangle(0, VIEW_Y0 - 40, W, VIEW_H + 80)
            ctx.clip()
            ctx.translate(X_CENA, VIEW_Y0)
            ctx.scale(S_CENA, S_CENA)
            ctx.translate(0, -AREA[1])
            for e in pg["els"]:
                if t < e["t0"]:
                    continue
                p = clamp((t - e["t0"]) / max(e["t1"] - e["t0"], 1e-6))
                ff = ease((t - e["t1"]) / 0.5) if t > e["t1"] else 0.0
                desenha_elemento(ctx, e, p, step, ff, self.imgs)
            ctx.restore()

        if t < tl["total"] - 0.3:
            x, y = para_ecra(*self.mao(t))
            if -200 < x < W + 400:
                desenha_mao(ctx, x, y, t)
        self.legendas(ctx, t)
        self.surface.flush()
        return bytes(self.surface.get_data())

    def png(self, f, path):
        self.render(f)
        self.surface.write_to_png(path)


_R = None


def _init(tl):
    global _R
    _R = Renderer(tl)


def _frame(f):
    return _R.render(f)


def codificar(tl, wav, saida, workers):
    cmd = [ffmpeg_exe(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-crf", "17", "-maxrate", "12M", "-bufsize", "20M",
           "-r", str(FPS), "-fps_mode", "cfr", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-t", f"{tl['n_frames'] / FPS:.3f}", "-movflags", "+faststart", str(saida)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    ctx = mp.get_context("fork" if sys.platform == "linux" else "spawn")
    with ctx.Pool(workers, initializer=_init, initargs=(tl,)) as pool:
        for i, buf in enumerate(pool.imap(_frame, range(tl["n_frames"]), chunksize=2)):
            ff.stdin.write(buf)
            if i % 150 == 0 or i == tl["n_frames"] - 1:
                print(f"\r  frame {i + 1}/{tl['n_frames']}  ({time.time() - t0:.0f}s)", end="", flush=True)
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg falhou")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("guiao")
    ap.add_argument("--png", nargs="+", type=float)
    ap.add_argument("-j", "--workers", type=int, default=max(1, mp.cpu_count() or 2))
    a = ap.parse_args()
    nome = Path(a.guiao).stem
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    print("[1/3] Voz e tempos")
    tl, partes = construir(a.guiao)
    for b in tl["blocos"]:
        print(f"  {b['start']:5.1f}–{b['end']:5.1f}s  [{b['cena']}] {b['texto'][:64]}")
    print(f"  duração: {tl['total']:.1f}s ({tl['n_frames']} frames)")
    if a.png:
        r = Renderer(tl)
        for s in a.png:
            p = out / f"{nome}_t{s:05.1f}.png"
            r.png(min(int(s * FPS), tl["n_frames"] - 1), str(p))
            print("  ", p)
        return
    wav = out / f"{nome}.wav"
    write_wav(str(wav), mistura(tl, partes))
    (out / f"{nome}.legenda.txt").write_text(tl["cfg"].get("legenda", "") + "\n", encoding="utf-8")
    print(f"[2/3] A desenhar {tl['n_frames']} frames ({a.workers} processos)")
    codificar(tl, wav, out / f"{nome}.mp4", a.workers)
    wav.unlink(missing_ok=True)
    print(f"[3/3] Pronto: {out / (nome + '.mp4')}")


if __name__ == "__main__":
    main()

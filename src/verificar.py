#!/usr/bin/env python3
"""Verifica as especificações do Reels (ESPECIFICACOES_REELS.md) antes de entregar:
zonas seguras (topo 220, fundo 420, esquerda 60, direita 140), texto ≥ 36 px, traços ≥ 3 px, e o ficheiro final.

    python src/verificar.py guioes/como_surgiu.json [output/como_surgiu.mp4]
"""
import json
import subprocess
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *  # noqa: E402
from desenho import largura_texto  # noqa: E402
import render as R  # noqa: E402


def caixa_elemento(ctx, e):
    if e["k"] == "path":
        x0, y0 = e["pts"].min(axis=0)
        x1, y1 = e["pts"].max(axis=0)
        m = e["w"] / 2 + 3 * e["tremor"]
        return (x0 - m, y0 - m, x1 + m, y1 + m)
    if e["k"] == "texto":
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(e["size"])
        ex = ctx.text_extents(e["txt"])
        wt = ex.x_advance
        xl = e["x"] - {"c": wt / 2, "l": 0, "r": wt}[e["align"]]
        return (xl, e["y"] + ex.y_bearing, xl + wt, e["y"] + ex.y_bearing + ex.height + (e["size"] * 0.3 if e["sub"] else 0))
    if e["k"] == "img":
        im = cairo.ImageSurface.create_from_png(str(ROOT / "assets" / "logo-994.png"))
        w = e["h"] * im.get_width() / im.get_height()
        return (e["x"] - w / 2, e["y"] - e["h"] / 2, e["x"] + w / 2, e["y"] + e["h"] / 2)


def main():
    guiao = sys.argv[1]
    mp4 = sys.argv[2] if len(sys.argv) > 2 else None
    tl, _ = R.construir(guiao)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
    ctx = cairo.Context(surf)
    x0s, y0s, x1s, y1s = SAFE
    erros, min_txt, min_w = [], 1e9, 1e9

    def fora(nome, bx):
        x0, y0, x1, y1 = bx
        if x0 < x0s - 0.5 or y0 < y0s - 0.5 or x1 > x1s + 0.5 or y1 > y1s + 0.5:
            erros.append(f"{nome}: ({x0:.0f},{y0:.0f})–({x1:.0f},{y1:.0f}) fora de {SAFE}")

    # 1) elementos desenhados
    for k, pg in enumerate(tl["paginas"]):
        for e in pg["els"]:
            bx = caixa_elemento(ctx, e)
            a, b = para_ecra(bx[0], bx[1])
            c, d = para_ecra(bx[2], bx[3])
            nome = f"página {k + 1} · {e['k']} {e.get('txt', '')}"
            fora(nome, (a, b, c, d))
            if e["k"] == "texto":
                min_txt = min(min_txt, e["size"] * S_CENA)
            if e["k"] == "path" and e["w"] > 6 or e["k"] == "path":
                min_w = min(min_w, e["w"] * S_CENA)
    # 2) legendas
    r = R.Renderer(tl)
    ctx2 = r.ctx
    maxw = 0
    for b, chs in r.chunks:
        for ch in chs:
            size = 64
            sp = largura_texto(ctx2, "a a", size) - largura_texto(ctx2, "aa", size) + 12
            ws = [largura_texto(ctx2, w["text"], size) for w in ch]
            tot = sum(ws) + sp * (len(ch) - 1)
            if tot > SUB_W and len(ch) > 1:
                kk = min(range(1, len(ch)), key=lambda kk: abs(sum(ws[:kk]) - sum(ws[kk:])))
                lw = max(sum(ws[:kk]) + sp * (kk - 1), sum(ws[kk:]) + sp * (len(ch) - kk - 1))
                lines = 2
            else:
                lw, lines = tot, 1
            maxw = max(maxw, lw)
            top = SUB_Y - (lines - 1) * 36 - size * 0.85
            bot = SUB_Y + (lines - 1) * 36 + size * 0.28
            fora("legenda «" + " ".join(w["text"] for w in ch) + "»", (SUB_CX - lw / 2, top, SUB_CX + lw / 2, bot))
    min_txt = min(min_txt, 64)
    # 3) marca d'água
    lg = r.imgs["logo"]
    kk = 72 / lg.get_height()
    ctx2.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx2.set_font_size(40)
    wt = ctx2.text_extents("@994caxinas").x_advance
    fora("marca d'água", (SAFE[0], MARCA_Y, SAFE[0] + lg.get_width() * kk + 18 + wt, MARCA_Y + 72))

    print(f"Zonas seguras {SAFE}: {'OK' if not erros else str(len(erros)) + ' violações'}")
    for e in erros[:20]:
        print("  ✗", e)
    print(f"Texto mínimo (já escalado): {min_txt:.1f} px  {'OK' if min_txt >= 36 else '✗ (< 36)'}")
    print(f"Traço mínimo (já escalado): {min_w:.1f} px  {'OK' if min_w >= 3 else '✗ (< 3)'}")
    print(f"Legenda mais larga: {maxw:.0f} px (máx. {SUB_W:.0f})")
    ok = not erros and min_txt >= 36 and min_w >= 3
    if mp4:
        pr = lambda sel, f: subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", f, "-of", "default=nw=1", mp4], capture_output=True, text=True).stdout
        v = dict(l.split("=") for l in pr("v:0", "stream=width,height,codec_name,profile,level,pix_fmt,r_frame_rate,avg_frame_rate,bit_rate").split())
        a = dict(l.split("=") for l in pr("a:0", "stream=codec_name,sample_rate,channels,bit_rate").split())
        chk = [("1080×1920", v["width"] == "1080" and v["height"] == "1920", f"{v['width']}×{v['height']}"),
               ("30 fps constantes", v["r_frame_rate"] == "30/1" and v["avg_frame_rate"] == "30/1", v["r_frame_rate"] + " / " + v["avg_frame_rate"]),
               ("H.264 High, nível 4.1", v["codec_name"] == "h264" and v["profile"] == "High" and v["level"] == "41", f"{v['codec_name']} {v['profile']} level {v['level']}"),
               ("yuv420p", v["pix_fmt"] == "yuv420p", v["pix_fmt"]),
               ("vídeo ≤ 12 Mbps", int(v["bit_rate"]) <= 12_000_000, f"{int(v['bit_rate']) / 1e6:.1f} Mbps"),
               ("áudio AAC 48 kHz estéreo", a["codec_name"] == "aac" and a["sample_rate"] == "48000" and a["channels"] == "2", f"{a['codec_name']} {a['sample_rate']} Hz, {a['channels']} canais, {int(a['bit_rate']) // 1000} kbps")]
        for nome, passou, val in chk:
            print(f"  {'✓' if passou else '✗'} {nome}  ({val})")
            ok = ok and passou
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

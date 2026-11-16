"""Legendas dinâmicas estilo Reels: blocos curtos, palavras que «saltam» ao serem ditas."""
import math

import cairo

from config import *

PAUSE_BREAK = 0.35
MAX_WORDS = 4
MAX_CHARS = 20
MAX_WIDTH = 900
FONT_SIZE = 84
LINE_H = 100


def make_chunks(words):
    """Agrupa palavras (com t0/t1) em chunks curtos para ecrã. Nunca atravessa blocos."""
    chunks, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            chunks.append(cur)
            cur = []

    for i, w in enumerate(words):
        if cur:
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            gap = w["t0"] - cur[-1]["t1"]
            prev = cur[-1]["text"]
            if (len(cur) >= MAX_WORDS or chars > MAX_CHARS or gap > PAUSE_BREAK
                    or prev[-1] in ".!?…" or (prev[-1] in ",;:" and len(cur) >= 2)):
                flush()
        cur.append(w)
    flush()
    return chunks


def _font(ctx, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)


def _layout(ctx, chunk, size=FONT_SIZE):
    _font(ctx, size)
    space = ctx.text_extents("a a").x_advance - ctx.text_extents("aa").x_advance + size * 0.16
    widths = [ctx.text_extents(w["text"].upper()).x_advance for w in chunk]
    total = sum(widths) + space * (len(chunk) - 1)
    lines = [list(range(len(chunk)))]
    if total > MAX_WIDTH and len(chunk) > 1:           # parte em duas linhas, o mais equilibrado possível
        best = min(range(1, len(chunk)),
                   key=lambda k: abs(sum(widths[:k]) - sum(widths[k:])))
        lines = [list(range(best)), list(range(best, len(chunk)))]
    pos = {}
    for li, idxs in enumerate(lines):
        lw = sum(widths[i] for i in idxs) + space * (len(idxs) - 1)
        x = 540 - lw / 2
        y = SUB_Y + (li - (len(lines) - 1) / 2) * LINE_H + size * 0.35
        for i in idxs:
            pos[i] = (x, y, widths[i])
            x += widths[i] + space
    return pos


def _back(x):
    c = 1.70158 + 1
    return 1 + c * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


def draw_word(ctx, text, x, y, wid, size, fill, scale=1.0):
    ctx.save()
    ctx.translate(x + wid / 2, y - size * 0.35)
    ctx.scale(scale, scale)
    ctx.translate(-wid / 2, size * 0.35)
    _font(ctx, size)
    ctx.move_to(0, 0)
    ctx.text_path(text)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_line_width(size * 0.15)
    ctx.stroke_preserve()
    ctx.set_source_rgb(*fill)
    ctx.fill()
    ctx.restore()


def draw_subtitles(ctx, chunks, t, cache):
    """Desenha o chunk ativo em t. `cache` guarda layouts por chunk."""
    active = None
    for ci, ch in enumerate(chunks):
        start = ch[0]["t0"] - 0.03
        nxt = chunks[ci + 1][0]["t0"] - 0.03 if ci + 1 < len(chunks) else 1e9
        end = min(ch[-1]["t1"] + 0.30, nxt)
        if start <= t < end:
            active = (ci, ch)
            break
    if not active:
        return
    ci, ch = active
    if ci not in cache:
        cache[ci] = _layout(ctx, ch)
    pos = cache[ci]
    for i, w in enumerate(ch):
        age = t - (w["t0"] - 0.02)
        if age < 0:
            continue
        s = 0.62 + 0.38 * _back(min(age / 0.20, 1.0))
        fill = {"y": YELLOW, "g": GREEN_LIGHT}.get(w["style"], WHITE)
        if w["style"]:
            s *= 1.06
        x, y, wid = pos[i]
        draw_word(ctx, w["text"].upper(), x, y, wid, FONT_SIZE, fill, s)

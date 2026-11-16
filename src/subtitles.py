"""Legendas virais (estilo Hormozi): blocos curtos sobre cápsula semitransparente, palavra ativa
com a cor do lenço do 994 e animação de escala suave."""
import cairo

from config import *

PAUSE_BREAK = 0.35
MAX_WORDS = 4
MAX_CHARS = 20
MAX_WIDTH = 860
FONT_SIZE = 82
LINE_H = 98


def make_chunks(words):
    chunks, cur = [], []
    for w in words:
        if cur:
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            gap = w["t0"] - cur[-1]["t1"]
            prev = cur[-1]["text"]
            if (len(cur) >= MAX_WORDS or chars > MAX_CHARS or gap > PAUSE_BREAK
                    or prev[-1] in ".!?…" or (prev[-1] in ",;:" and len(cur) >= 2)):
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def _font(ctx, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)


def _layout(ctx, chunk, size=FONT_SIZE):
    _font(ctx, size)
    space = ctx.text_extents("a a").x_advance - ctx.text_extents("aa").x_advance + size * 0.30
    widths = [ctx.text_extents(w["text"].upper()).x_advance for w in chunk]
    total = sum(widths) + space * (len(chunk) - 1)
    lines = [list(range(len(chunk)))]
    if total > MAX_WIDTH and len(chunk) > 1:
        best = min(range(1, len(chunk)), key=lambda k: abs(sum(widths[:k]) - sum(widths[k:])))
        lines = [list(range(best)), list(range(best, len(chunk)))]
    pos, maxw = {}, 0
    for li, idxs in enumerate(lines):
        lw = sum(widths[i] for i in idxs) + space * (len(idxs) - 1)
        maxw = max(maxw, lw)
        x = 540 - lw / 2
        y = SUB_Y + (li - (len(lines) - 1) / 2) * LINE_H + size * 0.35
        for i in idxs:
            pos[i] = (x, y, widths[i])
            x += widths[i] + space
    box = (540 - maxw / 2 - 40, SUB_Y - len(lines) * LINE_H / 2 - 6, maxw + 80, len(lines) * LINE_H + 12)
    return pos, box


def _back(x, c=1.5):
    x = max(0.0, min(1.0, x))
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def _pill(ctx, x, y, w, h, alpha):
    r = min(46, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -1.5708, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, 1.5708)
    ctx.arc(x + r, y + h - r, r, 1.5708, 3.1416)
    ctx.arc(x + r, y + r, r, 3.1416, 4.7124)
    ctx.close_path()
    ctx.set_source_rgba(0.06, 0.07, 0.06, 0.46 * alpha)
    ctx.fill()


def _word(ctx, text, x, y, wid, size, fill, scale, alpha):
    ctx.save()
    ctx.translate(x + wid / 2, y - size * 0.35)
    ctx.scale(scale, scale)
    ctx.translate(-wid / 2, size * 0.35)
    _font(ctx, size)
    ctx.move_to(0, 0)
    ctx.text_path(text)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(0.02, 0.02, 0.02, 0.85 * alpha)
    ctx.set_line_width(size * 0.13)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*fill, alpha)
    ctx.fill()
    ctx.restore()


def draw_subtitles(ctx, chunks, t, cache):
    active = None
    for ci, ch in enumerate(chunks):
        start = ch[0]["t0"] - 0.04
        nxt = chunks[ci + 1][0]["t0"] - 0.04 if ci + 1 < len(chunks) else 1e9
        end = min(ch[-1]["t1"] + 0.28, nxt)
        if start <= t < end:
            active = (ci, ch, start)
            break
    if not active:
        return
    ci, ch, start = active
    if ci not in cache:
        cache[ci] = _layout(ctx, ch)
    pos, (bx, by, bw, bh) = cache[ci]
    k = _back((t - start) / 0.16)
    a = min(1.0, (t - start) / 0.08)
    cx, cy = 540, SUB_Y
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(0.88 + 0.12 * k, 0.88 + 0.12 * k)
    ctx.translate(-cx, -cy)
    _pill(ctx, bx, by, bw, bh, a)
    for i, w in enumerate(ch):
        x, y, wid = pos[i]
        is_active = w["t0"] - 0.02 <= t < w["t1"] + 0.06
        fill = {"y": YELLOW, "g": GREEN_BRIGHT}.get(w["style"], GREEN_BRIGHT if is_active else WHITE)
        if is_active:
            s = 1.0 + 0.10 * _back((t - w["t0"] + 0.02) / 0.14)
        else:
            s = 1.0
        _word(ctx, w["text"].upper(), x, y, wid, FONT_SIZE, fill, s, a)
    ctx.restore()

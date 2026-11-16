"""Composição de cada frame: papel quadriculado, marca d'água, quadro, Tiko, legendas, outro."""
import bisect
import math

import cairo
import numpy as np

from character import draw_tiko, pose_at
from config import *
from props import draw_prop
from subtitles import draw_subtitles


# ------------------------------------------------------------------ fundo (gerado uma vez)
def make_background():
    """Folha de caderno de campo quadriculada, creme #FAF8F5, com grão subtil e vinheta."""
    rng = np.random.default_rng(994)
    base = np.array([0xF5, 0xF8, 0xFA], dtype=np.float32)          # BGR de #FAF8F5
    img = np.empty((H, W, 3), dtype=np.float32)
    img[:] = base
    grid = np.array([0xDC, 0xD2, 0xC4], dtype=np.float32)            # linhas azul-acinzentadas (BGR)
    step = 60
    for x in range(30, W, step):
        img[:, x:x + 2] = img[:, x:x + 2] * 0.45 + grid * 0.55
    for y in range(30, H, step):
        img[y:y + 2, :] = img[y:y + 2, :] * 0.45 + grid * 0.55
    # grão de papel + fibras suaves
    img += rng.normal(0, 2.2, (H, W, 1)).astype(np.float32)
    coarse = rng.normal(0, 1.6, (H // 8, W // 8, 1)).astype(np.float32)
    img += np.kron(coarse, np.ones((8, 8, 1), dtype=np.float32))
    # vinheta
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    img *= (1 - 0.10 * np.clip(d - 0.45, 0, 1))[..., None]
    out = np.empty((H, W, 4), dtype=np.uint8)
    out[..., :3] = np.clip(img, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    surf = cairo.ImageSurface.create_for_data(out, cairo.FORMAT_ARGB32, W, H, W * 4)
    return surf, out


# ------------------------------------------------------------------ elementos fixos
def draw_watermark(ctx, text):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(38)
    e = ctx.text_extents(text)
    total = e.width + 58
    x0 = 540 - total / 2
    # mini-lenço como ícone
    ctx.move_to(x0, WATERMARK_Y - 24)
    ctx.line_to(x0 + 40, WATERMARK_Y - 24)
    ctx.line_to(x0 + 20, WATERMARK_Y + 12)
    ctx.close_path()
    ctx.set_source_rgba(*GREEN, 0.9)
    ctx.fill_preserve()
    ctx.set_source_rgba(*YELLOW, 0.95)
    ctx.set_line_width(4)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.move_to(x0 + 58, WATERMARK_Y + 8)
    ctx.set_source_rgba(*GREEN, 0.85)
    ctx.show_text(text)


def draw_board(ctx, t):
    x, y, w, h = BOARD
    ctx.save()
    ctx.translate(x + w / 2, y + h / 2)
    ctx.rotate(math.radians(-0.6))
    ctx.translate(-w / 2, -h / 2)
    # sombra + folha
    ctx.rectangle(10, 12, w, h)
    ctx.set_source_rgba(0, 0, 0, 0.10)
    ctx.fill()
    ctx.rectangle(0, 0, w, h)
    ctx.set_source_rgb(1, 1, 0.985)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(9)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    # segundo traço, ligeiramente torto (ar de desenhado à mão)
    ctx.set_line_width(4)
    ctx.move_to(-4, 6)
    ctx.line_to(w + 3, -3)
    ctx.line_to(w - 2, h + 5)
    ctx.line_to(5, h - 3)
    ctx.close_path()
    ctx.set_source_rgba(*INK, 0.55)
    ctx.stroke()
    # fita-cola
    for cx, ang in ((70, -10), (w - 70, 9)):
        ctx.save()
        ctx.translate(cx, 2)
        ctx.rotate(math.radians(ang))
        ctx.rectangle(-55, -17, 110, 34)
        ctx.set_source_rgba(*YELLOW, 0.75)
        ctx.fill()
        ctx.restore()
    ctx.restore()


def _slots(n):
    x, y, w, h = BOARD
    slot = w / max(n, 1)
    size = min(slot * 0.9, h * 0.82, 380)
    return [(x + slot * (i + 0.5), y + h / 2 + 10, size) for i in range(n)]


def draw_props(ctx, blk, prev, t):
    names = blk["props"]
    for i, ((px, py, size), name, appear) in enumerate(zip(_slots(len(names)), names, blk["appear"])):
        draw_prop(ctx, name, px, py, size, t - appear, seed=i * 1.7)
    if prev and not prev.get("outro") and t - blk["vstart"] < 0.18:      # props antigos encolhem
        k = (t - blk["vstart"]) / 0.18
        for i, ((px, py, size), name) in enumerate(zip(_slots(len(prev["props"])), prev["props"])):
            if name not in names:
                draw_prop(ctx, name, px, py, size, 1.0, seed=i * 1.7, shrink=k)


def draw_outro_card(ctx, blk, t):
    x, y, w, h = BOARD
    age = t - blk["vstart"]
    draw_prop(ctx, "35", x + 225, y + h / 2 + 5, 330, age - 0.1)
    s = min(max((age - 0.25) / 0.4, 0), 1)
    if s > 0:
        e = 1 + 2.70158 * (s - 1) ** 3 + 1.70158 * (s - 1) ** 2
        ctx.save()
        ctx.translate(x + 640, y + h / 2 - 20)
        ctx.scale(e, e)
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for i, word in enumerate(("SEMPRE", "ALERTA!")):
            ctx.set_font_size(90 if i == 0 else 96)
            ex = ctx.text_extents(word)
            ctx.move_to(-ex.width / 2 - ex.x_bearing, -10 + i * 100)
            ctx.text_path(word)
            ctx.set_source_rgb(*(GREEN if i == 0 else YELLOW))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(10)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
        ctx.set_font_size(36)
        tag = "#35AnosDeExemplo"
        ex = ctx.text_extents(tag)
        ctx.move_to(-ex.width / 2 - ex.x_bearing, 150)
        ctx.set_source_rgb(*GREEN)
        ctx.show_text(tag)
        ctx.restore()


# ------------------------------------------------------------------ frame completo
class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.bg, self._bg_buf = make_background()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.ctx = cairo.Context(self.surface)
        self.starts = [b["vstart"] for b in tl["blocks"]]
        self.sub_cache = {}

    def render(self, f):
        tl, ctx = self.tl, self.ctx
        t = f / FPS
        bi = max(0, bisect.bisect_right(self.starts, t) - 1)
        blk = tl["blocks"][bi]
        prev = tl["blocks"][bi - 1] if bi > 0 else None

        ctx.set_source_surface(self.bg, 0, 0)
        ctx.paint()
        draw_watermark(ctx, tl["watermark"])
        draw_board(ctx, t)
        if blk.get("outro"):
            draw_outro_card(ctx, blk, t)
        else:
            draw_props(ctx, blk, prev, t)

        pose = pose_at(tl["blocks"], t)
        mo, mw = float(tl["mouth_o"][f]), float(tl["mouth_w"][f])
        ctx.save()
        if t < 0.5:                                   # entrada «pop» do Tiko
            k = t / 0.5
            e = 1 + 2.70158 * (k - 1) ** 3 + 1.70158 * (k - 1) ** 2
            ctx.translate(NECK[0], GROUND_Y)
            ctx.scale(0.8 + 0.2 * e, 0.8 + 0.2 * e)
            ctx.translate(-NECK[0], -GROUND_Y)
        draw_tiko(ctx, t, pose, mo, mw, mo, hat=tl["chapeu"])
        ctx.restore()

        draw_subtitles(ctx, blk["chunks"], t, self.sub_cache.setdefault(bi, {}))
        self.surface.flush()
        return bytes(self.surface.get_data())

    def png(self, f, path):
        self.render(f)
        self.surface.write_to_png(path)

"""Composição de cada frame: câmara virtual, fundo vivo, ilustrações, Tiko, legendas, marca d'água."""
import bisect
import math

import cairo

import character
import props
from album import Album
from background import draw_parallax, make_texture
from character import clamp, draw_tiko, ease, tiko_dx
from config import *
from props import draw_prop
from subtitles import draw_subtitles

CAM_BASE = {"normal": 1.0, "punch": 1.0, "aperto": 1.07, "lento": 1.0}


# ------------------------------------------------------------------ câmara
def _base_zoom(b, t):
    c = b.get("camara", "normal")
    z = CAM_BASE.get(c, 1.0)
    if c == "lento":
        z = 1.0 + 0.07 * clamp((t - b["vstart"]) / max(b["vend"] - b["vstart"], 0.1))
    return z


def camera_zoom(tl, t):
    blocks = tl["blocks"]
    i = max(0, bisect.bisect_right([b["vstart"] for b in blocks], t) - 1)
    z = _base_zoom(blocks[i], t)
    if i > 0:
        prev = _base_zoom(blocks[i - 1], blocks[i]["vstart"])
        z = prev + (z - prev) * ease((t - blocks[i]["vstart"]) / 0.4)
    for pt in tl["punches"]:                      # micro-zoom «punch-in» até ~112% com retorno elástico
        dt = t - pt
        if 0 <= dt < 1.2:
            z += 0.14 * min(dt / 0.06, 1.0) * math.exp(-3.4 * dt)
    return z


# ------------------------------------------------------------------ ilustrações
def prop_slots(n, side):
    xc = 540 + side * 275
    if n == 1:
        return [(xc, 840, 440)]
    if n == 2:
        return [(xc, 650, 340), (xc, 1030, 340)]
    ys = [560 + i * (680 / max(n - 1, 1)) for i in range(n)]
    return [(xc, y, 300) for y in ys]


def draw_props(ctx, blk, prev, t):
    names = blk["props"]
    side = 1 if blk["tiko_dx"] <= 0 else -1
    for i, ((px, py, size), name, ap) in enumerate(zip(prop_slots(len(names), side), names, blk["appear"])):
        if name.split("@")[0] == "logo":
            size = min(size, 370)
        draw_prop(ctx, name, px, py, size, t - ap, seed=i * 1.7)
    if prev and prev["props"] and t - blk["vstart"] < 0.2:
        k = (t - blk["vstart"]) / 0.2
        pside = 1 if prev["tiko_dx"] <= 0 else -1
        for i, ((px, py, size), name) in enumerate(zip(prop_slots(len(prev["props"]), pside), prev["props"])):
            if name not in names:
                draw_prop(ctx, name, px, py, size, 1.0, seed=i * 1.7, shrink=k)


# ------------------------------------------------------------------ HUD
def draw_watermark(ctx, logo, text):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(40)
    e = ctx.text_extents(text)
    h = 118.0
    k = h / logo.get_height()
    lw = logo.get_width() * k
    total = lw + 22 + e.width
    x0, y0 = 540 - total / 2, 130
    ctx.save()
    ctx.translate(x0, y0)
    ctx.scale(k, k)
    ctx.set_source_surface(logo, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_BEST)
    ctx.paint_with_alpha(0.95)
    ctx.restore()
    ctx.move_to(x0 + lw + 22 - e.x_bearing, y0 + h / 2 + 14)
    ctx.set_source_rgba(*SCARF_DARK, 0.92)
    ctx.show_text(text)


# ------------------------------------------------------------------ renderizador
class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.tex, self._buf = make_texture()
        self.logo = cairo.ImageSurface.create_from_png(str(LOGO_PATH))
        character.LOGO = self.logo
        props.LOGO = self.logo
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.ctx = cairo.Context(self.surface)
        self.starts = [b["vstart"] for b in tl["blocks"]]
        self.sub_cache = {}
        if tl.get("traje") == "lobito":                 # capuz de lobo + lenço amarelo com debrum verde
            character.TRAJE = "lobito"
            character.SCARF, character.SCARF_DARK = mix(LOGO_YELLOW, BLACK, 0.12), mix(LOGO_YELLOW, BLACK, 0.5)
            character.SCARF_LIGHT, character.TRIM = mix(LOGO_YELLOW, WHITE, 0.35), LOGO_GREEN
        self.album = Album(tl, self.tex) if tl.get("album") else None

    def render(self, f):
        tl, ctx = self.tl, self.ctx
        t = f / FPS
        bi = max(0, bisect.bisect_right(self.starts, t) - 1)
        blk = tl["blocks"][bi]
        prev = tl["blocks"][bi - 1] if bi > 0 else None

        z = camera_zoom(tl, t)
        cx, cy = 540 + tiko_dx(tl["blocks"], t) * 0.3, 1000
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(z, z)
        ctx.translate(-cx, -cy)
        if self.album:
            self.album.draw(ctx, t)
        else:
            ctx.set_source_surface(self.tex, 0, 0)
            ctx.paint()
            draw_parallax(ctx, t)
            draw_props(ctx, blk, prev, t)
        sc = tl["scarf"][f]
        draw_tiko(ctx, t, tl["blocks"], float(tl["mouth_o"][f]), float(tl["mouth_v"][f]),
                  (float(sc[0]), float(sc[1]), float(sc[2])), hat=tl["chapeu"])
        ctx.restore()

        draw_watermark(ctx, self.logo, tl["watermark"])
        draw_subtitles(ctx, blk["chunks"], t, self.sub_cache.setdefault(bi, {}))
        self.surface.flush()
        return bytes(self.surface.get_data())

    def png(self, f, path):
        self.render(f)
        self.surface.write_to_png(path)

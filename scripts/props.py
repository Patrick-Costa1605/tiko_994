"""Ilustrações do «quadro»: ícones simples desenhados em vetor (origem no centro, ~300 px)."""
import math
import unicodedata

import cairo

from config import *


def _norm(name):
    s = unicodedata.normalize("NFKD", name.lower().strip()).encode("ascii", "ignore").decode()
    return s.replace(" ", "_").replace("-", "_")


def _st(ctx, w=9, color=INK):
    ctx.set_source_rgb(*color)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)


def _fs(ctx, fill, w=9):
    ctx.set_source_rgb(*fill)
    ctx.fill_preserve()
    _st(ctx, w)
    ctx.stroke()


def _poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def _rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


TENT = (0.36, 0.68, 0.45)


def tenda(ctx, t):
    _st(ctx, 6)
    for s in (-1, 1):                                   # tirantes + estacas
        ctx.move_to(s * 78, 20)
        ctx.line_to(s * 175, 112)
        ctx.stroke()
        _poly(ctx, [(s * 175 - 7, 112), (s * 175 + 7, 112), (s * 175, 126)])
        _fs(ctx, BROWN, 4)
    _poly(ctx, [(-140, 112), (0, -112), (140, 112)])
    _fs(ctx, TENT, 10)
    _poly(ctx, [(-46, 112), (0, -22), (46, 112)])
    _fs(ctx, (0.16, 0.2, 0.17), 8)
    _st(ctx, 7)
    ctx.move_to(0, -112)
    ctx.line_to(0, -150)
    ctx.stroke()
    fl = math.sin(t * 6) * 5
    _poly(ctx, [(0, -150), (38, -140 + fl), (0, -126)])
    _fs(ctx, YELLOW, 6)
    _st(ctx, 8)
    ctx.move_to(-190, 112)
    ctx.line_to(190, 112)
    ctx.stroke()


def tenda_caida(ctx, t):
    _st(ctx, 8)
    ctx.move_to(-190, 112)
    ctx.line_to(190, 112)
    ctx.stroke()
    _poly(ctx, [(-150, 112), (-100, 52), (-40, 78), (10, 30), (70, 66), (150, 112)])
    _fs(ctx, TENT, 10)
    _st(ctx, 6)
    ctx.move_to(-60, 100)
    ctx.line_to(-20, 82)
    ctx.move_to(40, 100)
    ctx.line_to(80, 80)
    ctx.stroke()
    ctx.save()                                          # varão caído
    ctx.translate(40, 20)
    ctx.rotate(math.radians(-62))
    _st(ctx, 9)
    ctx.move_to(0, 0)
    ctx.line_to(0, -118)
    ctx.stroke()
    _poly(ctx, [(0, -118), (34, -108), (0, -92)])
    _fs(ctx, YELLOW, 6)
    ctx.restore()
    for k in range(3):                                  # estrelinhas de «tontura»
        a = t * 3 + k * 2.09
        _star4(ctx, 6 + math.cos(a) * 70, -62 + math.sin(a) * 18, 19)
        _fs(ctx, YELLOW, 5)
    for k, (x, r) in enumerate(((-170, 22), (175, 28), (-130, 14))):   # poeira
        ctx.arc(x, 96 - 8 * math.sin(t * 2 + k), r, 0, 2 * math.pi)
        ctx.set_source_rgba(0.75, 0.72, 0.66, 0.8)
        ctx.fill()


def _star4(ctx, x, y, r):
    ctx.new_path()
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    _poly(ctx, pts)


def _flame(ctx, x, base, h, w, sway, fill):
    ctx.move_to(x - w, base)
    ctx.curve_to(x - w * 1.1, base - h * 0.45, x - w * 0.2 + sway, base - h * 0.6, x + sway * 1.6, base - h)
    ctx.curve_to(x + w * 0.5 + sway, base - h * 0.55, x + w * 1.1, base - h * 0.4, x + w, base)
    ctx.close_path()
    ctx.set_source_rgb(*fill)


def fogueira(ctx, t):
    f = lambda k: math.sin(t * 9 + k) * 6
    _flame(ctx, 0, 70, 215, 74, f(0), ORANGE)
    ctx.fill_preserve()
    _st(ctx, 9)
    ctx.stroke()
    _flame(ctx, -30, 70, 140, 40, f(1), YELLOW)
    ctx.fill()
    _flame(ctx, 38, 70, 120, 34, f(2), ORANGE)
    ctx.fill()
    _flame(ctx, 0, 70, 95, 30, f(3), (1, 0.95, 0.65))
    ctx.fill()
    for s in (-1, 1):                                    # lenha cruzada
        _st(ctx, 38)
        ctx.move_to(-110, 78 + s * 26)
        ctx.line_to(110, 78 - s * 26)
        ctx.stroke()
        _st(ctx, 24, BROWN)
        ctx.move_to(-110, 78 + s * 26)
        ctx.line_to(110, 78 - s * 26)
        ctx.stroke()
    for k in range(4):                                   # faíscas
        ph = (t * 0.8 + k * 0.27) % 1
        ctx.arc(-50 + k * 34 + math.sin(ph * 6 + k) * 10, 20 - ph * 150, 6 * (1 - ph) + 1, 0, 2 * math.pi)
        ctx.set_source_rgba(*ORANGE, 1 - ph)
        ctx.fill()


def corda(ctx, t):
    """Nó de oito."""
    def pt(u):
        return 105 * math.sin(u), 62 * math.sin(2 * u)
    def path(a, b):
        n = 80
        for i in range(n + 1):
            x, y = pt(a + (b - a) * i / n)
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.save()
    ctx.rotate(math.sin(t * 2) * 0.06)
    for w, col in ((34, INK), (22, (0.80, 0.62, 0.36))):
        _st(ctx, w, col)
        path(0.55, 2 * math.pi - 0.55 + math.pi * 0 )
        ctx.stroke()
    for w, col in ((34, INK), (22, (0.80, 0.62, 0.36))):  # por cima no cruzamento
        _st(ctx, w, col)
        path(math.pi - 0.45, math.pi + 0.45)
        ctx.stroke()
    _st(ctx, 5, BROWN)                                    # tranças
    for k in range(14):
        x, y = pt(0.7 + k * 0.38)
        ctx.arc(x, y, 1, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()


def mochila(ctx, t):
    _st(ctx, 8)
    ctx.arc(0, -125, 34, math.pi, 2 * math.pi)             # pega
    ctx.stroke()
    _rrect(ctx, -95, -118, 190, 238, 42)
    _fs(ctx, GREEN, 10)
    _rrect(ctx, -95, -118, 190, 96, 42)
    _fs(ctx, (0.13, 0.42, 0.25), 10)
    _rrect(ctx, -62, 28, 124, 72, 14)
    _fs(ctx, KHAKI, 8)
    _rrect(ctx, -14, -46, 28, 38, 6)
    _fs(ctx, YELLOW, 7)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(34)
    ex = ctx.text_extents("994")
    ctx.move_to(-ex.width / 2 - ex.x_bearing, 74)
    ctx.set_source_rgb(*INK)
    ctx.show_text("994")
    for s in (-1, 1):                                       # correias
        _st(ctx, 10)
        ctx.move_to(s * 95, -60)
        ctx.curve_to(s * 125, -20, s * 125, 60, s * 95, 100)
        ctx.stroke()


def seta(ctx, t):
    k = math.sin(t * 5) * 10
    ctx.save()
    ctx.translate(k, 0)
    for w, col in ((34, INK), (22, RED)):
        _st(ctx, w, col)
        ctx.move_to(-130, 70)
        ctx.curve_to(-90, -80, 30, -90, 85, -30)
        ctx.stroke()
    _poly(ctx, [(60, -100), (150, -25), (50, 20)])
    _fs(ctx, RED, 10)
    ctx.restore()


def lenco(ctx, t):
    sw = math.sin(t * 3) * 6
    ctx.new_path()
    ctx.move_to(-140, -95)
    ctx.curve_to(-120, 30, -40, 90, sw, 130)
    ctx.curve_to(40, 90, 120, 30, 140, -95)
    ctx.curve_to(60, -60, -60, -60, -140, -95)
    ctx.close_path()
    ctx.set_source_rgb(*GREEN)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    _st(ctx, 52, WHITE)
    ctx.stroke_preserve()
    _st(ctx, 36, YELLOW)
    ctx.stroke_preserve()
    ctx.restore()
    _st(ctx, 10)
    ctx.stroke()
    ctx.arc(0, -66, 20, 0, 2 * math.pi)
    _fs(ctx, BROWN, 8)


def estrela(ctx, t):
    ctx.save()
    ctx.rotate(math.sin(t * 2) * 0.15)
    ctx.new_path()
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 135 if k % 2 == 0 else 58
        pts.append((math.cos(a) * r, math.sin(a) * r + 8))
    _poly(ctx, pts)
    _fs(ctx, YELLOW, 10)
    ctx.restore()


def bussola(ctx, t):
    ctx.arc(0, 0, 118, 0, 2 * math.pi)
    _fs(ctx, (1, 0.99, 0.95), 11)
    ctx.arc(0, 0, 98, 0, 2 * math.pi)
    _st(ctx, 4)
    ctx.stroke()
    for k in range(12):
        a = k * math.pi / 6
        r0 = 80 if k % 3 else 70
        _st(ctx, 5)
        ctx.move_to(math.cos(a) * r0, math.sin(a) * r0)
        ctx.line_to(math.cos(a) * 97, math.sin(a) * 97)
        ctx.stroke()
    ang = math.radians(25) * math.sin(t * 3.2) * math.exp(-t * 0.4) + math.radians(-30)
    ctx.save()
    ctx.rotate(ang)
    _poly(ctx, [(0, -88), (22, 0), (-22, 0)])
    _fs(ctx, RED, 7)
    _poly(ctx, [(0, 88), (22, 0), (-22, 0)])
    _fs(ctx, WHITE, 7)
    ctx.restore()
    ctx.arc(0, 0, 9, 0, 2 * math.pi)
    _fs(ctx, INK, 3)


def trinta_e_cinco(ctx, t):
    ctx.save()
    ctx.rotate(t * 0.25)
    for k in range(16):
        a = k * math.pi / 8
        _st(ctx, 9, YELLOW)
        ctx.move_to(math.cos(a) * 128, math.sin(a) * 128)
        ctx.line_to(math.cos(a) * 158, math.sin(a) * 158)
        ctx.stroke()
    ctx.restore()
    ctx.arc(0, 0, 118, 0, 2 * math.pi)
    _fs(ctx, GREEN, 11)
    ctx.arc(0, 0, 100, 0, 2 * math.pi)
    _st(ctx, 6, YELLOW)
    ctx.stroke()
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(112)
    ex = ctx.text_extents("35")
    ctx.move_to(-ex.width / 2 - ex.x_bearing, 24)
    ctx.set_source_rgb(*YELLOW)
    ctx.show_text("35")
    ctx.set_font_size(30)
    ex = ctx.text_extents("ANOS")
    ctx.move_to(-ex.width / 2 - ex.x_bearing, 66)
    ctx.set_source_rgb(*WHITE)
    ctx.show_text("ANOS")


def pinheiro(ctx, t):
    sw = math.sin(t * 2) * 3
    _st(ctx, 9)
    ctx.rectangle(-18, 80, 36, 50)
    _fs(ctx, BROWN, 8)
    for y, w in ((50, 120), (-10, 100), (-70, 78)):
        _poly(ctx, [(-w, y + 40), (sw, y - 70), (w, y + 40)])
        _fs(ctx, (0.2, 0.55, 0.33), 9)


def texto(ctx, t, label="TEXTO"):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    size = 120
    ctx.set_font_size(size)
    ex = ctx.text_extents(label)
    size = min(size, size * 280 / max(ex.width, 1))
    ctx.set_font_size(size)
    ex = ctx.text_extents(label)
    ctx.move_to(-ex.width / 2 - ex.x_bearing, size * 0.35)
    ctx.text_path(label)
    ctx.set_source_rgb(*YELLOW)
    ctx.fill_preserve()
    _st(ctx, 10)
    ctx.stroke()


PROPS = {"tenda": tenda, "tenda_caida": tenda_caida, "fogueira": fogueira, "corda": corda, "no": corda,
         "mochila": mochila, "seta": seta, "lenco": lenco, "estrela": estrela, "bussola": bussola,
         "35": trinta_e_cinco, "pinheiro": pinheiro, "arvore": pinheiro}


def _back(x):
    c = 1.70158 + 1
    return 1 + c * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


def draw_prop(ctx, name, x, y, size, age, seed=0, shrink=None):
    """Desenha um ícone com animação de entrada «pop». `shrink` (0..1) faz a saída."""
    key = _norm(name)
    if key.startswith("texto:"):
        fn = lambda c, tt: texto(c, tt, name.split(":", 1)[1].strip())
    elif key in PROPS:
        fn = PROPS[key]
    else:
        raise SystemExit(f"Ilustração desconhecida «{name}». Disponíveis: {', '.join(sorted(PROPS))}, texto:...")
    if shrink is not None:
        s = max(0.0, 1 - shrink)
    else:
        if age < 0:
            return
        s = _back(min(age / 0.38, 1.0))
    ctx.save()
    ctx.translate(x, y + math.sin(age * 2.0 + seed) * 4)
    ctx.rotate(math.sin(age * 1.5 + seed) * 0.025)
    ctx.scale(size / 300 * s, size / 300 * s)
    fn(ctx, max(age, 0))
    ctx.restore()

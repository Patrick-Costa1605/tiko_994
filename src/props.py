"""Ilustrações do «quadro»: ícones simples desenhados em vetor (origem no centro, ~300 px)."""
import math
import unicodedata

import cairo

from config import *


def _norm(name):
    s = unicodedata.normalize("NFKD", name.lower().strip()).encode("ascii", "ignore").decode()
    return s.replace(" ", "_").replace("-", "_")


def _st(ctx, w=9, color=INK, alpha=1.0):
    ctx.set_source_rgba(*color, alpha)
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


TENT = mix(LOGO_GREEN, WHITE, 0.25)
LOGO = None   # superfície cairo do logótipo (definida pela cena)


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def tenda(ctx, t):
    """A tenda monta-se sozinha: varões sobem, a lona desdobra-se e a bandeira abre."""
    pr = max(0.0, min(t / 1.15, 1.0))
    _st(ctx, 8)
    ctx.move_to(-190, 112)
    ctx.line_to(190, 112)
    ctx.stroke()
    rise = _ease(pr / 0.35)
    if pr < 0.75:                                       # varões
        _st(ctx, 9, BROWN)
        for s in (-1, 1):
            ctx.move_to(s * 140, 112)
            ctx.line_to(s * 140 * (1 - rise) , 112 - 224 * rise)
            ctx.stroke()
    k = _back2((pr - 0.25) / 0.5)
    ctx.save()
    ctx.translate(0, 112)
    ctx.scale(0.7 + 0.3 * min(k, 1.0), max(k, 0.001))
    ctx.translate(0, -112)
    if k > 0.01:
        _poly(ctx, [(-140, 112), (0, -112), (140, 112)])
        _fs(ctx, TENT, 10)
        _poly(ctx, [(-46, 112), (0, -22), (46, 112)])
        _fs(ctx, (0.16, 0.2, 0.17), 8)
        _st(ctx, 5, mix(TENT, BLACK, 0.4))
        ctx.move_to(-70, 100)
        ctx.line_to(-18, -40)
        ctx.move_to(70, 100)
        ctx.line_to(18, -40)
        ctx.stroke()
    ctx.restore()
    if pr > 0.55:                                       # tirantes + estacas
        f = _ease((pr - 0.55) / 0.3)
        _st(ctx, 6)
        for s in (-1, 1):
            ctx.move_to(s * 78, 20)
            ctx.line_to(s * (78 + 97 * f), 20 + 92 * f)
            ctx.stroke()
            if f > 0.95:
                _poly(ctx, [(s * 175 - 7, 112), (s * 175 + 7, 112), (s * 175, 126)])
                _fs(ctx, BROWN, 4)
    if pr > 0.78:                                       # varão central + bandeira
        f = _back2((pr - 0.78) / 0.22)
        _st(ctx, 7)
        ctx.move_to(0, -112)
        ctx.line_to(0, -112 - 38 * f)
        ctx.stroke()
        fl = math.sin(t * 6) * 5
        ctx.save()
        ctx.translate(0, -150)
        ctx.scale(f, f)
        _poly(ctx, [(0, 0), (40, 10 + fl), (0, 24)])
        _fs(ctx, YELLOW, 6)
        ctx.restore()


def _back2(x):
    x = max(0.0, min(1.0, x))
    return 1 + 2.4 * (x - 1) ** 3 + 1.4 * (x - 1) ** 2


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
    loose = 1 + 0.55 * math.exp(-t * 2.6) * math.cos(t * 13)     # a corda aperta com elasticidade
    ctx.scale(loose, 1 / loose)
    for w, col in ((34, INK), (22, (0.80, 0.62, 0.36))):
        _st(ctx, w, col)
        path(0.55, 2 * math.pi - 0.55)
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



def exclamacao(ctx, t):
    sh = math.sin(t * 28) * 3 * math.exp(-t * 2)
    ctx.save()
    ctx.translate(sh, 0)
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(330)
    e = ctx.text_extents("!")
    ctx.move_to(-e.width / 2 - e.x_bearing, 120)
    ctx.text_path("!")
    ctx.set_source_rgb(*RED)
    ctx.fill_preserve()
    _st(ctx, 14)
    ctx.stroke()
    ctx.restore()
    _st(ctx, 10, YELLOW)
    for k in range(5):
        a = math.radians(-150 + k * 30)
        r0, r1 = 150 + 6 * math.sin(t * 9 + k), 195 + 10 * math.sin(t * 9 + k)
        ctx.move_to(math.cos(a) * r0, 10 + math.sin(a) * r0)
        ctx.line_to(math.cos(a) * r1, 10 + math.sin(a) * r1)
    ctx.stroke()


def estrelas(ctx, t):
    k = _ease(t / 0.55)
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5 + t * 0.6
        r = 105 * k
        ctx.save()
        ctx.translate(math.cos(a) * r, math.sin(a) * r)
        ctx.rotate(t * 2 + i)
        sc = 0.75 + 0.25 * math.sin(t * 7 + i)
        ctx.scale(sc, sc)
        _star5(ctx, 0, 0, 46)
        _fs(ctx, YELLOW, 7)
        ctx.restore()
    _star5(ctx, 0, 0, 62 * k)
    _fs(ctx, YELLOW, 8)


def _star5(ctx, x, y, r):
    ctx.new_path()
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    _poly(ctx, pts)


def logo(ctx, t):
    """Logótipo oficial com brilho: raios rotativos, halo, reflexo a deslizar e cintilações."""
    ctx.save()
    ctx.rotate(t * 0.35)
    for k in range(18):
        a = k * math.pi / 9
        _st(ctx, 12, YELLOW, 0.85)
        r0, r1 = 178, 178 + (26 if k % 2 else 44) + 8 * math.sin(t * 5 + k)
        ctx.move_to(math.cos(a) * r0, math.sin(a) * r0)
        ctx.line_to(math.cos(a) * r1, math.sin(a) * r1)
        ctx.stroke()
    ctx.restore()
    g = cairo.RadialGradient(0, 0, 60, 0, 0, 190)
    g.add_color_stop_rgba(0, 1, 1, 0.9, 0.95)
    g.add_color_stop_rgba(1, *YELLOW, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 190, 0, 2 * math.pi)
    ctx.fill()
    _ellipse(ctx, 0, 0, 125, 168)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    _st(ctx, 8, INK, 0.9)
    ctx.stroke()
    if LOGO is not None:
        h = 300.0
        k = h / LOGO.get_height()
        ctx.save()
        ctx.scale(k, k)
        ctx.push_group()
        ctx.set_source_surface(LOGO, -LOGO.get_width() / 2, -LOGO.get_height() / 2)
        ctx.get_source().set_filter(cairo.FILTER_BEST)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_ATOP)            # reflexo apenas sobre os pixels do logótipo
        ph = (t * 0.55) % 1.6 - 0.3
        sx = (ph - 0.5) * 2.6 * LOGO.get_width()
        gl = cairo.LinearGradient(sx - 30, -80, sx + 30, 80)
        gl.add_color_stop_rgba(0, 1, 1, 1, 0)
        gl.add_color_stop_rgba(0.5, 1, 1, 1, 0.85)
        gl.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(gl)
        ctx.paint()
        ctx.pop_group_to_source()
        ctx.paint()
        ctx.restore()
    for i, (x, y, ph) in enumerate(((-120, -140, 0), (125, -80, 1.3), (95, 150, 2.4))):    # cintilações
        a = max(0.0, math.sin(t * 4 + ph))
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(t)
        ctx.scale(0.4 + 0.6 * a, 0.4 + 0.6 * a)
        ctx.move_to(0, -26)
        for q in range(4):
            ang = q * math.pi / 2
            ctx.line_to(math.sin(ang + math.pi / 4) * 7, -math.cos(ang + math.pi / 4) * 7)
            ctx.line_to(math.sin(ang + math.pi / 2) * 26, -math.cos(ang + math.pi / 2) * 26)
        ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.fill_preserve()
        _st(ctx, 3, YELLOW)
        ctx.stroke()
        ctx.restore()


def _ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


PROPS = {"tenda": tenda, "tenda_caida": tenda_caida, "fogueira": fogueira, "corda": corda, "no": corda,
         "mochila": mochila, "seta": seta, "lenco": lenco, "estrela": estrela, "bussola": bussola,
         "pinheiro": pinheiro, "exclamacao": exclamacao, "estrelas": estrelas, "logo": logo, "arvore": pinheiro}


def _back(x):
    c = 1.70158 + 1
    return 1 + c * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


def draw_prop(ctx, name, x, y, size, age, seed=0, shrink=None):
    """Desenha um ícone com animação «pop» (elástica) e sombra suave. `nome@1.3` = 30% maior."""
    scale_mult = 1.0
    if "@" in name and not name.lower().startswith("texto:"):
        name, m = name.split("@", 1)
        scale_mult = float(m)
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
        s = _back(min(age / 0.45, 1.0))
    size *= scale_mult
    if abs(s) < 0.004:
        return
    ctx.save()
    bob = math.sin(age * 2.0 + seed) * 5
    # sombra no «chão» por baixo do ícone
    ctx.save()
    ctx.translate(x, y + size * 0.50)
    ctx.scale(size * 0.36 * s * (1 - bob / 90), size * 0.05 * s)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.22)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    ctx.translate(x, y + bob)
    ctx.rotate(math.sin(age * 1.5 + seed) * 0.025)
    ctx.scale(size / 300 * s, size / 300 * s)
    fn(ctx, max(age, 0))
    ctx.restore()

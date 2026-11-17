"""Tiko: personagem vetorial (pycairo) com emoções, lip-sync de 5 bocas, lenço com física,
squash & stretch e cinemática inversa nos braços."""
import math

import cairo

from config import *

# ---- geometria (coordenadas locais: origem nos pés, y negativo = para cima)
HEAD_C = (0, -580)
HRX, HRY = 135, 125
NECK_Y = -455
SH_X, SH_Y = 82, -405
HIP_Y = -215
L1, L2 = 150, 140
LOGO = None          # superfície cairo do logótipo (definida pela cena)

# ---- poses / emoções (todos os valores são numéricos => interpoláveis entre blocos)
# brl/brr = sobrancelha esq./dir. (y px, negativo sobe | a graus, + = ponta interior sobe)
# lhx.. = alvo da mão relativo ao centro dos ombros (IK nos braços); salute = 3 dedos levantados
BASE = dict(brl_y=0, brl_a=0, brr_y=0, brr_a=0, eye=1.0, pup=1.0, sparkle=0, sweat=0, qmark=0,
            tilt=0, smile=0.35, open_gain=1.0, lookx=0, looky=0, lhx=-185, lhy=95, rhx=185, rhy=95,
            salute=0, bounce=0, shake=0, gest=0.6, cheeks=0, surprise=0, lean=0)

POSES = {
    "normal": dict(BASE),
    "entusiasmado": dict(BASE, brl_y=-20, brr_y=-20, brl_a=8, brr_a=8, eye=1.12, pup=1.25, sparkle=1,
                         smile=1.0, open_gain=1.15, lhx=-170, lhy=-235, rhx=170, rhy=-235, bounce=1,
                         gest=1.3, cheeks=1, looky=-0.1),
    "confuso": dict(BASE, brl_y=5, brl_a=-14, brr_y=-26, brr_a=12, tilt=8, smile=-0.05, qmark=1,
                    lhx=-165, lhy=125, rhx=52, rhy=-62, gest=0.12, lookx=0.7, looky=-0.7, open_gain=0.8),
    "assustado": dict(BASE, brl_y=-30, brr_y=-30, brl_a=22, brr_a=22, eye=1.3, pup=0.5, sweat=1,
                      smile=-0.6, shake=1, lhx=-150, lhy=-100, rhx=150, rhy=-100, gest=0.3, open_gain=1.2,
                      surprise=0.8),
    "saudacao": dict(BASE, brl_y=-10, brr_y=-12, brl_a=4, brr_a=4, smile=0.9, cheeks=0.6,
                     rhx=190, rhy=-215, salute=1, lhx=-170, lhy=110, gest=0.12),
    "orgulhoso": dict(BASE, brl_y=-8, brr_y=-8, brl_a=-4, brr_a=-4, smile=0.85, cheeks=0.5, tilt=-4,
                      rhx=14, rhy=12, lhx=-150, lhy=60, gest=0.2, lean=1, looky=-0.15, sparkle=0.4),
}
ALIASES = {"entusiasta": "entusiasmado", "feliz": "entusiasmado", "medo": "assustado",
           "duvida": "confuso", "dúvida": "confuso", "saudação": "saudacao", "continencia": "saudacao",
           "orgulho": "orgulhoso", "ajeita_lenco": "orgulhoso"}
SQUASH = {"entusiasmado": 0.13, "assustado": -0.10, "confuso": 0.04, "saudacao": 0.07, "orgulhoso": 0.07,
          "normal": 0.04}
LADO = {"centro": 0, "esquerda": -TIKO_SIDE, "direita": TIKO_SIDE}


def get_pose(name):
    name = ALIASES.get(name, name)
    if name not in POSES:
        raise SystemExit(f"Estado desconhecido «{name}». Disponíveis: {', '.join(POSES)}")
    return POSES[name]


def estado_key(name):
    return ALIASES.get(name, name)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x, c=1.4):
    x = clamp(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def _block_index(blocks, t):
    idx = 0
    for i, b in enumerate(blocks):
        if t >= b["vstart"]:
            idx = i
    return idx


def pose_at(blocks, t, trans=0.30):
    """Pose interpolada em t (função pura => renderização paralela segura)."""
    idx = _block_index(blocks, t)
    cur = get_pose(blocks[idx]["estado"])
    if idx == 0:
        return cur
    prev = get_pose(blocks[idx - 1]["estado"])
    k = ease((t - blocks[idx]["vstart"]) / trans)
    return {key: prev[key] + (cur[key] - prev[key]) * k for key in cur}


def tiko_dx(blocks, t):
    """Deslocação lateral suave (com ligeiro overshoot) quando entra/sai uma ilustração."""
    idx = _block_index(blocks, t)
    cur = blocks[idx]["tiko_dx"]
    if idx == 0:
        return cur
    prev = blocks[idx - 1]["tiko_dx"]
    return prev + (cur - prev) * back((t - blocks[idx]["vstart"]) / 0.55, 1.0)


def intro_motion(t):
    """Entrada em salto: (dy_px, squash)."""
    T = 0.55
    dy = 900 * (1 - back(t / T, 1.7)) if t < T else 0.0
    q = -0.12 * clamp(1 - t / 0.40)
    if t > 0.42:
        dt = t - 0.42
        q += 0.17 * math.exp(-9 * dt) * math.cos(24 * dt)
    return dy, q


def squash_at(blocks, t):
    idx = _block_index(blocks, t)
    if idx == 0:
        return 0.0
    dt = t - blocks[idx]["vstart"]
    A = SQUASH.get(estado_key(blocks[idx]["estado"]), 0.04)
    return A * math.exp(-9 * dt) * math.cos(20 * dt)


def body_motion(t, p):
    """(bx, by, jump) em unidades locais; by>0 = para baixo."""
    bx = math.sin(t * 1.3) * 4 + p["shake"] * math.sin(t * 63) * 5
    by = math.sin(t * 2.2) * 3 + p["shake"] * math.sin(t * 51) * 3
    jump = p["bounce"] * abs(math.sin(t * 6.3)) * 36
    return bx, by, jump


# ------------------------------------------------------------------ helpers
def _st(ctx, w, color=INK, alpha=1.0):
    ctx.set_source_rgba(*color, alpha)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)


def _capsule(ctx, pts, w, fill, ow=6):
    for width, col in ((w + 2 * ow, INK), (w, fill)):
        _st(ctx, width, col)
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.stroke()


def _fs(ctx, fill, w=7):
    ctx.set_source_rgb(*fill)
    ctx.fill_preserve()
    _st(ctx, w)
    ctx.stroke()


def _ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def _star4(ctx, x, y, r, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.move_to(0, -r)
    for k in range(4):
        a = k * math.pi / 2
        ctx.line_to(math.sin(a + math.pi / 4) * r * 0.28, -math.cos(a + math.pi / 4) * r * 0.28)
        ctx.line_to(math.sin(a + math.pi / 2) * r, -math.cos(a + math.pi / 2) * r)
    ctx.close_path()
    ctx.restore()


def _ik(shoulder, target, side):
    sx, sy = shoulder
    dx, dy = target[0] - sx, target[1] - sy
    dist = math.hypot(dx, dy) or 1.0
    d = min(max(dist, 70), L1 + L2 - 3)
    ux, uy = dx / dist, dy / dist
    hand = (sx + ux * d, sy + uy * d)
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    h = math.sqrt(max(L1 * L1 - a * a, 0))
    cands = [(sx + ux * a - uy * h, sy + uy * a + ux * h), (sx + ux * a + uy * h, sy + uy * a - ux * h)]
    elbow = max(cands, key=lambda e: side * (e[0] - sx) + (e[1] - sy) * 0.35)
    return elbow, hand


def _blink(t):
    v = 0.0
    for period, off in ((3.4, 0.7), (5.3, 2.1), (7.9, 4.4)):
        ph = (t + off) % period
        if ph < 0.16:
            v = max(v, math.sin(math.pi * ph / 0.16))
    return 1 - 0.95 * v


# ------------------------------------------------------------------ boca (5 formas)
# (meia-largura, altura lábio sup., profundidade lábio inf., elevação dos cantos, arredondamento)
MOUTH = {"ao": (40, 10, 64, 0, 1.0), "ei": (68, 8, 30, 4, 0.1),
         "sorriso": (66, 8, 48, 18, 0.5), "surpresa": (32, 26, 78, 0, 1.0)}


def _mix_shape(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def _draw_mouth(ctx, o, vow, smile, surprise, t):
    cy = 75
    o = clamp(o)
    if o < 0.06 and surprise < 0.4:                      # fechada (sorriso ou trémula)
        _st(ctx, 8, INK)
        if smile >= 0:
            w = 54 + smile * 14
            ctx.move_to(-w, cy - smile * 9)
            ctx.curve_to(-w * 0.5, cy + 8 + smile * 30, w * 0.5, cy + 8 + smile * 30, w, cy - smile * 9)
        else:
            n = 8
            for i in range(n + 1):
                x = -50 + 100 * i / n
                y = cy + 4 - (-smile) * 8 * (1 - (2 * i / n - 1) ** 2) + (-smile) * 5 * math.sin(t * 38 + i * 1.7)
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.stroke()
        return
    shape = _mix_shape(MOUTH["ao"], MOUTH["ei"], vow)
    shape = _mix_shape(shape, MOUTH["sorriso"], clamp(smile) * 0.75)
    shape = _mix_shape(shape, MOUTH["surpresa"], clamp(surprise) * 0.9)
    a, ht, hb, lift, r = shape
    o = max(o, surprise * 0.45)
    ht *= 0.45 + 0.55 * o
    hb = 5 + hb * o
    k = 0.55 + 0.35 * r

    def path():
        ctx.new_path()
        ctx.move_to(-a, cy - lift)
        ctx.curve_to(-a * 0.5, cy - lift - ht * 1.33, a * 0.5, cy - lift - ht * 1.33, a, cy - lift)
        ctx.curve_to(a * k, cy - lift + hb * 1.33, -a * k, cy - lift + hb * 1.33, -a, cy - lift)
        ctx.close_path()

    path()
    ctx.save()
    ctx.set_source_rgb(0.22, 0.07, 0.09)
    ctx.fill_preserve()
    ctx.clip()
    if hb > 26:                                           # língua
        ctx.set_source_rgb(*PINK)
        _ellipse(ctx, 0, cy - lift + hb * 0.85, a * 0.6, hb * 0.34)
        ctx.fill()
    if hb > 14 and vow > 0.25:                            # dentes (E/I e sorriso)
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(-a * 0.7, cy - lift - ht, a * 1.4, min(hb * 0.32 + ht, 20))
        ctx.fill()
    ctx.restore()
    path()
    _st(ctx, 8, INK)
    ctx.stroke()


# ------------------------------------------------------------------ cabeça
def _draw_hat(ctx):
    ctx.save()
    ctx.translate(0, -100)
    ctx.rotate(math.radians(-7))
    # aba
    _ellipse(ctx, 0, 0, 182, 31)
    g = cairo.LinearGradient(-180, 0, 180, 0)
    g.add_color_stop_rgb(0, *mix(KHAKI, BLACK, 0.12))
    g.add_color_stop_rgb(0.5, *mix(KHAKI, WHITE, 0.15))
    g.add_color_stop_rgb(1, *mix(KHAKI, BLACK, 0.12))
    ctx.set_source(g)
    ctx.fill_preserve()
    _st(ctx, 9)
    ctx.stroke()
    # copa
    ctx.move_to(-100, 4)
    ctx.curve_to(-108, -78, -66, -96, 0, -96)
    ctx.curve_to(66, -96, 108, -78, 100, 4)
    ctx.curve_to(60, 16, -60, 16, -100, 4)
    ctx.close_path()
    g = cairo.LinearGradient(-100, 0, 100, 0)
    g.add_color_stop_rgb(0, *mix(KHAKI, BLACK, 0.1))
    g.add_color_stop_rgb(0.4, *mix(KHAKI, WHITE, 0.2))
    g.add_color_stop_rgb(1, *mix(KHAKI, BLACK, 0.15))
    ctx.set_source(g)
    ctx.fill_preserve()
    _st(ctx, 9)
    ctx.stroke()
    # fita nas cores do lenço
    ctx.move_to(-102, -22)
    ctx.curve_to(-50, -6, 50, -6, 102, -22)
    ctx.line_to(99, -1)
    ctx.curve_to(50, 14, -50, 14, -99, -1)
    ctx.close_path()
    _fs(ctx, SCARF, 6)
    _st(ctx, 4, TRIM)
    ctx.move_to(-100, -11)
    ctx.curve_to(-50, 4, 50, 4, 100, -11)
    ctx.stroke()
    ctx.restore()


def _draw_eyes(ctx, t, p):
    blink = _blink(t)
    for side in (-1, 1):
        ex, ey = side * 50, -6
        rx, ry = 30 * p["eye"], 35 * p["eye"]
        ctx.save()
        ctx.translate(ex, ey)
        ctx.scale(1, max(blink, 0.06))
        _ellipse(ctx, 0, 0, rx, ry)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        if blink > 0.45:
            ir = 20 * min(p["pup"] * 0.5 + 0.6, 1.3)
            reachx, reachy = max(rx - ir - 2, 0), max(ry - ir - 2, 0)
            jx = math.sin(t * 1.7 + side) * 0.15 + (math.sin(t * 6.1) > 0.97) * 0.3
            jy = math.sin(t * 1.3) * 0.1
            px = clamp(p["lookx"] + jx, -1, 1) * reachx
            py = clamp(p["looky"] + jy, -1, 1) * reachy
            _ellipse(ctx, px, py, ir, ir)
            ctx.set_source_rgb(0.36, 0.22, 0.13)
            ctx.fill()
            _ellipse(ctx, px, py, 11 * p["pup"], 11 * p["pup"])
            ctx.set_source_rgb(0.04, 0.03, 0.03)
            ctx.fill()
            ctx.set_source_rgb(1, 1, 1)
            if p["sparkle"] > 0.05:
                _star4(ctx, px - 5, py - 7, 11 * (0.7 + 0.3 * math.sin(t * 9 + side)) * (0.5 + 0.5 * p["sparkle"]), t * 1.5)
                ctx.fill()
                _ellipse(ctx, px + 8, py + 8, 3.5, 3.5)
                ctx.fill()
            else:
                _ellipse(ctx, px - 6, py - 7, 5.5, 5.5)
                ctx.fill()
                _ellipse(ctx, px + 7, py + 7, 2.5, 2.5)
                ctx.fill()
        ctx.restore()
        _ellipse(ctx, 0, 0, rx, ry)
        _st(ctx, 7)
        ctx.stroke()
        ctx.restore()
        # pálpebra superior / pestana
        _st(ctx, 9)
        ctx.arc(ex, ey + (1 - blink) * ry * 0.3, rx + 2, math.radians(205), math.radians(335))
        ctx.stroke()
        if p["sparkle"] > 0.05:                           # raios de entusiasmo
            _st(ctx, 6, TRIM)
            for k in range(3):
                a = math.radians(-135 + k * 38) if side < 0 else math.radians(-45 - k * 38)
                a += 0.12 * math.sin(t * 8 + k)
                ctx.move_to(ex + math.cos(a) * (ry + 16), ey + math.sin(a) * (ry + 16))
                ctx.line_to(ex + math.cos(a) * (ry + 34), ey + math.sin(a) * (ry + 34))
            ctx.stroke()


def _draw_brows(ctx, p):
    for side, y, a in ((-1, p["brl_y"], p["brl_a"]), (1, p["brr_y"], p["brr_a"])):
        cx, cy = side * 50, -62 + y
        ar = math.radians(a)
        half = 31
        ix, iy = cx - side * math.cos(ar) * half, cy - math.sin(ar) * half
        ox, oy = cx + side * math.cos(ar) * half, cy + math.sin(ar) * half
        _st(ctx, 13, HAIR)
        ctx.move_to(ox, oy)
        ctx.curve_to(ox + (ix - ox) * 0.3, oy + (iy - oy) * 0.3 - 8, ox + (ix - ox) * 0.7, oy + (iy - oy) * 0.7 - 8, ix, iy)
        ctx.stroke()


def _draw_head(ctx, t, p, mo, vow, hat):
    ctx.save()
    ctx.translate(*HEAD_C)
    for s in (-1, 1):                                     # orelhas
        _ellipse(ctx, s * (HRX - 2), 8, 22, 26)
        _fs(ctx, SKIN_SHADE, 7)
    _ellipse(ctx, 0, 0, HRX, HRY)
    g = cairo.RadialGradient(-35, -45, 20, 0, 0, 170)
    g.add_color_stop_rgb(0, *SKIN_LIGHT)
    g.add_color_stop_rgb(0.6, *SKIN)
    g.add_color_stop_rgb(1, *SKIN_SHADE)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    ctx.new_path()                                        # cabelo
    ctx.move_to(-HRX - 6, -10)
    ctx.curve_to(-HRX - 6, -HRY - 24, HRX + 6, -HRY - 24, HRX + 6, -10)
    ctx.curve_to(HRX - 14, -52, 98, -78, 64, -54)
    ctx.curve_to(42, -84, 6, -74, -16, -56)
    ctx.curve_to(-38, -82, -90, -74, -HRX - 6, -10)
    ctx.close_path()
    ctx.set_source_rgb(*HAIR)
    ctx.fill()
    ctx.restore()
    _ellipse(ctx, 0, 0, HRX, HRY)
    _st(ctx, 10)
    ctx.stroke()
    if p["cheeks"] > 0.02:
        for s in (-1, 1):
            _ellipse(ctx, s * 88, 40, 20, 13)
            ctx.set_source_rgba(*PINK, 0.5 * min(p["cheeks"], 1))
            ctx.fill()
    _st(ctx, 6, SKIN_SHADE)                               # nariz
    ctx.move_to(-8, 36)
    ctx.curve_to(-2, 46, 10, 46, 14, 36)
    ctx.stroke()
    _draw_brows(ctx, p)
    _draw_eyes(ctx, t, p)
    _draw_mouth(ctx, mo * p["open_gain"], vow, p["smile"], p["surprise"], t)
    if hat:
        _draw_hat(ctx)
    if p["qmark"] > 0.02:                                 # ponto de interrogação
        q = min(p["qmark"], 1)
        ctx.save()
        ctx.translate(210, -115 + math.sin(t * 3.2) * 12)
        ctx.rotate(math.radians(12 * math.sin(t * 2.4)))
        s = q * (1 + 0.08 * math.sin(t * 6))
        ctx.scale(s, s)
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(170)
        e = ctx.text_extents("?")
        ctx.move_to(-e.width / 2 - e.x_bearing, e.height / 2)
        ctx.text_path("?")
        ctx.set_source_rgb(*TRIM)
        ctx.fill_preserve()
        _st(ctx, 9)
        ctx.stroke()
        ctx.restore()
    if p["sweat"] > 0.02:                                 # gotas de suor
        for i, (x0, y0, off) in enumerate(((98, -70, 0.0), (-104, -40, 0.5))):
            ph = (t * 0.9 + off) % 1.0
            a = min(p["sweat"], 1) * (1 - max(0, ph - 0.75) * 4)
            ctx.save()
            ctx.translate(x0, y0 + ph * 95)
            ctx.move_to(0, -30)
            ctx.curve_to(22, 0, 22, 22, 0, 22)
            ctx.curve_to(-22, 22, -22, 0, 0, -30)
            ctx.close_path()
            ctx.set_source_rgba(*SKY, a)
            ctx.fill_preserve()
            ctx.set_source_rgba(*INK, a)
            ctx.set_line_width(7)
            ctx.stroke()
            ctx.restore()
    ctx.restore()


# ------------------------------------------------------------------ lenço escutista
def _flap(ctx, ax, ay, base, theta, length, wtop, curl):
    ctx.save()
    ctx.translate(ax, ay)
    ctx.rotate(base + theta)

    def path():
        ctx.new_path()
        ctx.move_to(-wtop / 2, 0)
        ctx.curve_to(-wtop / 2 - 8, length * 0.45, -12 + curl, length * 0.82, curl, length)
        ctx.curve_to(12 + curl, length * 0.82, wtop / 2 + 8, length * 0.45, wtop / 2, 0)
        ctx.curve_to(wtop * 0.2, -8, -wtop * 0.2, -8, -wtop / 2, 0)
        ctx.close_path()

    g = cairo.LinearGradient(-wtop / 2, 0, wtop / 2, 0)
    g.add_color_stop_rgb(0, *SCARF_DARK)
    g.add_color_stop_rgb(0.35, *SCARF_LIGHT)
    g.add_color_stop_rgb(0.7, *SCARF)
    g.add_color_stop_rgb(1, *SCARF_DARK)
    path()
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    _st(ctx, 30, TRIM)                                    # debrum amarelo nos bordos
    ctx.stroke_preserve()
    ctx.restore()
    ctx.save()
    path()
    ctx.clip()
    _st(ctx, 4, SCARF_DARK, 0.55)                         # dobras suaves
    ctx.move_to(-wtop * 0.12, 8)
    ctx.curve_to(-wtop * 0.2, length * 0.4, curl * 0.5 - 8, length * 0.7, curl * 0.6 - 4, length * 0.86)
    ctx.move_to(wtop * 0.16, 8)
    ctx.curve_to(wtop * 0.28, length * 0.4, curl * 0.5 + 10, length * 0.7, curl * 0.6 + 6, length * 0.82)
    ctx.stroke()
    _st(ctx, 7, WHITE, 0.22)
    ctx.move_to(-4, 18)
    ctx.curve_to(-8, length * 0.35, curl * 0.4 - 4, length * 0.55, curl * 0.4 - 2, length * 0.66)
    ctx.stroke()
    ctx.restore()
    path()
    _st(ctx, 7)
    ctx.stroke()
    ctx.restore()


def _draw_scarf(ctx, t, env, sc):
    thL, thR, lift = sc
    wind = math.sin(t * 3.1) * 0.035
    _flap(ctx, -16, -408, 0.13 + lift * 0.08, thL + wind, 168, 86, 9 * math.sin(t * 2.3 + 1) + thL * 60)
    _flap(ctx, 16, -408, -0.13 - lift * 0.08, thR - wind * 0.8, 190, 86, -7 * math.sin(t * 2.1) + thR * 60)
    # gola enrolada à volta do pescoço (com volume)
    def collar():
        ctx.new_path()
        ctx.move_to(-102, -476)
        ctx.curve_to(-62, -438, -30, -420, 0, -420)
        ctx.curve_to(30, -420, 62, -438, 102, -476)
    collar()
    _st(ctx, 50, INK)
    ctx.stroke()
    collar()
    _st(ctx, 42, SCARF_DARK)
    ctx.stroke()
    ctx.save()
    ctx.translate(0, -3)
    collar()
    _st(ctx, 28, SCARF)
    ctx.stroke()
    ctx.restore()
    ctx.save()
    ctx.translate(0, -9)
    collar()
    _st(ctx, 10, SCARF_LIGHT, 0.7)
    ctx.stroke()
    ctx.restore()
    ctx.save()
    ctx.translate(0, 15)
    collar()
    _st(ctx, 5, TRIM)
    ctx.stroke()
    ctx.restore()
    # nó: tecido a passar pela argola (passador)
    ctx.move_to(-36, -440)
    ctx.curve_to(-30, -420, -22, -410, -15, -398)
    ctx.line_to(15, -398)
    ctx.curve_to(22, -410, 30, -420, 36, -440)
    ctx.close_path()
    _fs(ctx, SCARF, 7)
    _st(ctx, 4, SCARF_DARK, 0.6)
    ctx.move_to(-8, -436)
    ctx.line_to(-6, -400)
    ctx.move_to(9, -436)
    ctx.line_to(7, -400)
    ctx.stroke()
    # argola
    _ellipse(ctx, 0, -398, 21, 24)
    _st(ctx, 17, INK)
    ctx.stroke()
    _ellipse(ctx, 0, -398, 21, 24)
    _st(ctx, 10, BROWN)
    ctx.stroke()
    ctx.arc(0, -398, 21, math.radians(200), math.radians(260))
    _st(ctx, 3.5, mix(BROWN, WHITE, 0.55))
    ctx.stroke()


# ------------------------------------------------------------------ mãos de 4 dedos
def _draw_hand(ctx, hand, elbow, side, salute, t, gest):
    hx, hy = hand
    A = math.atan2(hy - elbow[1], hx - elbow[0])
    curl = 0.25 + 0.15 * math.sin(t * 7 + side) * gest
    spread = 0.34 * (1 - salute) + 0.17 * salute
    digits = []
    for k, ln in zip((-1, 0, 1), (30, 35, 30)):
        digits.append((A + k * spread, ln * (1 - 0.5 * curl * (1 - salute)) + 4 * salute))
    th = A - side * (1.15 * (1 - salute) + 1.9 * salute)
    digits.append((th, 23 * (1 - salute) + 13 * salute))
    for ang, ln in digits:
        sx, sy = hx + math.cos(ang) * 8, hy + math.sin(ang) * 8
        _capsule(ctx, [(sx, sy), (hx + math.cos(ang) * (8 + ln), hy + math.sin(ang) * (8 + ln))], 9, SKIN, 5)
    _ellipse(ctx, hx, hy, 19, 18)
    _fs(ctx, SKIN, 6)


# ------------------------------------------------------------------ figura completa
def draw_tiko(ctx, t, blocks, mouth_o, vowel, scarf, hat=True):
    p = pose_at(blocks, t)
    dx = tiko_dx(blocks, t)
    idy, iq = intro_motion(t)
    bx, by, jump = body_motion(t, p)
    ph = abs(math.sin(t * 6.3))
    q = iq + squash_at(blocks, t) + p["bounce"] * (0.09 * (1 - ph) ** 4 - 0.04 * ph * ph)
    env = mouth_o
    S = TIKO_SCALE

    gx = 540 + dx + bx * S
    # sombra suave no chão
    sh = max(0.35, 1 - (jump * S + max(-idy, 0)) / 260)
    ctx.save()
    ctx.translate(gx, GROUND_Y + 10 + max(idy, 0))
    ctx.scale(170 * sh, 24 * sh)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.30)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()

    ctx.save()
    ctx.translate(gx, GROUND_Y + idy - jump * S)
    ctx.rotate(math.radians(p["lean"] * 2.0 * math.sin(t * 1.5)))
    ctx.scale(S * (1 + q), S * (1 - q))
    ctx.translate(0, by + p["lean"] * -4)

    # pernas, sapatos, calções
    for s in (-1, 1):
        _capsule(ctx, [(s * 40, -225), (s * 62, -35)], 26, SKIN, 6)
    for s in (-1, 1):
        ctx.new_path()
        _ellipse(ctx, s * 76, -17, 42, 22)
        _fs(ctx, SHOE, 7)
        _st(ctx, 5, mix(SHOE, BLACK, 0.4))
        ctx.move_to(s * 40, -8)
        ctx.line_to(s * 112, -8)
        ctx.stroke()
    for s in (-1, 1):
        _capsule(ctx, [(s * 38, -222), (s * 52, -150)], 54, SHORTS, 6)
    # camisa (torso)
    ctx.new_path()
    ctx.move_to(-SH_X - 10, -432)
    ctx.curve_to(-100, -450, 100, -450, SH_X + 10, -432)
    ctx.curve_to(94, -380, 82, -290, 76, -205)
    ctx.curve_to(30, -190, -30, -190, -76, -205)
    ctx.curve_to(-82, -290, -94, -380, -SH_X - 10, -432)
    ctx.close_path()
    g = cairo.LinearGradient(-90, 0, 90, 0)
    g.add_color_stop_rgb(0, *SHIRT_DARK)
    g.add_color_stop_rgb(0.4, *SHIRT)
    g.add_color_stop_rgb(1, *SHIRT_DARK)
    ctx.set_source(g)
    ctx.fill_preserve()
    _st(ctx, 8)
    ctx.stroke()
    _st(ctx, 6, mix(SHORTS, BLACK, 0.3))                  # cinto
    ctx.move_to(-76, -208)
    ctx.curve_to(-30, -192, 30, -192, 76, -208)
    ctx.stroke()
    if LOGO is not None:                                  # crachá com o logótipo no peito
        ctx.save()
        ctx.translate(-66, -330)
        k = 46 / LOGO.get_height()
        ctx.scale(k, k)
        ctx.set_source_surface(LOGO, -LOGO.get_width() / 2, -LOGO.get_height() / 2)
        ctx.paint()
        ctx.restore()

    # cabeça (inclina à volta do pescoço; acena ao falar)
    ctx.save()
    ctx.translate(0, NECK_Y)
    ctx.rotate(math.radians(p["tilt"] + math.sin(t * 2.7) * 1.6 + env * 1.5 * math.sin(t * 9)))
    ctx.translate(0, -NECK_Y + env * 2.5)
    _capsule(ctx, [(0, -470), (0, -440)], 44, SKIN_SHADE, 5)
    _draw_head(ctx, t, p, mouth_o, vowel, hat)
    ctx.restore()

    # braços com IK + gesticulação proporcional à fala
    drive = p["gest"] * (0.35 + env)
    arms = []
    for side, tx, ty, phs in ((-1, p["lhx"], p["lhy"], 0.0), (1, p["rhx"], p["rhy"], 1.7)):
        d = drive * (0.35 if (side == 1 and p["salute"] > 0.5) else 1.0)
        tx += d * 26 * math.sin(t * 5.1 + phs)
        ty += d * 30 * math.sin(t * 4.3 + phs * 1.3)
        if side == 1 and p["lean"] > 0.5:                 # «ajeitar o lenço» com orgulho
            tx += 5 * math.sin(t * 9)
            ty += 9 * math.sin(t * 9 + 1)
        sh = (side * SH_X, SH_Y)
        elbow, hand = _ik(sh, (tx, SH_Y + ty), side)
        arms.append((side, elbow, hand))
        _capsule(ctx, [sh, elbow, hand], 21, SKIN, 6)
        mid = (sh[0] + (elbow[0] - sh[0]) * 0.5, sh[1] + (elbow[1] - sh[1]) * 0.5)
        _capsule(ctx, [(sh[0], sh[1] - 2), mid], 40, SHIRT, 6)   # manga

    _draw_scarf(ctx, t, env, scarf)
    for side, elbow, hand in arms:
        _draw_hand(ctx, hand, elbow, side, p["salute"] if side == 1 else 0.0, t, p["gest"])
    ctx.restore()

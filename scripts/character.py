"""Tiko: boneco de pauzinhos vetorial (pycairo) com emoções, lip-sync e lenço escutista."""
import math

import cairo

from config import *

HEAD_CY = NECK[1] - 125            # centro da cabeça
SHOULDER = (NECK[0], NECK[1] + 45)
HIP = (NECK[0], NECK[1] + 240)
L1, L2 = 150, 140                  # braço / antebraço

# ------------------------------------------------------------------ poses / emoções
# Todos os valores são numéricos para poderem ser interpolados entre blocos do guião.
# brl/brr = sobrancelha esq./dir. (y: px, negativo = sobe | a: graus, + = ponta interior sobe)
# lhx,lhy / rhx,rhy = posição-alvo da mão relativa ao ombro (cinemática inversa nos braços)
BASE = dict(brl_y=0, brl_a=0, brr_y=0, brr_a=0, eye=1.0, pup=1.0, sparkle=0, sweat=0, qmark=0,
            tilt=0, smile=0.3, open_gain=1.0, lookx=0, looky=0, lhx=-175, lhy=95, rhx=175, rhy=95,
            fingers=0, bounce=0, shake=0, gest=0.6, cheeks=0)

POSES = {
    "normal": dict(BASE),
    "entusiasmado": dict(BASE, brl_y=-22, brr_y=-22, brl_a=8, brr_a=8, eye=1.15, pup=1.3, sparkle=1,
                         smile=1.0, open_gain=1.15, lhx=-150, lhy=-215, rhx=150, rhy=-215, bounce=1,
                         gest=1.3, cheeks=1, lookx=0, looky=-0.1),
    "confuso": dict(BASE, brl_y=5, brl_a=-14, brr_y=-26, brr_a=12, tilt=8, smile=-0.05, qmark=1,
                    lhx=-150, lhy=125, rhx=70, rhy=-38, gest=0.15, lookx=0.7, looky=-0.7, open_gain=0.8),
    "assustado": dict(BASE, brl_y=-30, brr_y=-30, brl_a=22, brr_a=22, eye=1.38, pup=0.5, sweat=1,
                      smile=-0.6, shake=1, lhx=-130, lhy=-120, rhx=130, rhy=-120, gest=0.3, open_gain=1.2),
    "saudacao": dict(BASE, brl_y=-10, brr_y=-12, brl_a=4, brr_a=4, smile=0.9, cheeks=0.6,
                     rhx=165, rhy=-200, fingers=1, lhx=-150, lhy=110, gest=0.12),
}
ALIASES = {"entusiasta": "entusiasmado", "feliz": "entusiasmado", "medo": "assustado",
           "duvida": "confuso", "dúvida": "confuso", "saudação": "saudacao", "continencia": "saudacao"}


def get_pose(name):
    name = ALIASES.get(name, name)
    if name not in POSES:
        raise SystemExit(f"Estado desconhecido «{name}». Disponíveis: {', '.join(POSES)}")
    return POSES[name]


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def pose_at(blocks, t, trans=0.28):
    """Pose interpolada no instante t (função pura => renderização paralela segura)."""
    idx = 0
    for i, b in enumerate(blocks):
        if t >= b["vstart"]:
            idx = i
    cur = get_pose(blocks[idx]["estado"])
    if idx == 0:
        return cur
    prev = get_pose(blocks[idx - 1]["estado"])
    k = _ease((t - blocks[idx]["vstart"]) / trans)
    return {key: prev[key] + (cur[key] - prev[key]) * k for key in cur}


# ------------------------------------------------------------------ helpers de desenho
def _stroke_style(ctx, w=LINE, color=INK):
    ctx.set_source_rgb(*color)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)


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
    elbow = max(cands, key=lambda e: side * (e[0] - sx) * 1.0 + (e[1] - sy) * 0.35)
    return elbow, hand


def _blink(t):
    v = 0.0
    for period, off in ((3.4, 0.7), (5.3, 2.1)):
        ph = (t + off) % period
        if ph < 0.15:
            v = max(v, math.sin(math.pi * ph / 0.15))
    return 1 - 0.92 * v


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


def _fill_stroke(ctx, fill, w=10, stroke=INK, preserve=False):
    ctx.set_source_rgb(*fill)
    ctx.fill_preserve()
    _stroke_style(ctx, w, stroke)
    ctx.stroke()


# ------------------------------------------------------------------ partes do corpo
def _draw_mouth(ctx, o, wf, smile, t, gain):
    """Boca em coordenadas locais da cabeça, centro em (0, 72).

    o  = abertura do lip-sync (0..1)      wf = largura (0..1)       smile = -1..1
    Estados: fechada · semi-aberta · aberta · sorriso (interpolados continuamente).
    """
    o = min(1.0, o * gain)
    cy = 72
    wid = 62 + 14 * wf - 10 * o
    if o < 0.06:                                    # fechada / sorriso / medo
        _stroke_style(ctx, 9)
        if smile >= 0:
            ctx.move_to(-wid * 0.8, cy - smile * 8)
            ctx.curve_to(-wid * 0.4, cy + 6 + smile * 24, wid * 0.4, cy + 6 + smile * 24, wid * 0.8, cy - smile * 8)
        else:                                       # trémulo (medo / dúvida)
            n = 7
            for i in range(n + 1):
                x = -wid * 0.8 + 2 * wid * 0.8 * i / n
                y = cy + 2 + (-smile) * 6 * math.sin(t * 38 + i * 1.7) + (-smile) * 7 * (1 - (2 * i / n - 1) ** 2) * -1
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.stroke()
        return
    h = 8 + o * 62
    lift = max(smile, 0) * 11 * (1 - o * 0.4)
    ctx.new_path()
    ctx.move_to(-wid, cy - lift)
    ctx.curve_to(-wid * 0.5, cy - h * 0.18 - lift, wid * 0.5, cy - h * 0.18 - lift, wid, cy - lift)
    ctx.curve_to(wid * 0.75, cy + h * 1.05, -wid * 0.75, cy + h * 1.05, -wid, cy - lift)
    ctx.close_path()
    ctx.save()
    ctx.set_source_rgb(0.17, 0.09, 0.09)
    ctx.fill_preserve()
    ctx.clip()
    if h > 26:                                      # língua
        ctx.set_source_rgb(*PINK)
        ctx.save()
        ctx.translate(0, cy + h * 0.78)
        ctx.scale(wid * 0.55, h * 0.30)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    if h > 16:                                      # dentes de cima
        ctx.set_source_rgb(1, 1, 1)
        ctx.rectangle(-wid * 0.6, cy - h * 0.22 - lift, wid * 1.2, min(h * 0.28, 15))
        ctx.fill()
    ctx.restore()
    _stroke_style(ctx, 8)
    ctx.move_to(-wid, cy - lift)
    ctx.curve_to(-wid * 0.5, cy - h * 0.18 - lift, wid * 0.5, cy - h * 0.18 - lift, wid, cy - lift)
    ctx.curve_to(wid * 0.75, cy + h * 1.05, -wid * 0.75, cy + h * 1.05, -wid, cy - lift)
    ctx.close_path()
    ctx.stroke()


def _draw_eyes(ctx, t, p):
    blink = _blink(t)
    for side in (-1, 1):
        ex, ey = side * 52, 2
        r = 30 * p["eye"]
        ctx.save()
        ctx.translate(ex, ey)
        ctx.scale(1, max(blink, 0.08))
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill_preserve()
        _stroke_style(ctx, 8)
        ctx.stroke()
        if blink > 0.5:
            pr = 13 * p["pup"]
            reach = max(r - pr - 4, 0)
            # sacadas subtis: o olhar «vagueia» um pouco
            jx = math.sin(t * 1.7 + side) * 0.18 + (math.sin(t * 6.1) > 0.97) * 0.3
            jy = math.sin(t * 1.3) * 0.12
            lx = max(-1, min(1, p["lookx"] + jx))
            ly = max(-1, min(1, p["looky"] + jy))
            px, py = lx * reach, ly * reach
            ctx.arc(px, py, pr, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK)
            ctx.fill()
            ctx.set_source_rgb(1, 1, 1)
            if p["sparkle"] > 0.05:                  # olhos brilhantes
                _star4(ctx, px - pr * 0.2, py - pr * 0.25, pr * (0.55 + 0.25 * math.sin(t * 9 + side)) * p["sparkle"],
                       rot=t * 1.5)
                ctx.fill()
                ctx.arc(px + pr * 0.45, py + pr * 0.4, pr * 0.16, 0, 2 * math.pi)
                ctx.fill()
            else:
                ctx.arc(px - pr * 0.3, py - pr * 0.3, max(pr * 0.3, 2), 0, 2 * math.pi)
                ctx.fill()
        ctx.restore()
        if p["sparkle"] > 0.05:                      # raios à volta do olho
            _stroke_style(ctx, 6, YELLOW)
            for k in range(3):
                a = math.radians(-130 + k * 40) if side < 0 else math.radians(-50 - k * 40)
                a += 0.12 * math.sin(t * 8 + k)
                ctx.move_to(ex + math.cos(a) * (r + 14), ey + math.sin(a) * (r + 14))
                ctx.line_to(ex + math.cos(a) * (r + 30), ey + math.sin(a) * (r + 30))
            ctx.stroke()


def _draw_brows(ctx, p):
    for side, y, a in ((-1, p["brl_y"], p["brl_a"]), (1, p["brr_y"], p["brr_a"])):
        cx, cy = side * 52, -46 + y
        ar = math.radians(a)
        half = 30
        ix, iy = cx - side * math.cos(ar) * half, cy - math.sin(ar) * half
        ox, oy = cx + side * math.cos(ar) * half, cy + math.sin(ar) * half
        _stroke_style(ctx, 11)
        ctx.move_to(ox, oy)
        ctx.curve_to(ox + (ix - ox) * 0.3, oy + (iy - oy) * 0.3 - 7, ox + (ix - ox) * 0.7, oy + (iy - oy) * 0.7 - 7, ix, iy)
        ctx.stroke()


def _draw_hat(ctx):
    ctx.save()
    ctx.translate(0, -100)
    ctx.rotate(math.radians(-8))
    # copa
    ctx.move_to(-98, 0)
    ctx.curve_to(-104, -78, -62, -92, 0, -92)
    ctx.curve_to(62, -92, 104, -78, 98, 0)
    ctx.close_path()
    # aba (atrás da copa, desenhada antes)
    ctx.save()
    ctx.new_path()
    ctx.save()
    ctx.scale(176, 30)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    _fill_stroke(ctx, KHAKI, 11)
    ctx.restore()
    ctx.move_to(-98, 0)
    ctx.curve_to(-104, -78, -62, -92, 0, -92)
    ctx.curve_to(62, -92, 104, -78, 98, 0)
    ctx.curve_to(60, 12, -60, 12, -98, 0)
    ctx.close_path()
    _fill_stroke(ctx, KHAKI, 11)
    # fita verde com debrum amarelo
    ctx.move_to(-100, -22)
    ctx.curve_to(-50, -8, 50, -8, 100, -22)
    ctx.line_to(97, -2)
    ctx.curve_to(50, 10, -50, 10, -97, -2)
    ctx.close_path()
    _fill_stroke(ctx, GREEN, 6)
    _stroke_style(ctx, 4, YELLOW)
    ctx.move_to(-98, -12)
    ctx.curve_to(-50, 1, 50, 1, 98, -12)
    ctx.stroke()
    ctx.restore()


def _draw_head(ctx, t, p, mo, mw, hat, env):
    ctx.save()
    ctx.translate(NECK[0], HEAD_CY)
    ctx.arc(0, 0, HEAD_R, 0, 2 * math.pi)
    _fill_stroke(ctx, (1, 0.995, 0.97), LINE)
    if p["cheeks"] > 0.02:
        ctx.set_source_rgba(*PINK, 0.45 * min(p["cheeks"], 1))
        for s in (-1, 1):
            ctx.arc(s * 88, 44, 17, 0, 2 * math.pi)
            ctx.fill()
    _draw_brows(ctx, p)
    _draw_eyes(ctx, t, p)
    _draw_mouth(ctx, mo, mw, p["smile"], t, p["open_gain"])
    if hat:
        _draw_hat(ctx)
    # extras: ponto de interrogação e gota de suor
    if p["qmark"] > 0.02:
        q = min(p["qmark"], 1)
        ctx.save()
        ctx.translate(205, -105 + math.sin(t * 3.2) * 12)
        ctx.rotate(math.radians(12 * math.sin(t * 2.4)))
        s = q * (1 + 0.08 * math.sin(t * 6))
        ctx.scale(s, s)
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(170)
        ext = ctx.text_extents("?")
        ctx.move_to(-ext.width / 2 - ext.x_bearing, ext.height / 2)
        ctx.text_path("?")
        ctx.set_source_rgb(*YELLOW)
        ctx.fill_preserve()
        _stroke_style(ctx, 9)
        ctx.stroke()
        ctx.restore()
    if p["sweat"] > 0.02:
        ph = (t * 0.9) % 1.0
        x, y = 96, -62 + ph * 95
        a = min(p["sweat"], 1) * (1 - max(0, ph - 0.75) * 4)
        ctx.save()
        ctx.translate(x, y)
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


def _draw_scarf(ctx, t, env):
    """O elemento principal: lenço triangular verde com debrum amarelo/branco."""
    nx, ny = NECK
    flutter = math.sin(t * 3.1) * 7 + env * math.sin(t * 11) * 4
    # triângulo
    ctx.new_path()
    ctx.move_to(nx - 92, ny + 6)
    ctx.curve_to(nx - 82, ny + 95, nx - 34 + flutter * 0.3, ny + 150, nx + flutter, ny + 178)
    ctx.curve_to(nx + 34 + flutter * 0.3, ny + 150, nx + 82, ny + 95, nx + 92, ny + 6)
    ctx.curve_to(nx + 45, ny + 34, nx - 45, ny + 34, nx - 92, ny + 6)
    ctx.close_path()
    ctx.set_source_rgb(*GREEN)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    _stroke_style(ctx, 46, WHITE)
    ctx.stroke_preserve()
    _stroke_style(ctx, 32, YELLOW)
    ctx.stroke_preserve()
    ctx.restore()
    _stroke_style(ctx, 11)
    ctx.stroke()
    # prega central subtil
    _stroke_style(ctx, 5, (0.07, 0.30, 0.17))
    ctx.move_to(nx + flutter * 0.4, ny + 56)
    ctx.line_to(nx + flutter * 0.9, ny + 135)
    ctx.stroke()
    # gola à volta do pescoço
    ctx.move_to(nx - 84, ny - 12)
    ctx.curve_to(nx - 40, ny + 48, nx + 40, ny + 48, nx + 84, ny - 12)
    _stroke_style(ctx, 52, INK)
    ctx.stroke_preserve()
    _stroke_style(ctx, 38, GREEN)
    ctx.stroke_preserve()
    _stroke_style(ctx, 6, YELLOW)
    ctx.stroke()
    # nó / argola
    ctx.arc(nx, ny + 52, 17, 0, 2 * math.pi)
    _fill_stroke(ctx, BROWN, 8)


def _draw_hand(ctx, hand, elbow, fingers):
    hx, hy = hand
    if fingers > 0.05:
        ang = math.atan2(hy - elbow[1], hx - elbow[0])
        _stroke_style(ctx, 9)
        for k in (-1, 0, 1):
            a = ang + k * 0.38
            ctx.move_to(hx + math.cos(a) * 18, hy + math.sin(a) * 18)
            ctx.line_to(hx + math.cos(a) * (18 + 40 * fingers), hy + math.sin(a) * (18 + 40 * fingers))
        ctx.stroke()
    ctx.arc(hx, hy, 21, 0, 2 * math.pi)
    _fill_stroke(ctx, (1, 0.995, 0.97), 10)


# ------------------------------------------------------------------ figura completa
def draw_tiko(ctx, t, p, mouth_o, mouth_w, env, hat=True):
    bob = math.sin(t * 2.2) * 3
    bx = math.sin(t * 1.3) * 4 + p["shake"] * math.sin(t * 63) * 5
    by = bob + p["shake"] * math.sin(t * 51) * 3
    jump = p["bounce"] * abs(math.sin(t * 6.3)) * 34
    by -= jump
    # sombra no chão
    ctx.save()
    ctx.translate(NECK[0] + bx, GROUND_Y + 14)
    ctx.scale(150 * (1 - jump / 170), 16 * (1 - jump / 170))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0, 0, 0, 0.12)
    ctx.fill()

    ctx.save()
    ctx.translate(bx, by)
    nx, ny = NECK
    # pernas e torso
    _stroke_style(ctx, LINE + 2)
    for fx in (-85, 90):
        ctx.move_to(*HIP)
        ctx.line_to(nx + fx, GROUND_Y)
        ctx.line_to(nx + fx + (38 if fx > 0 else -38), GROUND_Y)
    ctx.stroke()
    ctx.move_to(nx, ny)
    ctx.line_to(*HIP)
    ctx.stroke()

    # cabeça (inclinação à volta do pescoço + pequeno acento ao falar)
    ctx.save()
    ctx.translate(nx, ny)
    ctx.rotate(math.radians(p["tilt"] + math.sin(t * 2.7) * 1.5))
    ctx.translate(-nx, -ny + env * 2.0)
    _draw_head(ctx, t, p, mouth_o, mouth_w, hat, env)
    ctx.restore()

    # braços (IK) com gesticulação proporcional à fala
    drive = p["gest"] * (0.35 + env)
    arms = []
    for side, tx, ty, ph in ((-1, p["lhx"], p["lhy"], 0.0), (1, p["rhx"], p["rhy"], 1.7)):
        if side == 1 and p["fingers"] > 0.5:
            drive_s = drive * 0.4
        else:
            drive_s = drive
        tx += drive_s * 26 * math.sin(t * 5.1 + ph)
        ty += drive_s * 30 * math.sin(t * 4.3 + ph * 1.3)
        elbow, hand = _ik(SHOULDER, (SHOULDER[0] + tx, SHOULDER[1] + ty), side)
        arms.append((side, elbow, hand))
        _stroke_style(ctx, LINE)
        ctx.move_to(*SHOULDER)
        ctx.line_to(*elbow)
        ctx.line_to(*hand)
        ctx.stroke()

    _draw_scarf(ctx, t, env)
    for side, elbow, hand in arms:
        _draw_hand(ctx, hand, elbow, p["fingers"] if side == 1 else 0)
    ctx.restore()

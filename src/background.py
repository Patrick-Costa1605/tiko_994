"""Fundo vivo: papel quadriculado com grão e vinheta + camadas em parallax
(nuvens, folhas, bússolas e ondas do mar das Caxinas)."""
import math

import cairo
import numpy as np

from config import *

NUVENS = [(260, 1.0, 9, 0.80, 0.0), (470, 0.7, 14, 0.65, 380.0), (700, 1.25, 6, 0.55, 760.0),
          (1180, 0.8, 11, 0.45, 120.0), (880, 0.6, 17, 0.45, 640.0)]
FOLHAS = [(((i * 211) % 1100), ((i * 389) % 1900), 22 + (i % 3) * 10, 28 + (i * 7) % 30, i) for i in range(9)]


def make_texture():
    """Papel #F9F6F0 com grelha subtil, grão e vinheta suave (gerado uma vez)."""
    rng = np.random.default_rng(994)
    base = np.array([PAPER[2], PAPER[1], PAPER[0]], dtype=np.float32) * 255
    img = np.empty((H, W, 3), dtype=np.float32)
    img[:] = base
    grid = np.array([0xD8, 0xD0, 0xC2], dtype=np.float32)
    for x in range(30, W, 60):
        img[:, x:x + 2] = img[:, x:x + 2] * 0.55 + grid * 0.45
    for y in range(30, H, 60):
        img[y:y + 2, :] = img[y:y + 2, :] * 0.55 + grid * 0.45
    img += rng.normal(0, 2.0, (H, W, 1)).astype(np.float32)
    coarse = rng.normal(0, 1.8, (H // 6, W // 6, 1)).astype(np.float32)
    img += np.kron(coarse, np.ones((6, 6, 1), dtype=np.float32))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    img *= (1 - 0.16 * np.clip(d - 0.35, 0, 1) ** 1.2)[..., None]
    out = np.empty((H, W, 4), dtype=np.uint8)
    out[..., :3] = np.clip(img, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return cairo.ImageSurface.create_for_data(out, cairo.FORMAT_ARGB32, W, H, W * 4), out


def _cloud(ctx, x, y, s, alpha):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    circles = ((-60, 8, 38), (-18, -14, 52), (36, -4, 44), (78, 14, 32), (10, 18, 46))
    for grow, col, a in ((5, SKY, alpha * 0.55), (0, WHITE, alpha)):      # contorno por baixo, miolo por cima
        ctx.new_path()
        for cx, cy, r in circles:
            ctx.new_sub_path()
            ctx.arc(cx, cy, r + grow, 0, 2 * math.pi)
        ctx.set_source_rgba(*col, a)
        ctx.fill()
    ctx.restore()


def _leaf(ctx, x, y, size, rot, alpha):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.move_to(0, -size)
    ctx.curve_to(size * 0.8, -size * 0.5, size * 0.8, size * 0.5, 0, size)
    ctx.curve_to(-size * 0.8, size * 0.5, -size * 0.8, -size * 0.5, 0, -size)
    ctx.set_source_rgba(*LOGO_GREEN, alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(*SCARF_DARK, alpha * 0.8)
    ctx.set_line_width(3)
    ctx.move_to(0, -size)
    ctx.line_to(0, size)
    ctx.stroke()
    ctx.restore()


def _compass(ctx, x, y, r, rot, alpha):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.set_source_rgba(*LOGO_GREEN, alpha)
    ctx.set_line_width(4)
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.stroke()
    ctx.arc(0, 0, r * 0.82, 0, 2 * math.pi)
    ctx.stroke()
    for k in range(8):
        a = k * math.pi / 4
        rr = r * (0.78 if k % 2 == 0 else 0.45)
        ctx.move_to(math.cos(a + 0.2) * r * 0.12, math.sin(a + 0.2) * r * 0.12)
        ctx.line_to(math.cos(a) * rr, math.sin(a) * rr)
        ctx.line_to(math.cos(a - 0.2) * r * 0.12, math.sin(a - 0.2) * r * 0.12)
        ctx.close_path()
    ctx.set_source_rgba(*LOGO_YELLOW, alpha * 1.4)
    ctx.fill()
    ctx.restore()


def _wave(ctx, y0, amp, wl, speed, t, color, alpha):
    ctx.new_path()
    ctx.move_to(-20, H + 20)
    for x in range(-20, W + 41, 40):
        ctx.line_to(x, y0 + amp * math.sin((x / wl) * 2 * math.pi + t * speed))
    ctx.line_to(W + 20, H + 20)
    ctx.close_path()
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()


def draw_parallax(ctx, t):
    # camada longínqua: nuvens (lentas)
    for y, s, v, a, x0 in NUVENS:
        x = (x0 + v * t * 6) % (W + 500) - 250
        _cloud(ctx, x, y + 10 * math.sin(t * 0.4 + x0), 1.1 * s * 1.6, a)
    # bússolas muito suaves, a rodar devagar
    _compass(ctx, 170, 420, 120, t * 0.12, 0.10)
    _compass(ctx, 930, 1300, 150, -t * 0.09 + 1, 0.09)
    # camada média: folhas a cair
    for x0, y0, vs, size, i in FOLHAS:
        y = (y0 + vs * t * 3.2) % (H + 120) - 60
        x = x0 + 50 * math.sin(t * 0.7 + i) - 0.18 * (y - y0)
        x = x % (W + 160) - 80
        _leaf(ctx, x, y, size, t * 0.8 + i, 0.32)
    # camada próxima: ondas do mar
    _wave(ctx, 1815, 14, 300, 1.3, t, SKY, 0.45)
    _wave(ctx, 1845, 12, 220, -1.7, t, mix(SKY, LOGO_GREEN, 0.25), 0.55)
    _wave(ctx, 1880, 10, 340, 2.1, t, mix(SKY, LOGO_BLUE, 0.3), 0.65)

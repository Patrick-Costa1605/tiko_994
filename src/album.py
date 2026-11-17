"""Álbum vivo: o Tiko vive dentro de um álbum de recortes.

Cada bloco do guião pode ter uma «página» (foto com fita-cola, autocolante de título e rabiscos).
- Os recortes mexem-se em *stop-motion* (12 fps) enquanto o Tiko se mexe a 60 fps.
- Os rabiscos desenham-se à mão, ao ritmo da fala.
- As páginas viram com perspetiva (como num caderno).
"""
import math
import zlib

import cairo
import numpy as np
from PIL import Image

from config import *

PHOTOS_DIR = ROOT / "assets" / "fotos"
CHEWY = "Chewy"
STOP = 12.0                                   # fps do «stop-motion»
FLIP_PRE, FLIP_DUR = 0.10, 0.62               # a página começa a virar 0.10 s antes do bloco
PAPEL = (1.0, 0.985, 0.94)


def h01(*a):
    return (zlib.crc32(repr(a).encode()) & 0xFFFFFFFF) / 2 ** 32


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x, c=1.7):
    x = clamp(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def _ink(ctx, w, a=1.0, color=INK):
    ctx.set_source_rgba(*color, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)


def _poly(ctx, pts, frac=1.0):
    """Desenha uma polilinha até à fração `frac` do seu comprimento (efeito «desenhado à mão»)."""
    if frac <= 0 or len(pts) < 2:
        return
    ln = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    goal, acc = sum(ln) * min(frac, 1.0), 0.0
    ctx.move_to(*pts[0])
    for i, l in enumerate(ln):
        if acc + l >= goal:
            k = (goal - acc) / max(l, 1e-6)
            ctx.line_to(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k)
            return
        ctx.line_to(*pts[i + 1])
        acc += l


def _wob(pts, seed, q, amp):
    return [(x + (h01(seed, i, q, "x") - .5) * amp, y + (h01(seed, i, q, "y") - .5) * amp) for i, (x, y) in enumerate(pts)]


def _bez(p0, p1, p2, p3, n=26):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def _text(ctx, txt, size, family=CHEWY):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return ctx.text_extents(txt)


# ------------------------------------------------------------------ rabiscos (desenhados à mão)
def d_linhas(ctx, a, q, box):
    """Linhas de velocidade à esquerda da foto."""
    x, y, w, h = box
    for i in range(5):
        yy = y + h * (0.18 + 0.16 * i)
        L = 150 + 60 * h01("l", i)
        sh = math.sin(q * 6 + i) * 14
        x1 = x - 30 - sh
        f = ease((a - 0.45 - 0.07 * i) / 0.25)
        _ink(ctx, 11)
        _poly(ctx, _wob([(x1, yy), (x1 - L / 2, yy + 3), (x1 - L, yy)], i, int(q * 12), 5), f)
        ctx.stroke()


def d_lama(ctx, a, q, box):
    """Salpicos de lama a surgir à volta da foto."""
    x, y, w, h = box
    spots = [(x + w * 0.08, y + h + 10, 46), (x + w * 0.35, y + h + 34, 30), (x + w * 0.78, y + h + 6, 54),
             (x + w + 6, y + h * 0.78, 38), (x + w * 0.9, y + h + 46, 26), (x - 10, y + h * 0.9, 34)]
    for i, (cx, cy, r) in enumerate(spots):
        s = back((a - 0.5 - 0.12 * i) / 0.35)
        if s <= 0:
            continue
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(s, s)
        n = 14
        pts = [(math.cos(2 * math.pi * k / n) * r * (1 + 0.28 * (h01("m", i, k, int(q * 6)) - .5)),
                math.sin(2 * math.pi * k / n) * r * 0.82 * (1 + 0.28 * (h01("m", i, k, int(q * 6), 1) - .5))) for k in range(n)]
        ctx.move_to(*pts[0])
        for k in range(n):
            p, nx = pts[k], pts[(k + 1) % n]
            ctx.curve_to(p[0] * 1.0, p[1] * 1.0, nx[0], nx[1], (p[0] + nx[0]) / 2, (p[1] + nx[1]) / 2)
        ctx.close_path()
        ctx.set_source_rgb(0.48, 0.30, 0.17)
        ctx.fill_preserve()
        _ink(ctx, 6)
        ctx.stroke()
        ctx.arc(-r * 0.3, -r * 0.3, r * 0.14, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, .35)
        ctx.fill()
        ctx.restore()


def d_interrogacoes(ctx, a, q, box):
    x, y, w, h = box
    for i, (px, py, sz, rot) in enumerate(((x - 40, y + 30, 150, -14), (x + w - 20, y - 10, 190, 12), (x + w * 0.45, y - 60, 120, -4))):
        s = back((a - 0.5 - 0.17 * i) / 0.35)
        if s <= 0:
            continue
        bob = math.sin(q * 5 + i * 2) * 8
        ctx.save()
        ctx.translate(px, py + bob)
        ctx.rotate(math.radians(rot + math.sin(q * 4 + i) * 4))
        ctx.scale(s, s)
        e = _text(ctx, "?", sz)
        ctx.move_to(-e.width / 2 - e.x_bearing, e.height / 2)
        ctx.text_path("?")
        ctx.set_source_rgb(*LOGO_YELLOW)
        ctx.fill_preserve()
        _ink(ctx, 9)
        ctx.stroke()
        ctx.restore()


def d_uivo(ctx, a, q, box):
    """«AUUUU!» com arcos de som, a sair da foto."""
    x, y, w, h = box
    s = back((a - 0.45) / 0.4)
    if s > 0:
        ctx.save()
        ctx.translate(x + w * 0.40, y + h + 78)
        ctx.rotate(math.radians(-5 + math.sin(q * 7) * 2.5))
        ctx.scale(s, s)
        e = _text(ctx, "AUUUU!", 120)
        ctx.move_to(-e.width / 2 - e.x_bearing, e.height / 2)
        ctx.text_path("AUUUU!")
        ctx.set_source_rgb(*LOGO_YELLOW)
        ctx.fill_preserve()
        _ink(ctx, 13)
        ctx.stroke()
        ctx.restore()
    for i in range(3):
        f = ease((a - 0.7 - 0.12 * i) / 0.3)
        if f <= 0:
            continue
        r = 70 + 42 * i + math.sin(q * 6 + i) * 4
        cx, cy = x + w + 12, y + 60
        pts = [(cx + math.cos(math.radians(-62 + 124 * k / 20)) * r, cy + math.sin(math.radians(-62 + 124 * k / 20)) * r) for k in range(21)]
        _ink(ctx, 10)
        _poly(ctx, _wob(pts, i, int(q * 12), 4), f)
        ctx.stroke()


def d_coracoes(ctx, a, q, box):
    x, y, w, h = box
    for i in range(5):
        age = a - (0.5 + 0.22 * i)
        if age < 0:
            continue
        life = (age % 1.6) / 1.6
        px = x + w * (0.15 + 0.17 * i) + math.sin(life * 6 + i) * 18
        py = y + h * 0.55 - life * 300
        sc = (0.6 + 0.5 * h01("h", i)) * min(age / 0.2, 1) * (1 - ease((life - 0.7) / 0.3))
        if sc <= 0.02:
            continue
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(math.radians(-12 + 24 * h01("hr", i)))
        ctx.scale(sc * 46, sc * 46)
        ctx.move_to(0, 0.9)
        ctx.curve_to(-1.5, -0.1, -0.9, -1.1, 0, -0.45)
        ctx.curve_to(0.9, -1.1, 1.5, -0.1, 0, 0.9)
        ctx.close_path()
        ctx.set_source_rgb(*LOGO_RED)
        ctx.fill_preserve()
        _ink(ctx, 6 / (sc * 46))
        ctx.stroke()
        ctx.restore()


def d_estrelas(ctx, a, q, box):
    x, y, w, h = box
    for i, (px, py, r) in enumerate(((x - 18, y - 10, 38), (x + w + 10, y + 40, 30),                                      (x + w + 22, y + h * 0.7, 40), (x - 24, y + h * 0.75, 28))):
        s = back((a - 0.4 - 0.1 * i) / 0.35) * (0.8 + 0.25 * math.sin(q * 6 + i * 1.7))
        if s <= 0:
            continue
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(q * 0.8 + i)
        ctx.scale(s, s)
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((math.cos(ang) * rr, math.sin(ang) * rr))
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.set_source_rgb(*LOGO_YELLOW)
        ctx.fill_preserve()
        _ink(ctx, 6)
        ctx.stroke()
        ctx.restore()


DOODLES = {"linhas": d_linhas, "lama": d_lama, "interrogacoes": d_interrogacoes, "uivo": d_uivo,
           "coracoes": d_coracoes, "estrelas": d_estrelas}


# ------------------------------------------------------------------ álbum
class Album:
    def __init__(self, tl, tex):
        self.tl, self.tex = tl, tex
        self.blocks = tl["blocks"]
        self.starts = [b["vstart"] for b in self.blocks]
        self._img = {}
        self.tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.tctx = cairo.Context(self.tmp)

    # ---- fotos
    def foto(self, nome, w, h, pos):
        key = (nome, w, h, pos)
        if key not in self._img:
            im = Image.open(PHOTOS_DIR / nome).convert("RGB")
            tw, th = int(w * 1.16), int(h * 1.16)
            k = max(tw / im.width, th / im.height)
            im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
            px, py = (float(v.strip("%")) / 100 for v in pos.split())
            x0, y0 = int((im.width - tw) * px), int((im.height - th) * py)
            im = im.crop((x0, y0, x0 + tw, y0 + th))
            a = np.dstack([np.array(im)[..., ::-1], np.full((th, tw), 255, np.uint8)]).copy()
            self._img[key] = (cairo.ImageSurface.create_for_data(a, cairo.FORMAT_ARGB32, tw, th, tw * 4), a, tw, th)
        return self._img[key]

    def _layout(self, blk):
        """Posição e tamanho da foto: do lado oposto ao Tiko (o Tiko fica à frente, a tapar um cantinho)."""
        pg = blk["pagina"]
        side = 0 if blk["tiko_dx"] == 0 else (1 if blk["tiko_dx"] < 0 else -1)
        horizontal = pg.get("formato", "h") == "h"
        w, h = (640, 430) if horizontal else (470, 600)
        if side == 0:
            w, h = (800, 400) if horizontal else (520, 640)
        cx = 540 + side * 215
        cy = 450 + (h + 110) / 2 + (0 if side else 10)
        return cx, cy, w, h

    # ---- uma página (papel + recortes)
    def draw_page(self, ctx, blk, t):
        ctx.set_source_surface(self.tex, 0, 0)
        ctx.paint()
        pg = blk.get("pagina")
        if not pg:
            return
        a = t - (blk["vstart"] - 0.05)
        q = math.floor(t * STOP) / STOP
        fq = int(t * STOP)
        cx, cy, w, h = self._layout(blk)
        seed = blk["start"]

        # foto em polaroid
        s = back((a - 0.12) / 0.5)
        if s > 0:
            rot = pg.get("rot", -3 if cx >= 540 else 3)
            surf, _arr, tw, th = self.foto(pg["foto"], w, h, pg.get("foto_pos", "50% 50%"))
            kb = 1.0 + 0.08 * clamp((t - blk["vstart"]) / max(blk["vend"] - blk["vstart"], 0.5))
            bx, by = cx + math.sin(q * 1.1 + seed) * 6 + (h01(seed, fq, "x") - .5) * 3, cy + math.sin(q * 0.9 + seed) * 5 + (h01(seed, fq, "y") - .5) * 3
            ctx.save()
            ctx.translate(bx, by + (1 - min(s, 1)) * -160)
            ctx.rotate(math.radians(rot + (h01(seed, fq, "r") - .5) * 1.2 + math.sin(q * 0.8 + seed) * 0.8))
            ctx.scale(s, s)
            fw, fh = w + 44, h + 22 + 88
            fy = -fh / 2
            ctx.rectangle(-fw / 2 + 12, fy + 16, fw, fh)                       # sombra
            ctx.set_source_rgba(0, 0, 0, 0.28)
            ctx.fill()
            ctx.rectangle(-fw / 2, fy, fw, fh)
            ctx.set_source_rgb(*PAPEL)
            ctx.fill_preserve()
            _ink(ctx, 6)
            ctx.stroke()
            ctx.save()
            ctx.rectangle(-w / 2, fy + 22, w, h)
            ctx.clip()
            ctx.translate(0, fy + 22 + h / 2)
            k = kb / 1.16
            ctx.scale(k, k)
            ctx.set_source_surface(surf, -tw / 2, -th / 2)
            ctx.paint()
            ctx.restore()
            ctx.rectangle(-w / 2, fy + 22, w, h)
            _ink(ctx, 5, .8)
            ctx.stroke()
            if pg.get("legenda"):
                ctx.save()
                e = _text(ctx, pg["legenda"], 46)
                ctx.move_to(-e.width / 2 - e.x_bearing, fy + 22 + h + 62)
                ctx.rotate(math.radians(-1))
                ctx.set_source_rgba(*INK, .85)
                ctx.show_text(pg["legenda"])
                ctx.restore()
            for tx, ty, tr in ((-fw * 0.28, fy, -5), (fw * 0.3, fy + 4, 7)) if pg.get("fita2") else ((0, fy, -3),):
                ctx.save()
                ctx.translate(tx, ty)
                ctx.rotate(math.radians(tr))
                ctx.rectangle(-95, -24, 190, 50)
                ctx.set_source_rgba(1, 0.93, 0.62, .82)
                ctx.fill()
                ctx.restore()
            ctx.restore()

        # autocolante de título
        titulo = pg.get("titulo")
        if titulo:
            ts = back((a - 0.02) / 0.42)
            if ts > 0:
                num, txt = (titulo if isinstance(titulo, list) else (None, titulo))
                e = _text(ctx, txt, 92)
                bw = e.width + 70 + (110 if num else 0)
                k = min(1.0, 960 / bw)
                ctx.save()
                ctx.translate(540 + (h01(seed, fq, "tx") - .5) * 3, 342 + (h01(seed, fq, "ty") - .5) * 3 + (1 - min(ts, 1)) * -90)
                ctx.rotate(math.radians(-2.2 + (h01(seed, fq, "tr") - .5) * 0.8))
                ctx.scale(ts * k, ts * k)
                bh = 130
                ctx.rectangle(-bw / 2 + 10, -bh / 2 + 12, bw, bh)
                ctx.set_source_rgba(*INK, .9)
                ctx.fill()
                ctx.rectangle(-bw / 2, -bh / 2, bw, bh)
                ctx.set_source_rgb(*LOGO_YELLOW)
                ctx.fill_preserve()
                _ink(ctx, 9)
                ctx.stroke()
                tx0 = -bw / 2 + 35
                if num:
                    ctx.arc(-bw / 2 + 60, 0, 52, 0, 2 * math.pi)
                    ctx.set_source_rgb(*LOGO_GREEN)
                    ctx.fill_preserve()
                    _ink(ctx, 8)
                    ctx.stroke()
                    en = _text(ctx, num, 80)
                    ctx.move_to(-bw / 2 + 60 - en.width / 2 - en.x_bearing, en.height / 2)
                    ctx.set_source_rgb(*PAPER)
                    ctx.show_text(num)
                    tx0 = -bw / 2 + 130
                e = _text(ctx, txt, 92)
                ctx.move_to(tx0 - e.x_bearing, e.height / 2)
                ctx.set_source_rgb(*INK)
                ctx.show_text(txt)
                ctx.restore()

        # rabiscos
        box = (cx - w / 2 - 22, cy - (h + 110) / 2 + 0, w + 44, h + 110)
        for name in pg.get("rabiscos", []):
            DOODLES[name](ctx, a, q, box)

    # ---- virar de página
    def _flip(self, ctx, A, B, t, p):
        self.draw_page(ctx, B, t)
        tc = self.tctx
        tc.save()
        tc.set_operator(cairo.OPERATOR_CLEAR)
        tc.paint()
        tc.restore()
        self.draw_page(tc, A, t)
        th = ease(p) * math.pi * 0.5
        c, s_ = math.cos(th), math.sin(th)
        D, cy, N = 1500.0, H * 0.5, 40
        # sombra projetada na página de baixo
        edge = W * c * (D / (D - W * s_))
        g = cairo.LinearGradient(edge, 0, edge + 220, 0)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.34 * s_)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.rectangle(edge, 0, 220, H)
        ctx.set_source(g)
        ctx.fill()
        for i in range(N):
            x0, x1 = i * W / N, (i + 1) * W / N
            px0 = x0 * c * (D / (D - x0 * s_))
            px1 = x1 * c * (D / (D - x1 * s_))
            sm = D / (D - (x0 + x1) / 2 * s_)
            sx = max((px1 - px0) / (x1 - x0), 1e-4)
            ctx.save()
            ctx.translate(px0, cy)
            ctx.scale(sx, sm)
            ctx.translate(-x0, -cy)
            ctx.rectangle(x0, 0, x1 - x0 + 0.6, H)
            ctx.clip()
            ctx.set_source_surface(self.tmp, 0, 0)
            ctx.paint()
            ctx.restore()
            shade = 0.30 * s_ * (0.4 + 0.6 * i / N)       # escurece à medida que levanta
            ctx.rectangle(px0, 0, px1 - px0 + 0.8, H)
            ctx.set_source_rgba(0.1, 0.07, 0.04, shade)
            ctx.fill()
        # brilho no rebordo
        ctx.rectangle(edge - 3, 0, 3, H)
        ctx.set_source_rgba(1, 1, 1, 0.5 * s_)
        ctx.fill()

    def draw(self, ctx, t):
        blocks = self.blocks
        j = max(0, sum(1 for s in self.starts if t + FLIP_PRE >= s) - 1)
        if j > 0:
            p = (t - (blocks[j]["vstart"] - FLIP_PRE)) / FLIP_DUR
            if p < 1.0:
                self._flip(ctx, blocks[j - 1], blocks[j], t, max(p, 0.0))
                return
        self.draw_page(ctx, blocks[j], t)

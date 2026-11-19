"""Primitivas de desenho «à mão»: traços com tremor, preenchimento tipo marcador, texto que se escreve e a mão que desenha."""
import math
import zlib

import cairo
import numpy as np

from config import *


def h01(*a):
    return (zlib.crc32(repr(a).encode()) & 0xFFFFFFFF) / 2 ** 32


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ geometria
def _dense(pts, step=5.0):
    """Reamostra uma polilinha para pontos a ~step px (para o tremor e o traço parcial)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        n = max(1, int(d / step))
        for i in range(1, n + 1):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def catmull(pts, closed=False, n=10):
    P = list(pts)
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                     + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(P[-2] if not closed else out[0])
    return out


def bez(p0, p1, p2, p3, n=18):
    return [tuple((1 - t) ** 3 * p0[j] + 3 * (1 - t) ** 2 * t * p1[j] + 3 * (1 - t) * t * t * p2[j] + t ** 3 * p3[j] for j in (0, 1))
            for t in (i / n for i in range(n + 1))]


def circulo(cx, cy, r, seed=0, wob=0.04, a0=0.0, a1=2 * math.pi, rot=None):
    n = max(12, int(abs(a1 - a0) * r / 6))
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r * (1 + (h01(seed, i) - .5) * wob),
             cy + math.sin(a0 + (a1 - a0) * i / n) * r * (1 + (h01(seed, i, 1) - .5) * wob)) for i in range(n + 1)]


def elipse(cx, cy, rx, ry, seed=0, a0=0.0, a1=2 * math.pi):
    n = max(12, int(abs(a1 - a0) * max(rx, ry) / 6))
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx, cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]


def rrect(x, y, w, h, r=0, seed=0):
    if r <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    pts = []
    for (cx, cy, a) in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(7):
            ang = math.radians(a + 90 * k / 6)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    pts.append(pts[0])
    return pts


def onda(x0, x1, y, amp, wl, fase=0.0):
    n = int((x1 - x0) / 8)
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin((x0 + (x1 - x0) * i / n) / wl * 2 * math.pi + fase)) for i in range(n + 1)]


# ------------------------------------------------------------------ elementos
def caminho(pts, c=INK, w=9, fill=None, fa=0.6, fechado=False, peso=1.0, seed=0, ancora=None, tremor=1.4):
    """Um traço. `fill` pinta o interior (como marcador, ligeiramente desalinhado) depois de o contorno estar feito."""
    d = np.array(_dense(pts, 5.0), dtype=np.float32)
    seg = np.hypot(*(d[1:] - d[:-1]).T)
    cum = np.concatenate([[0.0], np.cumsum(seg)]).astype(np.float32)
    return {"k": "path", "pts": d, "cum": cum, "len": float(cum[-1]), "c": c, "w": w, "fill": fill, "fa": fa, "fechado": fechado,
            "peso": peso, "seed": seed, "ancora": ancora, "tremor": tremor}


def texto(txt, x, y, size=80, c=INK, align="c", rot=0.0, peso=1.0, ancora=None, sublinhado=False):
    return {"k": "texto", "txt": txt, "x": x, "y": y, "size": size, "c": c, "align": align, "rot": rot, "peso": peso,
            "ancora": ancora, "sub": sublinhado}


def imagem(ficheiro, x, y, h, peso=1.0, ancora=None, rot=0.0):
    return {"k": "img", "f": ficheiro, "x": x, "y": y, "h": h, "peso": peso, "ancora": ancora, "rot": rot}


def pessoa(x, y, s=1.0, lenco=VERDE, chapeu=False, braco="baixo", seed=0, c=INK, w=8):
    """Boneco de pauzinhos com lenço escutista. (x, y) = pés. Devolve elementos já pela ordem de desenho."""
    S = lambda v: v * s
    cab = (x, y - S(230))
    E = []
    E.append(caminho(circulo(cab[0], cab[1], S(34), seed), c, w, fill=PELE, fa=0.9, fechado=True, seed=seed))
    E.append(caminho([(x, y - S(196)), (x, y - S(95))], c, w, seed=seed + 1))                                 # tronco
    E.append(caminho([(x, y - S(95)), (x - S(30), y)], c, w, seed=seed + 2))                                    # pernas
    E.append(caminho([(x, y - S(95)), (x + S(30), y)], c, w, seed=seed + 3))
    bx = {"baixo": ((x - S(48), y - S(125)), (x + S(48), y - S(125))),
          "cima": ((x - S(50), y - S(260)), (x + S(50), y - S(260))),
          "dir": ((x - S(48), y - S(125)), (x + S(58), y - S(218)))}[braco]
    E.append(caminho([(x, y - S(178)), bx[0]], c, w, seed=seed + 4))
    E.append(caminho([(x, y - S(178)), bx[1]], c, w, seed=seed + 5))
    E.append(caminho([(x - S(24), y - S(192)), (x + S(24), y - S(192)), (x, y - S(140)), (x - S(24), y - S(192))], c, max(w - 2, 5), fill=lenco, fa=0.95, fechado=True, seed=seed + 6))
    if chapeu:
        E.append(caminho(elipse(cab[0], cab[1] - S(26), S(52), S(11)), c, w - 1, fill=CASTANHO, fa=0.9, fechado=True, seed=seed + 7))
        E.append(caminho([(cab[0] - S(26), cab[1] - S(30)), (cab[0] - S(22), cab[1] - S(62)), (cab[0] + S(22), cab[1] - S(62)), (cab[0] + S(26), cab[1] - S(30))], c, w - 1, fill=CASTANHO, fa=0.9, seed=seed + 8))
    E.append(caminho(elipse(cab[0] - S(12), cab[1] - S(4), S(3), S(3)), c, 6, fill=c, fa=1, fechado=True, seed=seed + 9))   # olhos
    E.append(caminho(elipse(cab[0] + S(12), cab[1] - S(4), S(3), S(3)), c, 6, fill=c, fa=1, fechado=True, seed=seed + 10))
    E.append(caminho(elipse(cab[0], cab[1] + S(8), S(12), S(8), a0=0.15, a1=math.pi - 0.15), c, 5, seed=seed + 11))        # sorriso
    return E


def flordelis(cx, cy, s=1.0, c=INK, fill=VERDE, seed=0, w=8):
    """Flor-de-lis do escutismo: pétala central, duas pétalas laterais enroladas, faixa e as duas pontas."""
    S = lambda p: (cx + p[0] * s, cy + p[1] * s)
    centro = bez((0, -105), (38, -70), (40, -30), (0, 20)) + bez((0, 20), (-40, -30), (-38, -70), (0, -105))
    # pétala lateral esquerda: sobe e enrola para fora
    esq = (bez((-6, 14), (-30, 22), (-84, 18), (-92, -26)) + bez((-92, -26), (-96, -60), (-62, -74), (-46, -52))
           + bez((-46, -52), (-36, -38), (-52, -22), (-62, -30)) + bez((-62, -30), (-44, -22), (-26, -20), (-6, -8)))
    dire = [(-x, y) for x, y in esq]
    faixa = [(-52, 18), (52, 18), (52, 40), (-52, 40), (-52, 18)]
    pontas = [(-22, 40), (-34, 92), (-6, 70), (0, 100), (6, 70), (34, 92), (22, 40)]
    return [caminho([S(q) for q in centro], c, w, fill=fill, fechado=True, seed=seed, tremor=1.0),
            caminho([S(q) for q in esq], c, w, fill=fill, fechado=True, seed=seed + 1, tremor=1.0),
            caminho([S(q) for q in dire], c, w, fill=fill, fechado=True, seed=seed + 2, tremor=1.0),
            caminho([S(q) for q in faixa], c, w - 1, fill=fill, fechado=True, seed=seed + 3, tremor=1.0),
            caminho([S(q) for q in pontas], c, w - 1, fill=fill, fechado=True, seed=seed + 4, tremor=1.0)]


def lenco_icone(cx, cy, s, cor, seed=0):
    """Lenço escutista (triângulo) com debrum branco."""
    tri = [(cx - 70 * s, cy - 55 * s), (cx + 70 * s, cy - 55 * s), (cx, cy + 62 * s), (cx - 70 * s, cy - 55 * s)]
    return [caminho(tri, INK, 8, fill=cor, fa=0.95, fechado=True, seed=seed),
            caminho([(cx - 52 * s, cy - 40 * s), (cx, cy + 40 * s), (cx + 52 * s, cy - 40 * s)], (1, 1, 1), 5, seed=seed + 1, tremor=0.5)]


# ------------------------------------------------------------------ desenhar
_cache = {}


def _jit(el, step):
    key = (id(el), step)
    j = _cache.get(key)
    if j is None:
        r = np.random.default_rng(el["seed"] * 7919 + step * 104729 + len(el["pts"]))
        j = (r.normal(0, el["tremor"], el["pts"].shape)).astype(np.float32)
        if len(_cache) > 4000:
            _cache.clear()
        _cache[key] = j
    return j


def ponto_em(el, p):
    """Ponto (x, y) do traço à fração p do seu comprimento."""
    L = el["cum"][-1] * p
    i = int(np.searchsorted(el["cum"], L))
    i = min(max(i, 1), len(el["pts"]) - 1)
    a, b = el["pts"][i - 1], el["pts"][i]
    seg = max(el["cum"][i] - el["cum"][i - 1], 1e-6)
    t = (L - el["cum"][i - 1]) / seg
    return (float(a[0] + (b[0] - a[0]) * t), float(a[1] + (b[1] - a[1]) * t))


def _fonte(ctx, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def largura_texto(ctx, txt, size):
    _fonte(ctx, size)
    return ctx.text_extents(txt).x_advance


def desenha_elemento(ctx, el, p, step, fa_fill, imgs):
    """Desenha o elemento até à fração p (0..1). Devolve a posição da ponta do marcador (para a mão)."""
    if p <= 0:
        return None
    if el["k"] == "path":
        pts = el["pts"] + _jit(el, step)
        L = el["cum"][-1] * min(p, 1.0)
        n = int(np.searchsorted(el["cum"], L)) + 1
        n = min(max(n, 2), len(pts))
        part = pts[:n].copy()
        if p < 1.0 and n >= 2:
            a, b = el["pts"][n - 2], el["pts"][n - 1]
            seg = max(el["cum"][n - 1] - el["cum"][n - 2], 1e-6)
            t = clamp((L - el["cum"][n - 2]) / seg)
            part[-1] = (a + (b - a) * t) + _jit(el, step)[n - 1]
        if el["fill"] is not None and fa_fill > 0 and el["fechado"]:
            ctx.save()
            ctx.translate(5, 4)                                  # desalinhado, como marcador sobre papel
            ctx.move_to(*pts[0])
            for q in pts[1:]:
                ctx.line_to(*q)
            ctx.close_path()
            ctx.set_source_rgba(*el["fill"], el["fa"] * fa_fill)
            ctx.fill()
            ctx.restore()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        for dx, dy, al, wk in ((0, 0, 1.0, 1.0), (1.3, -1.0, 0.45, 0.8)):              # duas passagens: tinta mais viva no centro
            ctx.set_source_rgba(*el["c"], al)
            ctx.set_line_width(el["w"] * wk)
            ctx.move_to(part[0][0] + dx, part[0][1] + dy)
            for q in part[1:]:
                ctx.line_to(q[0] + dx, q[1] + dy)
            ctx.stroke()
        return (float(part[-1][0]), float(part[-1][1]))
    if el["k"] == "texto":
        _fonte(ctx, el["size"])
        e = ctx.text_extents(el["txt"])
        wtxt = e.x_advance
        x0 = el["x"] - {"c": wtxt / 2, "l": 0, "r": wtxt}[el["align"]]
        ctx.save()
        ctx.translate(el["x"], el["y"])
        ctx.rotate(math.radians(el["rot"]))
        ctx.translate(-el["x"], -el["y"])
        ctx.rectangle(x0 - 20, el["y"] - el["size"] * 1.2, (wtxt + 40) * min(p, 1.0), el["size"] * 1.8)
        ctx.clip()
        j = (h01(id(el), step) - .5) * 2.0
        ctx.move_to(x0 + j, el["y"] + (h01(id(el), step, 1) - .5) * 2.0)
        ctx.text_path(el["txt"])
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*el["c"], 1)
        ctx.fill_preserve()
        ctx.set_line_width(2.2)
        ctx.stroke()
        if el["sub"]:
            ctx.set_line_width(7)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(x0, el["y"] + el["size"] * 0.18)
            ctx.curve_to(x0 + wtxt * 0.3, el["y"] + el["size"] * 0.28, x0 + wtxt * 0.7, el["y"] + el["size"] * 0.10, x0 + wtxt, el["y"] + el["size"] * 0.2)
            ctx.stroke()
        ctx.restore()
        tx = x0 + wtxt * min(p, 1.0)
        return (tx, el["y"] - el["size"] * 0.25)
    if el["k"] == "img":
        im = imgs[el["f"]]
        k = el["h"] / im.get_height()
        ctx.save()
        ctx.translate(el["x"], el["y"])
        ctx.rotate(math.radians(el["rot"]))
        ctx.scale(k, k)
        ctx.set_source_surface(im, -im.get_width() / 2, -im.get_height() / 2)
        ctx.paint_with_alpha(ease(p))
        ctx.restore()
        return None
    return None


# ------------------------------------------------------------------ a mão com o marcador
def desenha_mao(ctx, x, y, t):
    """Mão que segura um marcador; a ponta do marcador fica em (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(0.82, 0.82)
    ctx.translate(-x, -y)
    ang = math.radians(-62)                       # o marcador sobe para a direita
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    wob = math.sin(t * 17) * 1.6
    x, y = x + wob * 0.4, y + wob * 0.3

    def P(a, b):                                  # coordenadas locais: a ao longo do marcador, b perpendicular
        return (x + dx * a + nx * b, y + dy * a + ny * b)

    # sombra
    ctx.save()
    ctx.translate(16, 26)
    for a0, a1, wd in ((0, 250, 34),):
        ctx.set_line_width(wd)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(0, 0, 0, 0.12)
        ctx.move_to(*P(a0, 0))
        ctx.line_to(*P(a1, 0))
        ctx.stroke()
    ctx.restore()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    def cap(a0, a1, wd, cor, ow=5):
        for w_, c_ in ((wd + 2 * ow, INK), (wd, cor)):
            ctx.set_line_width(w_)
            ctx.set_source_rgb(*c_)
            ctx.move_to(*P(a0, 0))
            ctx.line_to(*P(a1, 0))
            ctx.stroke()

    cap(0, 34, 12, INK, 0)                        # ponta
    cap(30, 215, 36, VERDE)                       # corpo
    cap(165, 215, 36, (0.12, 0.12, 0.12))         # tampa
    # antebraço: entra pela direita, quase na horizontal (cobre a zona ainda por escrever, não o que já está feito)
    hx_, hy_ = P(150, 14)
    ab = math.radians(-17)
    ax, ay = math.cos(ab), math.sin(ab)
    px, py = -ay, ax

    def braco(d0, d1, wd, cor):
        ctx.set_source_rgb(*cor)
        ctx.set_line_width(wd)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.move_to(hx_ + ax * d0, hy_ + ay * d0)
        ctx.line_to(hx_ + ax * d1, hy_ + ay * d1)
        ctx.stroke()
    braco(20, 330, 78, INK)
    braco(20, 330, 66, PELE)
    braco(320, 1500, 116, INK)
    braco(320, 1500, 104, hx("#D9C49B"))
    ctx.set_source_rgb(*INK)                       # punho da manga
    ctx.set_line_width(7)
    ctx.move_to(hx_ + ax * 322 + px * 58, hy_ + ay * 322 + py * 58)
    ctx.line_to(hx_ + ax * 322 - px * 58, hy_ + ay * 322 - py * 58)
    ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx, cy = P(150, 14)
    for rx, ry, col in ((70, 56, INK), (65, 51, PELE)):
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(ang)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(*col)
        ctx.fill()
    for k in range(3):                            # dedos por cima do marcador
        a = 110 + k * 30
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(34)
        ctx.move_to(*P(a, -26))
        ctx.line_to(*P(a + 6, 20))
        ctx.stroke()
        ctx.set_source_rgb(*PELE)
        ctx.set_line_width(25)
        ctx.move_to(*P(a, -26))
        ctx.line_to(*P(a + 6, 20))
        ctx.stroke()
    ctx.set_source_rgb(*INK)                      # polegar
    ctx.set_line_width(36)
    ctx.move_to(*P(176, -4))
    ctx.line_to(*P(130, -48))
    ctx.stroke()
    ctx.set_source_rgb(*PELE)
    ctx.set_line_width(27)
    ctx.move_to(*P(176, -4))
    ctx.line_to(*P(130, -48))
    ctx.stroke()
    ctx.set_source_rgb(*INK)                      # punho
    ctx.set_line_width(8)
    ctx.move_to(*P(300, -42))
    ctx.line_to(*P(300, 104))
    ctx.stroke()
    ctx.restore()

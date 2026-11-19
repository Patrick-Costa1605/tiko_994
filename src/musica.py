"""Música de fundo original, gerada por código (sem amostras nem direitos de autor).

Dedilhado de «ukulele» em Dó maior (Dó – Lá menor – Fá – Sol), baixo suave, uma almofada de acordes e um shaker que entra
depois da abertura. Baixa sozinha sob a voz (sidechain) e sobe um pouco nas pausas e no fim."""
import numpy as np

from audio import SR

BPM = 88
BEAT = 60.0 / BPM
NOTA = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(nome, oit):
    return 440.0 * 2 ** ((NOTA[nome] + 12 * (oit - 4) - 9) / 12)


# acordes: (baixo, [notas do dedilhado grave→agudo])
ACORDES = [
    (("C", 2), [("C", 3), ("E", 3), ("G", 3), ("C", 4), ("E", 4)]),
    (("A", 2), [("A", 2), ("E", 3), ("A", 3), ("C", 4), ("E", 4)]),
    (("F", 2), [("F", 2), ("C", 3), ("F", 3), ("A", 3), ("C", 4)]),
    (("G", 2), [("G", 2), ("D", 3), ("G", 3), ("B", 3), ("D", 4)]),
]
PADRAO = [0, 2, 3, 4, 3, 2, 3, 1]       # índices do acorde, uma colcheia cada


def _pluck(f, dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for h in range(1, 9):
        y += (1.0 / h ** 1.15) * np.exp(-(2.2 + 1.5 * h) * t) * np.sin(2 * np.pi * f * h * (1 + 0.0007 * h * h) * t)
    ataque = np.random.default_rng(int(f)).normal(0, 1, n).astype(np.float32) * np.exp(-t * 200) * 0.25
    y = (y + ataque) * np.minimum(1, t / 0.003)
    return y.astype(np.float32)


def _baixo(f, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-3 * t)
    return (y * np.exp(-1.6 * t) * np.minimum(1, t / 0.01)).astype(np.float32)


def _shaker(dur=0.07, seed=0):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    x = r.normal(0, 1, n).astype(np.float32)
    x = x - np.convolve(x, np.ones(9) / 9, mode="same")          # passa-alto
    t = np.arange(n) / SR
    return (x * np.exp(-t * 55)).astype(np.float32)


def _pad(acorde, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    base, notas = acorde
    y = np.zeros(n, np.float32)
    for k, (nm, o) in enumerate(notas[:3]):
        f = hz(nm, o + 1)
        y += np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.004 * t) * 0.8
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return (y * env * 0.05).astype(np.float32)


def _poe(buf, x, t):
    a = int(round(t * SR))
    if a < 0:                                   # começa antes de zero: corta o início
        x = x[-a:]
        a = 0
    if a >= len(buf) or len(x) == 0:
        return
    b = min(len(buf), a + len(x))
    buf[a:b] += x[: b - a]


def gerar(total, voz, shaker_a=6.0):
    """Música para `total` segundos, com sidechain a partir da voz."""
    n = int(total * SR)
    m = np.zeros(n, np.float32)
    bar = 4 * BEAT
    plucks = {}
    nb = int(total / bar) + 2
    for b in range(nb):
        t0 = b * bar
        ac = ACORDES[b % 4]
        base, notas = ac
        _poe(m, _baixo(hz(*base)) * 0.55, t0)
        _poe(m, _baixo(hz(*base)) * 0.35, t0 + 2 * BEAT)
        _poe(m, _pad(ac, bar * 1.15), t0 - 0.1)
        for i, idx in enumerate(PADRAO):
            nm = notas[idx]
            if nm not in plucks:
                plucks[nm] = _pluck(hz(*nm))
            acento = 1.0 if i % 2 == 0 else 0.72
            _poe(m, plucks[nm] * 0.30 * acento, t0 + i * BEAT / 2)
        if t0 >= shaker_a:                                    # o shaker entra depois da abertura
            for i in range(8):
                _poe(m, _shaker(seed=b * 8 + i) * (0.16 if i % 2 else 0.07), t0 + i * BEAT / 2 + (0.0 if i % 2 == 0 else 0.0))
    # nível: a música fica ~14 dB abaixo da voz quando a voz não fala
    rv = np.sqrt(np.mean(voz[np.abs(voz) > 0.02] ** 2)) if np.any(np.abs(voz) > 0.02) else 0.1
    rm = np.sqrt(np.mean(m ** 2)) + 1e-9
    m *= 0.30 * rv / rm
    # sidechain: gain = 1 - 0.55*envolvente(voz)
    hop = int(SR * 0.02)
    k = len(voz) // hop
    env = np.sqrt((voz[: k * hop].reshape(k, hop) ** 2).mean(axis=1))
    env = np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)
    for _ in range(2):                                         # suavizar (ataque rápido, largada lenta)
        o, s = np.zeros_like(env), 0.0
        for i, v in enumerate(env):
            s += (v - s) * (0.5 if v > s else 0.04)
            o[i] = s
        env = o
    gain = np.interp(np.arange(n) / SR, np.arange(k) * hop / SR, 1 - 0.58 * env)
    # abertura mais presente, fim a subir e a desaparecer
    t = np.arange(n) / SR
    gain *= 1 + 0.6 * np.exp(-t / 3.0)
    gain *= 1 + 0.5 * np.clip((t - (total - 4.5)) / 2.0, 0, 1)
    gain *= np.clip(t / 0.4, 0, 1) * np.clip((total - t) / 1.8, 0, 1)
    return (m * gain).astype(np.float32)

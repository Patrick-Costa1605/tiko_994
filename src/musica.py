"""Música de fundo original, gerada por código (sem amostras nem direitos de autor).

Estilo pop alegre para crianças: melodia viva de xilofone em colcheias, ukulele a rasgar em todas as colcheias, baixo
saltitante, batida leve (bombo, palmas, hi-hat). Progressão Dó – Sol – Lá menor – Fá. Baixa sozinha sob a voz (sidechain)
e sobe um pouco nas pausas e no fim."""
import numpy as np

from audio import SR

BPM = 132
BEAT = 60.0 / BPM
NOTA = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(nome, oit):
    return 440.0 * 2 ** ((NOTA[nome] + 12 * (oit - 4) - 9) / 12)


ACORDES = {          # (raiz, quinta, notas do acorde para o ukulele)
    "C": (("C", 3), ("G", 3), [("C", 4), ("E", 4), ("G", 4), ("C", 5)]),
    "G": (("G", 3), ("D", 4), [("G", 3), ("B", 3), ("D", 4), ("G", 4)]),
    "A": (("A", 2), ("E", 3), [("A", 3), ("C", 4), ("E", 4), ("A", 4)]),
    "F": (("F", 3), ("C", 4), [("F", 3), ("A", 3), ("C", 4), ("F", 4)]),
}
SEQ = ["C", "G", "A", "F", "C", "G", "F", "C"]
MELODIA = [          # por compasso: (tempo em semínimas, nota)
    [(0, ("E", 5)), (0.5, ("E", 5)), (1, ("G", 5)), (2, ("A", 5)), (2.5, ("G", 5)), (3, ("E", 5))],
    [(0, ("D", 5)), (0.5, ("D", 5)), (1, ("G", 5)), (2, ("B", 5)), (2.5, ("A", 5)), (3, ("G", 5))],
    [(0, ("C", 5)), (0.5, ("E", 5)), (1, ("A", 5)), (2, ("A", 5)), (2.5, ("G", 5)), (3, ("E", 5))],
    [(0, ("F", 5)), (0.5, ("A", 5)), (1, ("C", 6)), (2, ("A", 5)), (2.5, ("F", 5)), (3, ("A", 5))],
    [(0, ("G", 5)), (0.5, ("G", 5)), (1, ("C", 6)), (2, ("B", 5)), (2.5, ("G", 5)), (3, ("E", 5))],
    [(0, ("D", 5)), (0.5, ("G", 5)), (1, ("B", 5)), (2, ("D", 6)), (2.5, ("B", 5)), (3, ("G", 5))],
    [(0, ("A", 5)), (0.5, ("A", 5)), (1, ("C", 6)), (2, ("A", 5)), (2.5, ("G", 5)), (3, ("F", 5))],
    [(0, ("G", 5)), (1, ("D", 6)), (2, ("C", 6))],
]


def _xilofone(f, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) * np.exp(-9 * t)
         + 0.40 * np.sin(2 * np.pi * 3.0 * f * t) * np.exp(-16 * t)
         + 0.15 * np.sin(2 * np.pi * 6.0 * f * t) * np.exp(-30 * t))
    return (y * np.minimum(1, t / 0.002)).astype(np.float32)


def _uke(f, dur=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for h in range(1, 7):
        y += (1.0 / h ** 1.2) * np.exp(-(9 + 4 * h) * t) * np.sin(2 * np.pi * f * h * t)
    return (y * np.minimum(1, t / 0.002)).astype(np.float32)


def _baixo(f, dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-8 * t)
    return (y * np.exp(-7 * t) * np.minimum(1, t / 0.005)).astype(np.float32)


def _pandeireta(seed, dur=0.09):
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = r.normal(0, 1, n).astype(np.float32)
    x = x - np.convolve(x, np.ones(7) / 7, mode="same")             # passa-alto
    return (x * np.exp(-t * 45)).astype(np.float32)


def _bombo(dur=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * np.cumsum(55 + 80 * np.exp(-t * 35)) / SR) * np.exp(-t * 22)).astype(np.float32)


def _palma(dur=0.11):
    r = np.random.default_rng(11)
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = r.normal(0, 1, n).astype(np.float32)
    x = x - np.convolve(x, np.ones(5) / 5, mode="same")
    return (x * np.exp(-t * 42)).astype(np.float32)


def _poe(buf, x, t):
    a = int(round(t * SR))
    if a < 0:
        x = x[-a:]
        a = 0
    if a >= len(buf) or len(x) == 0:
        return
    b = min(len(buf), a + len(x))
    buf[a:b] += x[: b - a]


def gerar(total, voz):
    """Música para `total` segundos, com sidechain a partir da voz."""
    n = int(total * SR)
    m = np.zeros(n, np.float32)
    bar = 4 * BEAT
    xil, uke, bx = {}, {}, {}
    for b in range(int(total / bar) + 2):
        t0 = b * bar
        raiz, quinta, notas = ACORDES[SEQ[b % 8]]
        for pos, nome in ((0, raiz), (1.5, raiz), (2, quinta), (3.5, raiz)):   # baixo saltitante
            if nome not in bx:
                bx[nome] = _baixo(hz(*nome) / 2)
            _poe(m, bx[nome] * 0.50, t0 + pos * BEAT)
        for i in range(8):                                            # ukulele a rasgar em colcheias (acento nos contratempos 2 e 4)
            forte = i in (2, 6)
            for k, nome in enumerate(notas):
                if nome not in uke:
                    uke[nome] = _uke(hz(*nome))
                _poe(m, uke[nome] * (0.24 if forte else 0.12 if i % 2 == 0 else 0.15), t0 + i * BEAT / 2 + k * 0.010)
        for k in (0, 2):
            _poe(m, _bombo() * 0.55, t0 + k * BEAT)
        for k in (1, 3):
            _poe(m, _palma() * 0.30, t0 + k * BEAT)
        for i in range(8):
            _poe(m, _pandeireta(b * 8 + i) * (0.12 if i % 2 else 0.06), t0 + i * BEAT / 2)
        for pos, nome in MELODIA[b % 8]:
            if nome not in xil:
                xil[nome] = _xilofone(hz(*nome))
            _poe(m, xil[nome] * 0.36, t0 + pos * BEAT)
    # nível: a música fica ~12 dB abaixo da voz quando a voz não fala
    rv = np.sqrt(np.mean(voz[np.abs(voz) > 0.02] ** 2)) if np.any(np.abs(voz) > 0.02) else 0.1
    rm = np.sqrt(np.mean(m ** 2)) + 1e-9
    m *= 0.36 * rv / rm
    # sidechain: ganho = 1 - 0.58 * envolvente(voz)
    hop = int(SR * 0.02)
    k = len(voz) // hop
    env = np.sqrt((voz[: k * hop].reshape(k, hop) ** 2).mean(axis=1))
    env = np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)
    for _ in range(2):                                                # ataque rápido, largada lenta
        o, s = np.zeros_like(env), 0.0
        for i, v in enumerate(env):
            s += (v - s) * (0.5 if v > s else 0.04)
            o[i] = s
        env = o
    gain = np.interp(np.arange(n) / SR, np.arange(k) * hop / SR, 1 - 0.58 * env)
    t = np.arange(n) / SR
    gain *= 1 + 0.6 * np.exp(-t / 3.0)                                # abertura mais presente
    gain *= 1 + 0.5 * np.clip((t - (total - 4.5)) / 2.0, 0, 1)        # fim a subir e a desaparecer
    gain *= np.clip(t / 0.4, 0, 1) * np.clip((total - t) / 2.0, 0, 1)
    return (m * gain).astype(np.float32)

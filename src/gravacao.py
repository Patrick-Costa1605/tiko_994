"""Usa uma gravação real da voz em vez da síntese: trata o áudio, alinha o texto do guião às palavras ditas
(tempos de `assets/gravacao/palavras.json`, feitos por `src/transcrever.py`) e corta um troço por bloco,
cortando sempre no ponto mais silencioso da pausa entre blocos."""
import difflib
import json

import numpy as np

from audio import SR, decode, esticar, tratar_gravacao, trim_silence
from config import ROOT
from voz import norm, silabas

PAD = 0.10          # folga de silêncio à volta de cada troço
FADE = 0.015
DESLOCA = -0.08     # o Whisper marca o início das palavras ~0,08 s tarde (medido contra o início acústico das frases)


def _sim(a, b):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    if min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a)):
        return 0.85
    return difflib.SequenceMatcher(None, a, b).ratio()


def alinhar(script, ws):
    """Alinha as palavras do guião (lista de str) às palavras reconhecidas (dicts com w,t0,t1).
    Devolve [(t0, t1)] por palavra do guião; as que não casam são interpoladas entre as vizinhas."""
    A = [norm(s) for s in script]
    B = [norm(w["w"]) for w in ws]
    n, m = len(A), len(B)
    GAP = -0.35
    S = np.zeros((n + 1, m + 1))
    S[:, 0] = np.arange(n + 1) * GAP
    S[0, :] = np.arange(m + 1) * GAP
    P = np.zeros((n + 1, m + 1), np.int8)       # 0 diagonal, 1 salta guião, 2 salta reconhecida
    P[:, 0], P[0, :] = 1, 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = _sim(A[i - 1], B[j - 1])
            d = S[i - 1, j - 1] + (s if s >= 0.55 else -9)
            u, l = S[i - 1, j] + GAP, S[i, j - 1] + GAP
            S[i, j] = max(d, u, l)
            P[i, j] = 0 if S[i, j] == d else (1 if S[i, j] == u else 2)
    i, j, par = n, m, {}
    while i > 0 or j > 0:
        if i > 0 and j > 0 and P[i, j] == 0:
            par[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif i > 0 and (j == 0 or P[i, j] == 1):
            i -= 1
        else:
            j -= 1
    out = [None] * n
    for i, j in par.items():
        out[i] = (ws[j]["t0"], ws[j]["t1"])
    k = 0
    while k < n:                                  # interpola os buracos
        if out[k] is not None:
            k += 1
            continue
        a = k
        while k < n and out[k] is None:
            k += 1
        t_ini = out[a - 1][1] if a > 0 else (out[k][0] - 0.3 * (k - a) if k < n else 0.0)
        t_fim = out[k][0] if k < n else t_ini + 0.3 * (k - a)
        pesos = np.array([silabas(script[q]) for q in range(a, k)], float)
        e = np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum()
        for q in range(a, k):
            out[q] = (t_ini + (t_fim - t_ini) * e[q - a], t_ini + (t_fim - t_ini) * e[q - a + 1])
    return out, len(par)


def _minimo(x, a, b):
    """Instante (s) de menor energia no intervalo [a, b] (janelas de 10 ms)."""
    hop = int(SR * 0.01)
    i0, i1 = int(a * SR), max(int(b * SR), int(a * SR) + hop)
    seg = x[i0:i1]
    k = max(1, len(seg) // hop)
    r = np.sqrt((seg[: k * hop].reshape(k, hop) ** 2).mean(axis=1))
    return a + (int(np.argmin(r)) + 0.5) * hop / SR


def _aparar(x, pad):
    """Corta o silêncio das pontas deixando `pad` s. Devolve (troço, início cortado em s, folga que sobrou no fim em s, onde a fala começa no troço em s)."""
    hop = int(SR * 0.01)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    idx = np.where(rms > max(0.008, 0.06 * np.percentile(rms, 95)))[0]
    if len(idx) == 0:
        return x, 0.0, 0.0, 0.0
    a = max(0, idx[0] * hop - int(pad * SR))
    b = min(len(x), (idx[-1] + 1) * hop + int(pad * SR))
    return x[a:b], a / SR, (b - (idx[-1] + 1) * hop) / SR, (idx[0] * hop - a) / SR


def preparar(cfg, blocos):
    """Devolve, por bloco, {"x": voz (já tratada), "words": [{text,t0,t1}] relativos ao início de x, "fim": fim da fala}."""
    g = cfg["gravacao"]
    cache = json.loads((ROOT / g["palavras"]).read_text(encoding="utf-8"))["palavras"]
    voz = tratar_gravacao(decode(str(ROOT / g["audio"])))

    script, dono = [], []
    for bi, b in enumerate(blocos):
        for w in b["texto"].split():
            script.append(w)
            dono.append(bi)
    tempos, casadas = alinhar(script, cache)
    print(f"  gravação: {casadas}/{len(script)} palavras do guião casadas com a fala ({len(cache)} reconhecidas)")

    por_bloco = [[] for _ in blocos]
    for w, (t0, t1), bi in zip(script, tempos, dono):
        por_bloco[bi].append({"text": w, "t0": t0, "t1": max(t1, t0 + 0.06)})

    # pontos de corte: o mais silencioso da pausa entre blocos
    cortes = [max(0.0, por_bloco[0][0]["t0"] - 0.5)]
    for bi in range(len(blocos) - 1):
        a, b = por_bloco[bi][-1]["t1"], por_bloco[bi + 1][0]["t0"]
        cortes.append(_minimo(voz, min(a + 0.02, b - 0.05), max(b - 0.02, a + 0.05)) if b - a > 0.12 else _minimo(voz, (a + b) / 2 - 0.07, (a + b) / 2 + 0.07))
    for bi in range(1, len(blocos)):                          # `corte` (s na gravação): corte manual entre este bloco e o anterior
        if blocos[bi].get("corte") is not None:
            cortes[bi] = float(blocos[bi]["corte"])
    cortes.append(min(len(voz) / SR, por_bloco[-1][-1]["t1"] + 0.6))

    saida = []
    for bi, ws in enumerate(por_bloco):
        a, b = int(cortes[bi] * SR), int(cortes[bi + 1] * SR)
        x = voz[a:b].copy()
        manual_ini = bi > 0 and blocos[bi].get("corte") is not None
        manual_fim = bi + 1 < len(blocos) and blocos[bi + 1].get("corte") is not None
        x, off, cauda, onset = _aparar(x, PAD)
        ritmo = float(blocos[bi].get("ritmo", 1.0))           # <1 alarga o troço (mais lento), mantendo o tom
        if ritmo != 1.0:
            x = esticar(x, ritmo)
        for lado, f_s in (("ini", 0.004 if manual_ini else FADE), ("fim", 0.008 if manual_fim else FADE)):
            f = int(f_s * SR)
            if lado == "ini":
                x[:f] *= np.linspace(0, 1, f)
            else:
                x[-f:] *= np.linspace(1, 0, f)
        t_base = a / SR + off
        rel = [{"text": w["text"], "t0": max(0.0, w["t0"] + DESLOCA - t_base) / ritmo, "t1": max(0.0, w["t1"] + DESLOCA - t_base) / ritmo} for w in ws]
        onset, cauda = onset / ritmo, cauda / ritmo
        dur = len(x) / SR
        rel[0]["t0"] = onset                                    # a 1.ª palavra começa onde o áudio começa mesmo (o troço foi aparado)
        rel[-1]["t1"] = max(rel[-1]["t0"] + 0.1, dur - cauda) # e a última acaba onde a fala acaba
        for a_, b_ in zip(rel, rel[1:]):
            b_["t0"] = max(b_["t0"], a_["t0"])
            b_["t1"] = max(b_["t1"], b_["t0"] + 0.06)
        saida.append({"x": x, "words": rel, "fim": rel[-1]["t1"]})
    return saida

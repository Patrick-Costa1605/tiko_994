"""Música de fundo: uma faixa gravada (MP3/WAV), ajustada à duração do vídeo.

A faixa mantém o início e o fim naturais (o acorde final fecha o vídeo). Se for mais curta do que o vídeo,
repete-se um troço do meio cujo comprimento é um múltiplo do ciclo de acordes, com crossfade em potência
constante centrado num tempo forte; o pequeno resto ajusta-se acelerando/abrandando a faixa sem mudar o tom.
Se for mais longa, a mesma emenda serve para saltar o excesso (Q < P na configuração não é necessário: basta
indicar `emenda` = [salta_de, salta_para] com salta_para > salta_de).

Configuração no guião (`"musica"`):
    ficheiro   caminho da faixa
    emenda     [P, Q] em segundos da faixa original: toca até Q e continua a partir de P (repete P..Q)
               ou, se P > Q, salta de Q para P (corta Q..P)
    fim_som    instante (s, na faixa original) em que o acorde final deixa de soar
    crossfade  duração do crossfade da emenda (s)
    fade_in    fade-in no arranque (s)
    lufs       volume base da música na mistura final (LUFS integrados, até `subida.t`)
    subida     {"t": s, "db": +dB, "rampa": s}: ganho extra a partir de t (apelo final)
    folga_fim  o acorde final acaba esta quantidade de segundos antes do fim do vídeo
"""
import numpy as np

from audio import SR, decode, esticar
from config import ROOT


def _xfade(a, b):
    """Crossfade em potência constante entre dois troços do mesmo comprimento."""
    t = np.linspace(0, np.pi / 2, len(a), dtype=np.float32)
    return a * np.cos(t) + b * np.sin(t)


def faixa(total, cfg):
    """Devolve (música mono a SR com `total` s já com fade-in/subida, info) — o nível base é posto na mistura."""
    x = decode(str(ROOT / cfg["ficheiro"]))
    P, Q = (float(v) for v in cfg["emenda"])
    h = int(float(cfg.get("crossfade", 1.8)) * SR / 2)
    p, q = int(round(P * SR)), int(round(Q * SR))
    # toca [0, Q) e continua em P: crossfade centrado na emenda (Q na 1.ª passagem, P na 2.ª)
    y = np.concatenate([x[: q - h], _xfade(x[q - h: q + h], x[p - h: p + h]), x[p + h:]])
    fim_som = float(cfg["fim_som"]) + (Q - P)                     # onde o acorde final acaba, já na faixa emendada
    alvo_fim = total - float(cfg.get("folga_fim", 0.15))
    tempo = fim_som / alvo_fim                                    # >1 acelera, <1 abranda; o tom não muda
    if abs(tempo - 1) > 1e-4:
        y = esticar(y, tempo)
    n = int(round(total * SR))
    y = np.pad(y, (0, max(0, n - len(y))))[:n].astype(np.float32)
    t = np.arange(n) / SR
    g = np.clip(t / float(cfg.get("fade_in", 1.0)), 0, 1)
    sub = cfg.get("subida")
    if sub:
        rampa = float(sub.get("rampa", 0.4))
        g = g * 10 ** (float(sub["db"]) / 20 * np.clip((t - float(sub["t"])) / rampa, 0, 1))
    info = {"tempo": tempo, "emenda_no_video": (Q / tempo), "fim_no_video": fim_som / tempo, "duracao_faixa": len(x) / SR}
    return (y * g).astype(np.float32), info

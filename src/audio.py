"""Áudio: ffmpeg, decodificação, corte de silêncio e efeitos procedurais (o riscar do marcador, o virar da página)."""
import shutil
import subprocess
import wave

import numpy as np

SR = 24000


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def decode(path):
    out = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def trim_silence(x, pad=0.04):
    hop = int(SR * 0.01)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    thr = max(0.008, 0.06 * np.percentile(rms, 95))
    idx = np.where(rms > thr)[0]
    if len(idx) == 0:
        return x, 0.0
    a = max(0, idx[0] * hop - int(pad * SR))
    b = min(len(x), (idx[-1] + 1) * hop + int(pad * SR))
    return x[a:b], a / SR


def _mov(x, n):
    c = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    return ((c[n:] - c[:-n]) / n).astype(np.float32)


def risco(dur, seed=0):
    """O som de um marcador a riscar papel: ruído filtrado com uma pulsação lenta (a velocidade da mão)."""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    x = r.normal(0, 1, n + 40).astype(np.float32)
    x = x[20:20 + n] - _mov(x, 21)[:n]                         # passa-alto
    x = np.convolve(x, np.ones(3) / 3, mode="same")
    t = np.arange(n) / SR
    mod = 0.65 + 0.35 * np.sin(2 * np.pi * (7 + 3 * r.random()) * t + r.random() * 6)
    env = np.minimum(1, np.minimum(t / 0.03, (dur - t) / 0.05))
    return (x * mod * np.clip(env, 0, 1) * 0.055).astype(np.float32)


def folha(dur=0.55):
    """O virar da página: um sopro de ruído com a intensidade a subir e a descer."""
    r = np.random.default_rng(3)
    n = int(dur * SR)
    x = r.normal(0, 1, n).astype(np.float32)
    x = _mov(np.concatenate([x, np.zeros(10, np.float32)]), 6)[:n]
    t = np.arange(n) / SR
    return (x * np.sin(np.pi * t / dur) ** 1.6 * 0.5).astype(np.float32)


def tratar_voz(x):
    """Torna a voz sintética menos seca: passa-alto, calor nos graves, compressão suave e uma sala muito curta."""
    af = ("highpass=f=85,equalizer=f=180:t=q:w=1.0:g=2.5,equalizer=f=3200:t=q:w=1.2:g=-1.5,"
          "acompressor=threshold=0.09:ratio=2.6:attack=8:release=140:makeup=1.6,"
          "aecho=0.88:0.55:19|41:0.16|0.09")
    out = subprocess.run([ffmpeg_exe(), "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", af, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                         input=x.astype(np.float32).tobytes(), check=True, capture_output=True).stdout
    y = np.frombuffer(out, dtype=np.float32).copy()
    if len(y) < len(x):
        y = np.concatenate([y, np.zeros(len(x) - len(y), np.float32)])
    return y[: len(x)]

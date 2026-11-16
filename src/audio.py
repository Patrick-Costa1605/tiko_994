"""Áudio: ffmpeg, análise para lip-sync (amplitude + espectro) e efeitos sonoros procedurais."""
import shutil
import subprocess
import wave

import numpy as np

SR = 24000


def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # pragma: no cover
        raise SystemExit("ffmpeg não encontrado. Instala-o ou faz `pip install imageio-ffmpeg`.") from e


def decode(path: str) -> np.ndarray:
    out = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def write_wav(path: str, x: np.ndarray) -> None:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def trim_silence(x: np.ndarray, pad: float = 0.04):
    hop = int(SR * 0.01)
    n = len(x) // hop
    if n == 0:
        return x, 0.0
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    thr = max(0.008, 0.06 * np.percentile(rms, 95))
    idx = np.where(rms > thr)[0]
    if len(idx) == 0:
        return x, 0.0
    a = max(0, idx[0] * hop - int(pad * SR))
    b = min(len(x), (idx[-1] + 1) * hop + int(pad * SR))
    return x[a:b], a / SR


# ------------------------------------------------------------------ lip-sync
def mouth_tracks(x: np.ndarray, fps: int, n_frames: int):
    """Por frame: abertura (0..1) e «vogal» (0 = A/O arredondada … 1 = E/I larga).

    A abertura vem do RMS (janela de 25 ms centrada no frame); a vogal vem do centroide
    espectral (FFT de 512 amostras): graves => A/O, agudos/sibilantes => E/I.
    """
    centers = (np.arange(n_frames) / fps * SR).astype(int)
    half = int(SR * 0.0125)
    sq = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)])
    lo, hi = np.clip(centers - half, 0, len(x)), np.clip(centers + half, 0, len(x))
    rms = np.sqrt((sq[hi] - sq[lo]) / np.maximum(hi - lo, 1))

    pad = np.concatenate([np.zeros(256, np.float32), x, np.zeros(256, np.float32)])
    win = np.hanning(512).astype(np.float32)
    freqs = np.fft.rfftfreq(512, 1 / SR)
    cent = np.zeros(n_frames)
    for i, c in enumerate(centers):
        seg = pad[c:c + 512]
        if len(seg) < 512:
            continue
        mag = np.abs(np.fft.rfft(seg * win))
        cent[i] = (freqs * mag).sum() / max(mag.sum(), 1e-9)

    voiced = rms[rms > 0.01]
    ref = np.percentile(voiced, 90) if len(voiced) else 1.0
    raw = np.clip(rms / max(ref, 1e-6), 0, 1.3)
    raw[rms < 0.012] = 0.0
    vow = np.clip((cent - 900) / 1500, 0, 1)

    o, v = np.zeros(n_frames), np.zeros(n_frames)
    so = sv = 0.0
    for i in range(n_frames):
        so += (raw[i] - so) * (0.80 if raw[i] > so else 0.38)
        if raw[i] > 0.05:
            sv += (vow[i] - sv) * 0.45
        o[i], v[i] = so, sv
    return np.clip(o * 0.95, 0, 1).astype(np.float32), v.astype(np.float32)


# ------------------------------------------------------------------ efeitos sonoros procedurais
def _t(dur):
    return np.arange(int(dur * SR)) / SR


def sfx_pop():
    t = _t(0.16)
    f = 180 + 520 * np.exp(-t * 38)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 26)).astype(np.float32)


def sfx_whoosh():
    rng = np.random.default_rng(7)
    t = _t(0.5)
    n = rng.normal(0, 1, len(t))
    out = np.zeros_like(n)
    s = 0.0
    for i in range(len(t)):                       # passa-baixo com corte a subir e descer
        a = 0.04 + 0.5 * np.sin(np.pi * t[i] / 0.5) ** 2
        s += (n[i] - s) * a
        out[i] = s
    return (out * np.sin(np.pi * t / 0.5) ** 1.5 * 2.2).astype(np.float32)


def sfx_ding():
    t = _t(0.9)
    y = sum(a * np.sin(2 * np.pi * 1318.5 * k * t) * np.exp(-t * d)
            for k, a, d in ((1, 1.0, 5), (2.0, 0.4, 8), (3.01, 0.2, 12)))
    return (y * 0.6).astype(np.float32)


def sfx_boing():
    t = _t(0.55)
    f = 110 + 160 * np.exp(-t * 6) + 25 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 5)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5)).astype(np.float32)


def sfx_tick():
    t = _t(0.05)
    return (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)).astype(np.float32)


SFX = {"pop": sfx_pop, "whoosh": sfx_whoosh, "ding": sfx_ding, "boing": sfx_boing, "tick": sfx_tick}
_cache = {}


def add_sfx(full, name, t, gain=1.0):
    if name not in SFX:
        raise SystemExit(f"Efeito sonoro desconhecido «{name}». Disponíveis: {', '.join(SFX)}")
    if name not in _cache:
        x = SFX[name]()
        _cache[name] = x / max(float(np.abs(x).max()), 1e-6)
    s = _cache[name] * gain * 0.45
    a = int(max(t, 0) * SR)
    b = min(len(full), a + len(s))
    if b > a:
        full[a:b] += s[: b - a]

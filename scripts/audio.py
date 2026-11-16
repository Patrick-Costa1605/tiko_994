"""Utilitários de áudio: ffmpeg, decodificação, análise de amplitude (lip-sync)."""
import shutil
import subprocess
import wave

import numpy as np

SR = 24000  # taxa de amostragem interna (mono)


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
    """Decodifica qualquer áudio para float32 mono @SR."""
    out = subprocess.run(
        [ffmpeg_exe(), "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def write_wav(path: str, x: np.ndarray) -> None:
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def trim_silence(x: np.ndarray, pad: float = 0.05):
    """Corta silêncio inicial/final. Devolve (áudio, segundos cortados no início)."""
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


def _window_mean(v: np.ndarray, centers: np.ndarray, half: int) -> np.ndarray:
    c = np.concatenate([[0.0], np.cumsum(v, dtype=np.float64)])
    lo = np.clip(centers - half, 0, len(v))
    hi = np.clip(centers + half, 0, len(v))
    return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)


def mouth_tracks(x: np.ndarray, fps: int, n_frames: int):
    """Curvas por frame para o lip-sync: abertura (0..1) e largura (0..1).

    - abertura: RMS numa janela de ~40 ms, normalizado, com gate de ruído e
      suavização assimétrica (abre depressa, fecha mais devagar).
    - largura: taxa de cruzamentos por zero (sons sibilantes/«i» => boca mais larga).
    """
    centers = (np.arange(n_frames) / fps * SR).astype(int)
    half = int(SR * 0.02)
    rms = np.sqrt(_window_mean(x.astype(np.float64) ** 2, centers, half))
    sgn = np.signbit(x).astype(np.int8)
    zc = np.abs(np.diff(sgn, prepend=sgn[0])).astype(np.float64)
    zcr = _window_mean(zc, centers, half)

    voiced = rms[rms > 0.01]
    ref = np.percentile(voiced, 90) if len(voiced) else 1.0
    raw = np.clip(rms / max(ref, 1e-6), 0, 1.3)
    raw[rms < 0.012] = 0.0

    o = np.zeros(n_frames)
    s = 0.0
    for i, v in enumerate(raw):
        s += (v - s) * (0.65 if v > s else 0.30)
        o[i] = s
    o = np.clip(o * 0.95, 0, 1)

    w = np.clip((zcr - 0.04) / 0.20, 0, 1)
    ws = np.zeros(n_frames)
    s = 0.0
    for i, v in enumerate(w):
        s += (v - s) * 0.3
        ws[i] = s
    return o.astype(np.float32), ws.astype(np.float32)

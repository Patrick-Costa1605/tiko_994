"""Áudio: ffmpeg, decodificação, corte de silêncio e efeitos procedurais (o riscar do marcador, o virar da página)."""
import shutil
import subprocess
import wave

import numpy as np

SR = 48000


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


def _ffmpeg_pcm(x, af, extra=(), cwd=None):
    out = subprocess.run([ffmpeg_exe(), "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", af, *extra, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                         input=x.astype(np.float32).tobytes(), check=True, capture_output=True, cwd=cwd).stdout
    y = np.frombuffer(out, dtype=np.float32).copy()
    return np.concatenate([y, np.zeros(max(0, len(x) - len(y)), np.float32)])[: len(x)]


def tratar_gravacao(x):
    """Melhora uma gravação de telemóvel: repara picos cortados, tira graves e «caixa», dá presença, doma os «ss»,
    comprime de leve e nivela a voz (≈ -19 dBFS de média na fala) com um limitador por cima."""
    from config import ROOT
    # 1) rede neuronal (RNNoise) tira o sopro e o ruído de fundo; 2) expansor suave encurta as «caudas» de sala e o chiado entre palavras
    x = _ffmpeg_pcm(x, "adeclip,arnndn=m=rnnoise_sh.rnnn:mix=0.85,agate=threshold=0.012:ratio=2.2:attack=4:release=160:range=0.3:knee=4",
                    cwd=str(ROOT / "assets" / "gravacao"))
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = np.concatenate([x[480:], np.zeros(480, np.float32)])       # o RNNoise atrasa 10 ms (480 amostras a 48 kHz): realinha com o original
    y = _ffmpeg_pcm(x, "highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3000:t=q:w=1.0:g=2.2,"
                       "treble=g=0.8:f=8000,lowpass=f=15000,deesser=i=0.4:m=0.5:f=0.5,"
                       "acompressor=threshold=0.09:ratio=3:attack=6:release=140:makeup=2")
    hop = int(SR * 0.02)
    n = len(y) // hop
    rms = np.sqrt((y[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    fala = rms[rms > 0.02]
    alvo = 10 ** (-19 / 20)
    y = y * (alvo / (float(np.sqrt((fala ** 2).mean())) + 1e-9))
    return _ffmpeg_pcm(y, "alimiter=limit=0.9:attack=3:release=60:level=false")


def normalizar_loudness(x, alvo=-15.0, pico=-1.5):
    """EBU R128 em duas passagens (linear): o Instagram fica à vontade com ~-14 LUFS."""
    import json as _j
    import re as _re
    a = subprocess.run([ffmpeg_exe(), "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"loudnorm=I={alvo}:TP={pico}:LRA=9:print_format=json", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    m = _j.loads(_re.findall(r"\{.*?\}", a.stderr.decode("utf-8", "ignore"), _re.S)[-1])
    af = (f"loudnorm=I={alvo}:TP={pico}:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    return _ffmpeg_pcm(x, af)


def esticar(x, tempo):
    """Muda a velocidade (tempo<1 = mais lento) sem mexer no tom nem nas vogais (rubberband). Devolve o troço com a nova duração."""
    out = subprocess.run([ffmpeg_exe(), "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                          f"rubberband=tempo={tempo}:pitch=1:transients=mixed:formant=preserved", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                         input=x.astype(np.float32).tobytes(), check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def lufs(x):
    """Loudness integrado (EBU R128, LUFS) de um sinal mono a SR."""
    import re as _re
    a = subprocess.run([ffmpeg_exe(), "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "ebur128", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    return float(_re.findall(r"I:\s+(-?[\d.]+) LUFS", a.stderr.decode("utf-8", "ignore"))[-1])


def pico_real(x):
    """True peak (dBTP, sobre-amostrado 4x pelo ebur128) de um sinal mono a SR."""
    import re as _re
    a = subprocess.run([ffmpeg_exe(), "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    return float(_re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", a.stderr.decode("utf-8", "ignore"))[-1])


def normalizar_linear(x, alvo=-16.0, teto=-1.5):
    """Ganho fixo até `alvo` LUFS e um limitador rápido só nos picos acima de `teto` dBFS (as proporções entre voz e música
    mantêm-se). Ao contrário do `loudnorm`, nunca passa para modo dinâmico. Devolve (sinal, ganho aplicado)."""
    G = 10 ** ((alvo - lufs(x)) / 20)
    y = _ffmpeg_pcm(x * G, f"alimiter=limit={10 ** (teto / 20):.4f}:attack=1:release=40:level=false")
    return y, G

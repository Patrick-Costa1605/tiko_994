#!/usr/bin/env python3
"""Gerador de Reels do Tiko (994-Caxinas) — 1080x1920 @ 60 fps.

Uso:
    python src/render.py guioes/ep01_apresentacao.json              # -> output/ep01_apresentacao.mp4
    python src/render.py guioes/ep01_apresentacao.json --png 0.3 8  # só PNGs de teste (segundos)

Pipeline: guião -> edge-tts (por pedaço, com pausas) -> timestamps por palavra -> lip-sync (amplitude +
espectro) -> efeitos sonoros procedurais -> física do lenço -> frames vetoriais (pycairo, em paralelo)
-> ffmpeg (H.264 + AAC).
"""
import argparse
import json
import math
import multiprocessing as mp
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audio import SR, add_sfx, decode, ffmpeg_exe, mouth_tracks, trim_silence, write_wav  # noqa: E402
from character import LADO, body_motion, intro_motion, pose_at, tiko_dx  # noqa: E402
from config import FPS, H, ROOT, TIKO_SCALE, W  # noqa: E402
from subtitles import make_chunks  # noqa: E402
from tts import parse_markup, spoken_tokens, split_pauses, synthesize, syllables  # noqa: E402

DEFAULT_VOICE = {"nome": "pt-PT-DuarteNeural", "velocidade": "+14%", "tom": "+3Hz", "volume": "+0%"}


# ------------------------------------------------------------------ timeline
def assign_words(words, pron, wb, dur, off, label):
    toks = [spoken_tokens(w["text"], pron).split() for w in words]
    n = sum(len(t) for t in toks)
    if len(wb) == n:                                   # timestamps reais do edge-tts
        k = 0
        for w, tk in zip(words, toks):
            a, b = wb[k], wb[k + len(tk) - 1]
            k += len(tk)
            w["t0"], w["t1"] = max(0.0, a["t0"] - off), min(dur, b["t1"] - off)
        method = "edge-tts"
    else:                                              # plano B: proporcional às sílabas
        print(f"  ! «{label}»: {len(wb)} marcas vs {n} palavras; a estimar por sílabas", file=sys.stderr)
        wts = np.array([syllables(" ".join(t)) for t in toks], dtype=float)
        edges = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        a0, a1 = 0.04, max(dur - 0.04, 0.1)
        for w, s, e in zip(words, edges[:-1], edges[1:]):
            w["t0"], w["t1"] = a0 + (a1 - a0) * s, a0 + (a1 - a0) * e
        method = "estimado"
    last = 0.0
    for w in words:
        w["t0"] = max(w["t0"], last)
        w["t1"] = max(w["t1"], w["t0"] + 0.08)
        last = w["t0"]
    return method


def norm_props(v):
    return [] if v is None else ([v] if isinstance(v, str) else list(v))


def simulate_scarf(tl):
    """Física leve do lenço: duas pontas = osciladores amortecidos excitados pela aceleração do corpo."""
    n, dt, S = tl["n_frames"], 1.0 / FPS, TIKO_SCALE
    xs, ys = np.zeros(n + 2), np.zeros(n + 2)
    for i in range(n + 2):
        t = (i - 1) * dt
        p = pose_at(tl["blocks"], t)
        bx, by, jump = body_motion(t, p)
        xs[i] = tiko_dx(tl["blocks"], t) + bx * S
        ys[i] = (by - jump) * S + intro_motion(t)[0]
    ax = (xs[2:] - 2 * xs[1:-1] + xs[:-2]) / dt ** 2
    ay = (ys[2:] - 2 * ys[1:-1] + ys[:-2]) / dt ** 2
    out = np.zeros((n, 3), dtype=np.float32)
    st = {"l": [0.0, 0.0, 80.0], "r": [0.0, 0.0, 105.0], "u": [0.0, 0.0, 70.0]}   # pos, vel, k
    for f in range(n):
        for key, force in (("l", -ax[f] * 0.0045), ("r", -ax[f] * 0.0036), ("u", ay[f] * 0.0030)):
            x, v, k = st[key]
            v += (-k * x - 6.5 * v + force) * dt
            x += v * dt
            st[key] = [0.7 * math.tanh(x / 0.7), v, k]
        out[f] = (st["l"][0], st["r"][0], st["u"][0])
    return out


def build_timeline(script_path, hat=None):
    cfg = json.loads(Path(script_path).read_text(encoding="utf-8"))
    voz = {**DEFAULT_VOICE, **cfg.get("voz", {})}
    pron = cfg.get("pronuncia", {})
    gap = float(cfg.get("pausa_entre_blocos", 0.14))
    t = float(cfg.get("inicio", 0.25))

    blocks, parts = [], []
    for rb in cfg["blocos"]:
        start, cursor, words_all, method = t, t, [], "edge-tts"
        pieces = split_pauses(rb["texto"])
        for txt, pause in pieces:
            words = parse_markup(txt)
            spoken = " ".join(spoken_tokens(w["text"], pron) for w in words)
            mp3, wb = synthesize(spoken, voz["nome"], rb.get("velocidade", voz["velocidade"]),
                                 rb.get("tom", voz["tom"]), voz["volume"])
            x, off = trim_silence(decode(mp3))
            dur = len(x) / SR
            m = assign_words(words, pron, wb, dur, off, txt[:30])
            method = m if m != "edge-tts" else method
            for w in words:
                w["t0"] += cursor
                w["t1"] += cursor
            parts.append((cursor, x))
            words_all += words
            end = cursor + dur
            cursor = end + pause
        props = norm_props(rb.get("ilustracao"))
        lado = rb.get("lado", "esquerda" if props else "centro")
        album_dx = (235 if lado == "direita" else -235 if lado == "esquerda" else 0) if rb.get("pagina") else None
        cam = rb.get("camara", "normal")
        pts = [start + 0.05] if cam == "punch" else []
        pts += [start + float(s) for s in rb.get("punches", [])]
        blocks.append({
            "texto": " ".join(p for p, _ in pieces), "estado": rb.get("estado", "normal"), "props": props,
            "start": start, "end": end, "words": words_all, "chunks": make_chunks(words_all), "method": method,
            "camara": cam, "punches": pts, "tiko_dx": album_dx if album_dx is not None else LADO[lado], "sfx": rb.get("sfx", []),
            "pagina": rb.get("pagina"),
        })
        t = end + float(rb.get("pausa_depois", gap))

    total = blocks[-1]["end"] + float(cfg.get("final_extra", 1.0))
    for i, b in enumerate(blocks):
        b["vstart"] = 0.0 if i == 0 else b["start"] - gap / 2
    for i, b in enumerate(blocks):
        b["vend"] = blocks[i + 1]["vstart"] if i + 1 < len(blocks) else total
        prev = blocks[i - 1] if i else None
        b["appear"] = []
        for j, name in enumerate(b["props"]):
            if prev and name in prev["props"]:
                b["appear"].append(prev["appear"][prev["props"].index(name)])
            else:
                b["appear"].append(max(b["vstart"], 0.0) + 0.15 + 0.16 * j)

    n_frames = int(math.ceil(total * FPS))
    voice = np.zeros(int(math.ceil(total * SR)) + SR // 2, dtype=np.float32)
    for start, x in parts:
        a = int(start * SR)
        voice[a:a + len(x)] += x
    mo, mv = mouth_tracks(voice, FPS, n_frames)        # lip-sync só a partir da voz (sem efeitos)

    # ---- efeitos sonoros: automáticos (entrada, punch-ins, ícones, emoções) + manuais do guião
    sfx = [(0.0, "whoosh", 0.9), (0.45, "pop", 0.9)]
    for b in blocks:
        sfx += [(p, "pop", 0.45) for p in b["punches"]]
        for j, (name, ap) in enumerate(zip(b["props"], b["appear"])):
            key = name.split("@")[0]
            if ap < b["vstart"] + 0.05 and b is not blocks[0]:
                continue
            if j == 0:
                sfx.append((ap - 0.05, "whoosh", 0.55))
            sfx.append((ap + 0.05, "ding" if key in ("logo", "estrelas", "estrela") else "pop", 0.8))
            if key == "tenda":
                sfx.append((ap + 1.05, "ding", 0.5))
            if key == "tenda_caida":
                sfx.append((ap + 0.1, "boing", 0.9))
            if key == "exclamacao":
                sfx.append((ap + 0.12, "tick", 0.8))
        if b is not blocks[0] and b["estado"] in ("entusiasmado", "assustado"):
            sfx.append((b["vstart"] + 0.02, "boing", 0.8))
        for s in b["sfx"]:
            s = {"tipo": s} if isinstance(s, str) else s
            sfx.append((b["start"] + float(s.get("em", 0)), s["tipo"], float(s.get("ganho", 0.8))))
    for i, b in enumerate(blocks):                     # álbum: virar de página, fotos a surgir, rabiscos
        if not b.get("pagina"):
            continue
        if i > 0:
            sfx.append((b["vstart"] - 0.10, "whoosh", 0.45))
        sfx.append((b["vstart"] + 0.12, "pop", 0.7))
        for r in b["pagina"].get("rabiscos", []):
            sfx.append((b["vstart"] + 0.55, {"lama": "boing", "estrelas": "ding", "uivo": "boing"}.get(r, "tick"), 0.6))
    fx = np.zeros_like(voice)
    for tt, name, g in sfx:
        add_sfx(fx, name, tt, g)
    mix = voice + 0.55 * fx
    peak = float(np.abs(mix).max())
    if peak > 0.95:
        mix *= 0.95 / peak

    tl = {
        "fps": FPS, "total": total, "n_frames": n_frames, "blocks": blocks, "mouth_o": mo, "mouth_v": mv,
        "punches": sorted(p for b in blocks for p in b["punches"]),
        "watermark": cfg.get("marca_dagua", "@994caxinas"),
        "chapeu": (cfg.get("personagem", {}).get("chapeu", True) and cfg.get("traje") != "lobito") if hat is None else hat,
        "traje": cfg.get("traje"), "album": any(b.get("pagina") for b in blocks),
        "titulo": cfg.get("titulo", ""),
    }
    tl["scarf"] = simulate_scarf(tl)
    return tl, mix


# ------------------------------------------------------------------ render paralelo
_R = None


def _init(tl):
    global _R
    from scene import Renderer
    _R = Renderer(tl)


def _frame(f):
    return _R.render(f)


def encode(tl, wav_path, out_path, workers):
    cmd = [ffmpeg_exe(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(wav_path), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{tl['n_frames'] / FPS:.3f}", "-movflags", "+faststart", str(out_path)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    ctx = mp.get_context("fork" if sys.platform == "linux" else "spawn")
    with ctx.Pool(workers, initializer=_init, initargs=(tl,)) as pool:
        for i, buf in enumerate(pool.imap(_frame, range(tl["n_frames"]), chunksize=2)):
            ff.stdin.write(buf)
            if i % 120 == 0 or i == tl["n_frames"] - 1:
                print(f"\r  frame {i + 1}/{tl['n_frames']}  ({time.time() - t0:.0f}s)", end="", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg falhou")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("guiao", help="ficheiro JSON do episódio (pasta guioes/)")
    ap.add_argument("-o", "--saida", help="MP4 de saída (por omissão output/<nome>.mp4)")
    ap.add_argument("--png", nargs="+", type=float, metavar="SEG", help="só gera PNGs de teste nesses instantes")
    ap.add_argument("--sem-chapeu", action="store_true")
    ap.add_argument("-j", "--workers", type=int, default=max(1, (mp.cpu_count() or 2)))
    a = ap.parse_args()

    name = Path(a.guiao).stem
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    print(f"[1/3] Voz, timestamps, lip-sync e efeitos ({name})")
    tl, mix = build_timeline(a.guiao, hat=False if a.sem_chapeu else None)
    for b in tl["blocks"]:
        print(f"  {b['start']:5.2f}–{b['end']:5.2f}s  {b['estado']:<12} [{b['method']}] {b['texto'][:58]}")
    print(f"  duração total: {tl['total']:.2f}s ({tl['n_frames']} frames @ {FPS} fps)")

    wav = out_dir / f"{name}.wav"
    write_wav(str(wav), mix[: int(tl["total"] * SR)])
    subprocess.run([ffmpeg_exe(), "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-q:a", "2",
                    str(out_dir / f"{name}.mp3")], check=True)
    (out_dir / f"{name}.timings.json").write_text(json.dumps({
        "titulo": tl["titulo"], "duracao": tl["total"], "fps": FPS,
        "blocos":
                  [{"texto": b["texto"], "estado": b["estado"], "inicio": round(b["start"], 3), "fim": round(b["end"], 3),
                    "palavras": [{"texto": w["text"], "t0": round(w["t0"], 3), "t1": round(w["t1"], 3)} for w in b["words"]]}
                   for b in tl["blocks"]]}, ensure_ascii=False, indent=1), encoding="utf-8")

    if a.png:
        print("[2/3] PNGs de teste")
        from scene import Renderer
        r = Renderer(tl)
        for s in a.png:
            p = out_dir / f"{name}_t{s:05.2f}.png"
            r.png(min(int(s * FPS), tl["n_frames"] - 1), str(p))
            print("  ", p)
        return

    print(f"[2/3] A desenhar {tl['n_frames']} frames com {a.workers} processos e a codificar")
    mp4 = Path(a.saida) if a.saida else out_dir / f"{name}.mp4"
    encode(tl, wav, mp4, a.workers)
    wav.unlink(missing_ok=True)
    print(f"[3/3] Pronto: {mp4}")


if __name__ == "__main__":
    main()

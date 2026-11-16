#!/usr/bin/env python3
"""Gerador de Reels do Tiko (994-Caxinas).

Uso:
    python scripts/render.py episodios/episodio_01.json              # -> output/episodio_01.mp4
    python scripts/render.py episodios/episodio_01.json --png 2.5 8  # só frames de teste (segundos)

Pipeline: guião -> edge-tts (por bloco) -> timestamps por palavra -> lip-sync por amplitude
          -> frames vetoriais (pycairo, em paralelo) -> ffmpeg (H.264 + AAC).
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

from audio import SR, decode, ffmpeg_exe, mouth_tracks, trim_silence, write_wav  # noqa: E402
from config import FPS, H, W  # noqa: E402
from subtitles import make_chunks  # noqa: E402
from tts import parse_markup, spoken_tokens, synthesize, syllables  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VOICE = {"nome": "pt-PT-DuarteNeural", "velocidade": "+5%", "tom": "+4Hz", "volume": "+0%"}


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
        a0, a1 = 0.05, max(dur - 0.05, 0.1)
        for w, s, e in zip(words, edges[:-1], edges[1:]):
            w["t0"], w["t1"] = a0 + (a1 - a0) * s, a0 + (a1 - a0) * e
        method = "estimado"
    last = 0.0
    for w in words:                                    # garantir monotonia
        w["t0"] = max(w["t0"], last)
        w["t1"] = max(w["t1"], w["t0"] + 0.08)
        last = w["t0"]
    return method


def norm_props(v):
    if v is None:
        return []
    return [v] if isinstance(v, str) else list(v)


def build_timeline(script_path, hat=None):
    cfg = json.loads(Path(script_path).read_text(encoding="utf-8"))
    voz = {**DEFAULT_VOICE, **cfg.get("voz", {})}
    pron = cfg.get("pronuncia", {})
    gap = float(cfg.get("pausa_entre_blocos", 0.2))
    lead = 0.35
    raw_blocks = list(cfg["blocos"])
    outro_cfg = cfg.get("outro", {})
    outro_dur = float(outro_cfg.get("duracao", 2.5))
    if outro_cfg.get("fala"):
        raw_blocks.append({"texto": outro_cfg["fala"], "estado": "saudacao", "outro": True,
                           "ilustracao": ["35"]})

    blocks, parts, t = [], [], lead
    for i, rb in enumerate(raw_blocks):
        words = parse_markup(rb["texto"])
        spoken = " ".join(spoken_tokens(w["text"], pron) for w in words)
        mp3, wb = synthesize(spoken, voz["nome"], rb.get("velocidade", voz["velocidade"]),
                             rb.get("tom", voz["tom"]), voz["volume"])
        x, off = trim_silence(decode(mp3))
        dur = len(x) / SR
        method = assign_words(words, pron, wb, dur, off, rb["texto"][:30])
        is_outro = bool(rb.get("outro"))
        if is_outro:
            t += float(outro_cfg.get("pausa_antes", 0.25))
        start = t + (0.15 if is_outro else 0.0)
        for w in words:
            w["t0"] += start
            w["t1"] += start
        parts.append((start, x))
        blocks.append({
            "texto": rb["texto"], "estado": rb.get("estado", "normal"), "outro": is_outro,
            "props": norm_props(rb.get("ilustracao")), "start": start, "end": start + dur,
            "words": words, "chunks": make_chunks(words), "method": method,
        })
        t = start + dur + float(rb.get("pausa_depois", gap))
    last_end = blocks[-1]["end"]
    if outro_cfg.get("fala"):
        ob = blocks[-1]
        o0 = ob["start"] - 0.15
        total = max(o0 + outro_dur, ob["end"] + 0.35)
        if total > o0 + outro_dur + 1e-6:
            print(f"  ! a fala do outro excede {outro_dur}s; outro estendido para {total - o0:.2f}s", file=sys.stderr)
    else:
        blocks.append({"texto": "", "estado": "saudacao", "outro": True, "props": ["35"], "start": last_end + 0.25,
                       "end": last_end + 0.25, "words": [], "chunks": [], "method": "-"})
        o0 = blocks[-1]["start"]
        total = o0 + outro_dur

    # tempos visuais (emoção/cenário mudam a meio da pausa entre blocos) + «appear» dos ícones
    for i, b in enumerate(blocks):
        b["vstart"] = 0.0 if i == 0 else (b["start"] - gap / 2 if not b["outro"] else o0)
    for i, b in enumerate(blocks):
        b["vend"] = blocks[i + 1]["vstart"] if i + 1 < len(blocks) else total
        prev = blocks[i - 1] if i else None
        ap = []
        for j, name in enumerate(b["props"]):
            if prev and name in prev["props"]:
                ap.append(prev["appear"][prev["props"].index(name)])
            else:
                ap.append(b["vstart"] + 0.12 + 0.14 * j)
        b["appear"] = ap

    n_frames = int(math.ceil(total * FPS))
    full = np.zeros(int(math.ceil(total * SR)) + SR // 2, dtype=np.float32)
    for start, x in parts:
        a = int(start * SR)
        full[a:a + len(x)] += x
    mo, mw = mouth_tracks(full, FPS, n_frames)
    return {
        "fps": FPS, "total": total, "n_frames": n_frames, "blocks": blocks, "mouth_o": mo, "mouth_w": mw,
        "watermark": cfg.get("marca_dagua", "@994caxinas | 35 Anos"),
        "chapeu": cfg.get("personagem", {}).get("chapeu", True) if hat is None else hat,
        "nome": cfg.get("personagem", {}).get("nome", "Tiko"), "titulo": cfg.get("titulo", ""),
    }, full


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
    ctx = mp.get_context("spawn" if sys.platform != "linux" else "fork")
    with ctx.Pool(workers, initializer=_init, initargs=(tl,)) as pool:
        for i, buf in enumerate(pool.imap(_frame, range(tl["n_frames"]), chunksize=2)):
            ff.stdin.write(buf)
            if i % 60 == 0 or i == tl["n_frames"] - 1:
                el = time.time() - t0
                print(f"\r  frame {i + 1}/{tl['n_frames']}  ({el:.0f}s)", end="", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg falhou")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("guiao", help="ficheiro JSON do episódio")
    ap.add_argument("-o", "--saida", help="MP4 de saída (por omissão output/<nome>.mp4)")
    ap.add_argument("--png", nargs="+", type=float, metavar="SEG", help="só gera PNGs de teste nesses instantes")
    ap.add_argument("--sem-chapeu", action="store_true")
    ap.add_argument("-j", "--workers", type=int, default=max(1, (mp.cpu_count() or 2)))
    a = ap.parse_args()

    name = Path(a.guiao).stem
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    print(f"[1/3] Voz e timestamps ({name})")
    tl, full = build_timeline(a.guiao, hat=False if a.sem_chapeu else None)
    for b in tl["blocks"]:
        print(f"  {b['start']:5.2f}–{b['end']:5.2f}s  {b['estado']:<13} [{b['method']}] {b['texto'][:60]}")
    print(f"  duração total: {tl['total']:.2f}s ({tl['n_frames']} frames @ {FPS} fps)")

    wav = out_dir / f"{name}.wav"
    write_wav(str(wav), full[: int(tl["total"] * SR)])
    mp3 = out_dir / f"{name}.mp3"
    subprocess.run([ffmpeg_exe(), "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-q:a", "2", str(mp3)], check=True)
    (out_dir / f"{name}.timings.json").write_text(json.dumps({
        "titulo": tl["titulo"], "duracao": tl["total"],
        "blocos": [{"texto": b["texto"], "estado": b["estado"], "inicio": round(b["start"], 3), "fim": round(b["end"], 3),
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

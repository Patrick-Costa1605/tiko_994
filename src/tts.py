"""Síntese de voz pt-PT com edge-tts + timestamps por palavra."""
import asyncio
import hashlib
import json
import os
import re
from pathlib import Path

import edge_tts

CACHE = Path(__file__).resolve().parent.parent / "assets" / "audio_cache"
PUNCT = ".,;:!?…\"'()[]«»—–-"


def _proxy():
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None


async def _synth(text, voice, rate, pitch, volume, mp3_path):
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume,
                               proxy=_proxy(), boundary="WordBoundary")
    words = []
    with open(mp3_path, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"text": ch["text"], "t0": ch["offset"] / 1e7,
                              "t1": (ch["offset"] + ch["duration"]) / 1e7})
    return words


def synthesize(text, voice, rate, pitch, volume="+0%"):
    """Devolve (caminho_mp3, palavras[{text,t0,t1}]). Usa cache em assets/audio_cache."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(json.dumps([text, voice, rate, pitch, volume]).encode()).hexdigest()[:16]
    mp3, meta = CACHE / f"{key}.mp3", CACHE / f"{key}.json"
    if mp3.exists() and meta.exists() and mp3.stat().st_size > 0:
        return str(mp3), json.loads(meta.read_text())
    last = None
    for attempt in range(4):
        try:
            words = asyncio.run(_synth(text, voice, rate, pitch, volume, mp3))
            if mp3.stat().st_size == 0:
                raise RuntimeError("áudio vazio")
            meta.write_text(json.dumps(words))
            return str(mp3), words
        except Exception as e:  # rede instável
            last = e
            asyncio.run(asyncio.sleep(1.5 * (attempt + 1)))
    raise SystemExit(f"Falha no edge-tts após 4 tentativas: {last}\n"
                     "Precisas de acesso a speech.platform.bing.com (e de HTTPS_PROXY se estiveres atrás de proxy).")


# ---------------------------------------------------------------- texto do guião
_MARK = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*")


def parse_markup(text):
    """'Olá *Caxinas*! **Sempre** Alerta' -> lista de palavras [{text, style}] (style: None|'y'|'g').

    *x* = destaque amarelo, **x** = destaque verde. Pontuação colada fica na mesma palavra.
    """
    chars, pos = [], 0
    for m in _MARK.finditer(text):
        chars += [(c, None) for c in text[pos:m.start()]]
        inner, style = (m.group(1), "g") if m.group(1) is not None else (m.group(2), "y")
        chars += [(c, style) for c in inner]
        pos = m.end()
    chars += [(c, None) for c in text[pos:]]

    words, cur = [], []
    for c, st in chars + [(" ", None)]:
        if c.isspace():
            if cur:
                styles = [s for ch, s in cur if ch.isalnum() and s]
                words.append({"text": "".join(ch for ch, _ in cur), "style": styles[0] if styles else None})
                cur = []
        else:
            cur.append((c, st))
    return words


def spoken_tokens(word_text, pron):
    """Texto falado de uma palavra do ecrã (aplica o dicionário `pronuncia`)."""
    core = word_text.strip(PUNCT)
    if core in pron:
        return word_text.replace(core, pron[core])
    return word_text


def syllables(s):
    n = len(re.findall(r"[aeiouáéíóúâêôãõàüy]+", s.lower()))
    n += 2 * len(re.findall(r"\d", s))
    return max(1, n)


_BREAK = re.compile(r'<break\s+time="(\d+)(ms|s)"\s*/?>', re.I)


def split_pauses(text):
    """'Olá!<break time="250ms"/> Tudo bem?' -> [('Olá!', 0.25), ('Tudo bem?', 0.0)].

    O edge-tts não interpreta SSML, por isso cada pedaço é sintetizado em separado e o
    silêncio é inserido pelo gerador (pausas cómicas exatas e sem depender do serviço).
    """
    parts, pos = [], 0
    for m in _BREAK.finditer(text):
        seg = text[pos:m.start()].strip()
        pause = int(m.group(1)) / (1000 if m.group(2).lower() == "ms" else 1)
        if seg:
            parts.append([seg, pause])
        elif parts:
            parts[-1][1] += pause
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        parts.append([tail, 0.0])
    return [tuple(p) for p in parts]

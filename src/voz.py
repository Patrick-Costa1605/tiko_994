"""Voz pt-PT (edge-tts) com timestamps por palavra; cache em assets/audio_cache."""
import asyncio
import hashlib
import json
import os
import re
import unicodedata

import edge_tts

from config import ROOT

CACHE = ROOT / "assets" / "audio_cache"
PUNCT = ".,;:!?…\"'()[]«»—–"


def sintetizar(texto, voz, rate, pitch):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(json.dumps([texto, voz, rate, pitch]).encode()).hexdigest()[:16]
    mp3, meta = CACHE / f"{key}.mp3", CACHE / f"{key}.json"
    if mp3.exists() and meta.exists() and mp3.stat().st_size:
        return str(mp3), json.loads(meta.read_text())
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

    async def run():
        com = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch, proxy=proxy, boundary="WordBoundary")
        pal = []
        with open(mp3, "wb") as f:
            async for ch in com.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    pal.append({"text": ch["text"], "t0": ch["offset"] / 1e7, "t1": (ch["offset"] + ch["duration"]) / 1e7})
        return pal

    ult = None
    for k in range(4):
        try:
            pal = asyncio.run(run())
            if mp3.stat().st_size == 0:
                raise RuntimeError("áudio vazio")
            meta.write_text(json.dumps(pal))
            return str(mp3), pal
        except Exception as e:
            ult = e
            asyncio.run(asyncio.sleep(1.5 * (k + 1)))
    raise SystemExit(f"edge-tts falhou: {ult}\nPrecisa de acesso a speech.platform.bing.com (e de HTTPS_PROXY atrás de proxy).")


def falado(palavra, pron):
    core = palavra.strip(PUNCT)
    return palavra.replace(core, pron[core]) if core in pron else palavra


def silabas(s):
    return max(1, len(re.findall(r"[aeiouáéíóúâêôãõàüy]+", s.lower())))


def norm(s):
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode().strip(PUNCT.replace("-", ""))

#!/usr/bin/env python3
"""Transcreve a gravação com tempos por palavra (faster-whisper) para assets/gravacao/palavras.json.
Só é preciso correr quando a gravação muda; o render usa o resultado em cache.

    pip install faster-whisper
    python src/transcrever.py [ini fim]      # ini/fim em segundos: parte da gravação que é fala (o resto é conversa de fundo)
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "assets" / "gravacao" / "voz_original.mp4"
INI, FIM = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (2.4, 57.6)
PROMPT = ("Agrupamento 994 das Caxinas. Monsenhor Domingos de Araújo. Chefe Miguel, chefe Milton, chefe Albertino. "
          "Lobitos, Exploradores, Pioneiros e Caminheiros.")

x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(AUDIO), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                                 capture_output=True, check=True).stdout, dtype="float32")
modelo = WhisperModel("medium", device="cpu", compute_type="int8")
segs, _ = modelo.transcribe(x[int(INI * 16000):int(FIM * 16000)], language="pt", word_timestamps=True, beam_size=5,
                            condition_on_previous_text=False, temperature=0.0, initial_prompt=PROMPT)
pal = [{"w": w.word.strip(), "t0": round(w.start + INI, 3), "t1": round(w.end + INI, 3), "p": round(w.probability, 2)}
       for s in segs for w in s.words]
(ROOT / "assets" / "gravacao" / "palavras.json").write_text(
    json.dumps({"fonte": AUDIO.name, "modelo": "faster-whisper medium", "palavras": pal}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(pal), "palavras")

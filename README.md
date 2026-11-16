# Tiko · Reels do 994 Caxinas

Gerador de vídeos verticais (1080×1920, **60 fps**) com o Tiko, mascote do Agrupamento 994 – Caxinas.
Stack: **Python** — `edge-tts` (voz pt-PT), `pycairo` (vetor), `numpy` (lip-sync/áudio), `ffmpeg`.

## Instalar e renderizar
```bash
pip install -r requirements.txt        # pycairo pode precisar de libcairo (Linux: libcairo2-dev; macOS: brew install cairo pkg-config)
python src/palette.py                  # (opcional) volta a extrair a paleta de assets/logo-994.png
python src/render.py guioes/ep01_apresentacao.json            # -> output/ep01_apresentacao.mp4 (+ .mp3, .timings.json)
python src/render.py guioes/ep01_apresentacao.json --png 2 9  # só imagens de teste (segundos)
```
Fonte: **Inter** instalada no sistema. A voz fica em cache (`assets/audio_cache/`). Atrás de proxy usa-se `HTTPS_PROXY`.

## Guião (`guioes/*.json`)
| campo | descrição |
|---|---|
| `voz` | `nome`, `velocidade` (`+14%`), `tom` (`+3Hz`) |
| `pronuncia` | texto *falado* diferente do escrito (`"994": "nove nove quatro"`) |
| `final_extra` | segundos de «respiração» no fim (logótipo a brilhar) |
| `blocos[].texto` | `*amarelo*` e `**verde**` = palavras-chave; `<break time="250ms"/>` = pausa cómica exata |
| `blocos[].estado` | `normal` · `entusiasmado` · `confuso` · `assustado` · `saudacao` · `orgulhoso` (ajeita o lenço) |
| `blocos[].ilustracao` | `tenda`, `tenda_caida`, `fogueira`, `corda`/`no`, `mochila`, `seta`, `lenco`, `estrela(s)`, `exclamacao`, `bussola`, `pinheiro`, `logo`, `texto:ABC`; `nome@1.3` = 30% maior |
| `blocos[].lado` | onde fica o Tiko: `centro` (sem ilustrações), `esquerda`, `direita` — desliza suavemente |
| `blocos[].camara` | `normal` · `punch` (micro-zoom a ~112%) · `aperto` · `lento` (zoom contínuo) |
| `blocos[].punches` | segundos (relativos ao bloco) de punch-ins extra, ex. para piadas |
| `blocos[].sfx` | efeitos extra: `{"tipo":"ding","em":3.9}` (`pop`, `whoosh`, `ding`, `boing`, `tick`) |

## Código (`src/`)
`render.py` pipeline · `tts.py` voz+pausas · `audio.py` lip-sync (amplitude + centroide espectral → 5 bocas) e SFX procedurais ·
`character.py` Tiko (IK, squash & stretch, lenço com física) · `props.py` ilustrações/VFX · `background.py` fundo e parallax ·
`subtitles.py` legendas · `scene.py` câmara e composição · `palette.py` cores do logótipo.
O lenço usa verde com debrum amarelo do logótipo (`SCARF`/`TRIM` em `src/config.py`).

# Tiko · Reels 994-Caxinas (#35AnosDeExemplo)

Gerador de vídeos verticais (1080×1920, 30 fps) com o Tiko, boneco de pauzinhos com lenço escutista.
Stack: **Python** — `edge-tts` (voz pt-PT), `pycairo` (vetor), `numpy` (lip-sync), `ffmpeg`.

## Instalar
```bash
pip install -r requirements.txt     # pycairo pode precisar de libcairo (Linux: libcairo2-dev; macOS: brew install cairo pkg-config)
```
Fonte usada: **Inter** (instalar no sistema; sem ela o cairo usa uma sans-serif genérica).

## Renderizar
```bash
python scripts/render.py episodios/episodio_01.json            # -> output/episodio_01.mp4 (+ .mp3 e .timings.json)
python scripts/render.py episodios/episodio_01.json --png 2 9  # só imagens de teste nos segundos 2 e 9
```
A voz fica em cache (`assets/audio_cache/`), por isso ajustar visuais não volta a chamar o serviço de TTS.
Atrás de proxy, o `HTTPS_PROXY` é usado automaticamente.

## Guião (`episodios/*.json`)
| campo | descrição |
|---|---|
| `voz` | `nome`, `velocidade` (`+5%`), `tom` (`+4Hz`) |
| `pronuncia` | substitui o texto *falado* (`"994": "nove nove quatro"`) sem mudar a legenda |
| `blocos[].texto` | `*amarelo*`, `**verde**` marcam palavras-chave nas legendas |
| `blocos[].estado` | `normal` · `entusiasmado` · `confuso` · `assustado` · `saudacao` |
| `blocos[].ilustracao` | lista de ícones para o quadro: `tenda`, `tenda_caida`, `fogueira`, `corda`, `mochila`, `seta`, `lenco`, `estrela`, `bussola`, `35`, `pinheiro`, `texto:QUALQUER COISA` |
| `outro.fala` | fala do cartão final (2.5 s; estende se a fala não couber) |

## Código
- `scripts/tts.py` voz + timestamps por palavra · `audio.py` envelope/lip-sync
- `scripts/character.py` Tiko e poses (acrescentar emoção = nova entrada em `POSES`)
- `scripts/props.py` ícones do quadro · `subtitles.py` legendas · `scene.py` composição · `render.py` pipeline

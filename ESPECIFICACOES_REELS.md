# Especificações Obrigatórias de Exportação de Vídeo (Instagram Reels)

Sempre que criares, renderizares ou exportares um vídeo gráfico/animado neste projeto, segue rigorosamente estas especificações técnicas para evitar perda de qualidade, desfocagem ou compressão agressiva no Instagram Reels.

---

## 1. Formato e Resolução
- **Proporção (Aspect Ratio):** `9:16` (vertical)
- **Resolução exata:** `1080 x 1920 px` (Full HD vertical)
- **Proibido:** Não renderizar em 4K (`2160 x 3840`), 720p (`720 x 1280`) ou formatos horizontais/quadrados com barras pretas automáticas. O ficheiro deve nascer em `1080 x 1920 px`.

---

## 2. Parâmetros de Codificação (FFmpeg / Remotion / Canvas)
- **Contentor:** `.mp4`
- **Codec de Vídeo:** `H.264` (`libx264`)
- **Perfil H.264:** `High` (`-profile:v high -level 4.1`)
- **Espaço de Cor / Pixel Format:** `yuv420p` (garante compatibilidade total com iOS, Android e Instagram sem alteração de cores)
- **Taxa de Fotogramas (FPS):** `30 fps` constantes (`CFR` — Constant Frame Rate)
- **Taxa de Bits (Bitrate):** Entre `10 Mbps` e `12 Mbps` (`-b:v 10M -maxrate 12M -bufsize 20M`) ou `-crf 17` com limite de bitrate de `12 Mbps`
- **Codec de Áudio (se aplicável):** `AAC`, `48 kHz`, `128 kbps` ou `192 kbps` stereo

### Comando FFmpeg de Referência
Caso uses `ffmpeg` para codificar ou converter o vídeo final, aplica esta configuração:

```bash
ffmpeg -i input.mp4 -vf "scale=1080:1920:flags=lanczos,fps=30" -c:v libx264 -profile:v high -level 4.1 -pix_fmt yuv420p -crf 17 -maxrate 12M -bufsize 20M -movflags +faststart -c:a aac -b:a 192k -ar 48000 output_reels.mp4
```

---

## 3. Regras de Design Gráfico e Tipografia (Anti-Compressão)
O algoritmo do Instagram degrada linhas muito finas e degradês suaves. Ao desenhar elementos visuais no código:

- **Espessura mínima de texto:** Evita fontes `Thin` (100) ou `Light` (300). Usa pesos a partir de `Regular` (400) ou `Medium` (500), com tamanho mínimo de `36px` para corpo de texto e `64px+` para títulos.
- **Espessura mínima de linhas e vetores:** Traços (`stroke-width`) devem ter no mínimo `3px` a `4px`.
- **Contraste e Cores:** Prioriza cores sólidas e alto contraste entre texto e fundo. Evita degradês muito subtis de uma mesma cor (causam *color banding* após o upload). Se usares degradês, adiciona um ruído/grão muito leve (`1%` a `2%` de opacidade) para evitar manchas de compressão.
- **Anti-aliasing e Nitidez:** Renderiza gráficos vetoriais e texto na escala nativa (`1080x1920` ou `deviceScaleFactor: 2` reduzido com filtro `lanczos`), nunca esticando imagens de baixa resolução.

---

## 4. Zonas Seguras (Safe Zones do Reels)
Mantém todos os textos, logótipos e elementos gráficos principais dentro da área visível para não serem tapados pela interface do Instagram:

- **Margem Superior:** Mínimo `220 px` livres
- **Margem Inferior:** Mínimo `420 px` livres (onde ficam a legenda, nome de utilizador e áudio)
- **Margem Lateral Esquerda:** Mínimo `60 px` livres
- **Margem Lateral Direita:** Mínimo `140 px` livres (onde ficam os botões de gosto, comentário e partilha)

---

## 5. Checklist Antes de Entregar o Ficheiro
Antes de disponibilizares o `.mp4` para download, confirma que:
1. O ficheiro tem exatamente `1080 x 1920` pixels.
2. O frame rate é `30 fps` constantes.
3. O pixel format é `yuv420p` em `H.264`.
4. Nenhum texto importante invade as margens de segurança.

---

## Como este projeto cumpre e verifica isto
- `src/config.py` define `SAFE = (60, 220, 940, 1500)`; as páginas são desenhadas em 1080×1330 e escaladas para a zona segura; as legendas e a marca d'água ficam lá dentro.
- `src/render.py` codifica com `-profile:v high -level 4.1 -pix_fmt yuv420p -crf 17 -maxrate 12M -bufsize 20M -r 30 -fps_mode cfr`, áudio AAC 48 kHz estéreo 192 kbps.
- **`python src/verificar.py guioes/<ep>.json output/<ep>.mp4`** mede os limites de cada traço, texto, legenda e marca d'água, o texto mínimo (36 px), o traço mínimo (3 px) e as características do ficheiro. Corre-o sempre antes de entregar.
- O braço da mão que desenha é decorativo e pode atravessar a margem direita; nenhum conteúdo importante o faz.

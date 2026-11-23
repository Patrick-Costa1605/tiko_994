# Como surgiu o Escutismo nas Caxinas — vídeo desenhado à mão em tempo real

Um Reel (1080×1920, 30 fps, ~52 s) em que uma mão desenha, com marcador sobre papel, a história do Agrupamento 994 – Caxinas,
ao ritmo da voz (pt-PT). Tudo é gerado por código: os traços, a mão, as legendas e o som do marcador.

```bash
pip install -r requirements.txt
python src/render.py guioes/como_surgiu.json              # -> output/como_surgiu.mp4 (+ .legenda.txt)
python src/render.py guioes/como_surgiu.json --png 6 20   # só imagens de teste (segundos)
```
Voz: a **gravação real** em `assets/gravacao/voz_original.mp4` (o guião tem o bloco `"gravacao"`). Sem esse bloco, usa-se `edge-tts` (`pt-PT-DuarteNeural`).
Fonte: Chewy (em `assets/fonts/`; instala-a no sistema).

## Voz gravada
- `python src/transcrever.py [ini fim]` (precisa de `faster-whisper`) gera `assets/gravacao/palavras.json` com o tempo de cada palavra; só é preciso se a gravação mudar. `ini`/`fim` = parte que é fala (a conversa antes/depois da leitura fica de fora).
- `src/gravacao.py` alinha o texto do guião (tem de ser o que a pessoa diz) a essas palavras, corta um troço por bloco no ponto mais silencioso da pausa e deixa as pausas entre páginas ao render.
- Tratamento (`audio.tratar_gravacao`): repara picos cortados, tira graves e «caixa», dá presença, doma os «ss», comprime e nivela; mistura final a -15 LUFS (pico -1,5 dB).

## Especificações do Reels
Ver [`ESPECIFICACOES_REELS.md`](ESPECIFICACOES_REELS.md) (zonas seguras, codificação, tipografia). `python src/verificar.py guioes/como_surgiu.json output/como_surgiu.mp4` confirma tudo.

## Ritmo e som
- **Abertura:** uma pergunta enorme («Como nasce um agrupamento de escuteiros, numa terra de pescadores?») com o «?» a vermelho e marcador amarelo.
- **Páginas:** cada página fica parada ~1,2 s depois da fala e o caderno desliza em 0,85 s (`SLIDE`, `GAP_PAG` em `src/render.py`).
- **Voz:** uma síntese por frase (entoação mais natural) com pausas, mais calma (-2%), e um tratamento leve (graves, compressão, sala curta).
- **Música:** original, gerada por `src/musica.py` (ukulele em Dó maior, baixo, almofada e shaker); baixa sozinha sob a voz.
- **Lápis e página:** quase impercetíveis (~25 dB e ~14 dB abaixo da voz); a mistura é normalizada de forma linear.

## Como funciona
- `guioes/como_surgiu.json`: os blocos de fala (texto + `cena`). `pronuncia` diz como ler números (1991 → «mil novecentos e noventa e um»).
  `continua: true` mantém a mesma página; sem isso o caderno desliza para uma página nova.
- `src/cenas.py`: cada página é uma lista de traços pela ordem em que a mão os desenha. `ancora="palavra"` faz o elemento começar quando a voz diz essa palavra.
- `src/desenho.py`: traço com tremor que «ferve» a 10 fps, preenchimento tipo marcador (ligeiramente desalinhado), texto que se escreve, boneco de pauzinhos, a mão.
- `src/render.py`: junta voz, tempos por palavra, desenho (4 processos em paralelo) e ffmpeg; o som do marcador a riscar e o virar da página são gerados em código.

## Factos usados (só o que está confirmado)
- **CNE (escutismo.pt, História):** o Escutismo foi fundado em 1907, em Inglaterra, por Baden-Powell; o CNE nasceu em Braga a 27 de maio de 1923.
- **Site do 994 (994caxinas.com):** fundado em 1991 por iniciativa do Monsenhor Domingos de Araújo; Chefes de Agrupamento: Miguel Fernandes de Castro (1991–2013),
  Milton Fernandes de Castro (2013–2022; dirigente fundador e o único ainda no ativo), Albertino Arteiro (desde 2022; escuteiro desde 1998);
  4 secções (6–22 anos); mais de 100 jovens formados; missão «substituir o egoísmo pelo serviço».
- **Não confirmado, por isso não está no vídeo:** como a ideia surgiu em Caxinas (primeiras reuniões, primeiro acampamento, quem foram os primeiros jovens).

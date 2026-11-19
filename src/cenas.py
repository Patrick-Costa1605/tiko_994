"""As páginas do caderno: cada função devolve os elementos pela ordem em que a mão os desenha.
`ancora="palavra"` faz o elemento começar quando a voz diz essa palavra.

Factos só os verificados (994caxinas.com, escutismo.pt, fontes públicas sobre a igreja das Caxinas);
a decoração (pescador de oleado, gotas de suor, bonecos das secções) é humor visual e não afirma factos."""
import math

from config import *
from desenho import *

L = AREA[1]          # topo da zona de desenho
CREME = hx("#EADFC8")


def chapeu(cx, cy, s, seed):
    """Chapéu escutista de abas largas (as abas em (cx, cy))."""
    copa = catmull([(cx - 62 * s, cy - 4 * s), (cx - 54 * s, cy - 58 * s), (cx, cy - 78 * s), (cx + 54 * s, cy - 58 * s), (cx + 62 * s, cy - 4 * s)])
    return [caminho(elipse(cx, cy, 100 * s, 24 * s), INK, 8, fill=CASTANHO, fa=0.9, fechado=True, seed=seed, peso=0.9),
            caminho(copa + [(cx - 62 * s, cy - 4 * s)], INK, 8, fill=CASTANHO, fa=0.9, fechado=True, seed=seed + 1, peso=0.8),
            caminho([(cx - 58 * s, cy - 22 * s), (cx, cy - 12 * s), (cx + 58 * s, cy - 22 * s)], VERDE, 12, seed=seed + 2, peso=0.4)]


# ------------------------------------------------------------------ 1. abertura
def gancho():
    """Um pescador de oleado amarelo pesca… um chapéu e um lenço escutistas. A pergunta responde-se com o desenho."""
    fx, fy, s = 230, 905, 1.25
    E = pessoa(fx, fy, s, lenco=hx("#D9A441"), braco="dir", seed=200)
    E.append(caminho([(fx - 26, fy - 226), (fx + 26, fy - 226), (fx + 42, fy - 120), (fx - 42, fy - 120)], INK, 8, fill=AMARELO, fa=0.95, fechado=True, seed=210, peso=0.6))
    E.append(caminho(elipse(fx, fy - 322, 58, 13), INK, 8, fill=AMARELO, fa=0.95, fechado=True, seed=211, peso=0.5))
    E.append(caminho(onda(400, 1040, 905, 12, 150, 0.5), AGUA, 9, seed=212, peso=0.7))
    E.append(caminho([(fx + 72, fy - 272), (610, 420)], CASTANHO, 9, seed=213, peso=0.7))          # cana
    E.append(caminho([(610, 420), (610, 706)], INK, 5, seed=214, peso=0.5))                         # linha
    E.append(caminho(catmull([(610, 706), (610, 726), (630, 734), (640, 716)]), INK, 7, seed=215, peso=0.3))
    E += chapeu(610, 790, 0.8, 216)
    E.append(caminho([(576, 822), (644, 822), (610, 884), (576, 822)], INK, 7, fill=VERDE, fa=1, fechado=True, seed=220, peso=0.5))   # lenço
    E.append(texto("?", fx + 10, 520, 170, VERMELHO, peso=1.0))
    E.append(caminho([(130, 1060), (950, 1046)], AMARELO, 118, seed=202, peso=0.7, ancora="agrupamento", tremor=1.0))
    E.append(texto("ESCUTEIROS", 540, 1104, 150, VERDE, peso=1.2, ancora="agrupamento"))
    E.append(texto("numa terra de", 540, 1214, 84, INK, peso=0.9, ancora="numa"))
    E.append(caminho([(200, 1340), (890, 1326)], AMARELO, 118, seed=203, peso=0.7, ancora="pescadores", tremor=1.0))
    E.append(texto("PESCADORES", 540, 1392, 150, AZUL, peso=1.2, ancora="pescadores"))
    return E


# ------------------------------------------------------------------ 2. Caxinas
def caxinas():
    E = [texto("CAXINAS", 540, 350, 200, VERDE, peso=1.2),
         texto("Vila do Conde", 540, 440, 64, INK, peso=0.8)]
    # mar
    for i, (y, amp, wl, fase) in enumerate(((1000, 12, 170, 0.0), (1075, 14, 200, 1.7), (1150, 12, 160, 3.1), (1225, 14, 210, 0.8))):
        E.append(caminho(onda(70, 1010, y, amp, wl, fase), AGUA, 9, seed=30 + i, ancora="mar" if i == 0 else None, peso=0.9))
    # a igreja em forma de barco, a navegar nas ondas
    casco = bez((220, 900), (240, 1010), (330, 1050), (470, 1052)) + bez((470, 1052), (640, 1056), (790, 1040), (860, 900))
    E.append(caminho(casco + [(220, 900)], INK, 10, fill=CREME, fa=1, fechado=True, seed=50, peso=1.6, ancora="igreja"))
    E.append(caminho([(400, 900), (400, 760), (690, 650), (690, 900)], INK, 10, fill=VERMELHO, fa=0.9, fechado=True, seed=51, peso=1.2))
    E.append(caminho([(690, 650), (690, 560)], INK, 10, seed=52, peso=0.4))
    E.append(caminho([(655, 598), (725, 598)], INK, 10, seed=53, peso=0.3))
    E.append(caminho(catmull([(500, 900), (500, 850), (545, 820), (590, 850), (590, 900)]), INK, 8, fill=CASTANHO, fa=0.85, seed=54, peso=0.5))
    # sol sorridente
    E.append(caminho(circulo(880, 640, 80, 1), INK, 8, fill=AMARELO, fa=0.95, fechado=True, seed=1))
    for k in range(10):
        a = k * 2 * math.pi / 10
        E.append(caminho([(880 + math.cos(a) * 108, 640 + math.sin(a) * 108), (880 + math.cos(a) * 146, 640 + math.sin(a) * 146)], INK, 7, seed=20 + k, peso=0.3))
    E.append(caminho(circulo(855, 625, 6, 2), INK, 6, fill=INK, fa=1, fechado=True, seed=2, peso=0.2))
    E.append(caminho(circulo(905, 625, 6, 3), INK, 6, fill=INK, fa=1, fechado=True, seed=3, peso=0.2))
    E.append(caminho(elipse(880, 645, 34, 24, a0=0.2, a1=math.pi - 0.2), INK, 6, seed=4, peso=0.3))
    return E


# ------------------------------------------------------------------ 3. a viagem: 1907 → 1923 → 1991 (um só mapa)
def viagem():
    def pj(lon, lat):
        return (120 + (lon + 9.6) * 165, 210 + (42.15 - lat) * 190)
    costa = [(-8.87, 41.87), (-8.84, 41.70), (-8.78, 41.45), (-8.72, 41.20), (-8.68, 41.00), (-8.65, 40.70), (-8.75, 40.45), (-8.88, 40.15), (-8.96, 39.90),
             (-9.05, 39.62), (-9.30, 39.42), (-9.38, 39.34), (-9.42, 39.0), (-9.50, 38.78), (-9.25, 38.68), (-9.12, 38.50), (-8.90, 38.50), (-8.78, 38.20),
             (-8.80, 37.90), (-8.80, 37.45), (-8.97, 37.05), (-8.65, 37.08), (-8.30, 37.09), (-7.90, 37.00), (-7.45, 37.18),
             (-7.42, 37.50), (-7.52, 37.90), (-7.28, 38.20), (-7.06, 38.55), (-7.16, 38.90), (-7.30, 39.28), (-7.45, 39.66), (-7.05, 39.75),
             (-7.00, 40.00), (-6.85, 40.28), (-6.82, 40.60), (-6.95, 41.00), (-6.55, 41.30), (-6.22, 41.58), (-6.55, 41.86), (-7.05, 41.93),
             (-7.45, 41.80), (-7.90, 41.88), (-8.20, 41.95), (-8.65, 42.04)]
    E = [caminho(catmull([pj(*p) for p in costa], closed=True, n=6), INK, 9, fill=hx("#DCC8A0"), fa=0.8, fechado=True, seed=70, peso=2.0, tremor=1.8)]
    # 1907: o chapéu de Baden-Powell
    chap = chapeu(890, 262, 0.95, 300)
    chap[0]["ancora"] = "1907"
    E += chap
    E.append(texto("1907", 890, 420, 100, INK, peso=1.0))
    E.append(texto("Baden-Powell", 890, 490, 52, VERDE, peso=0.9, ancora="Baden-Powell"))
    # 1923: o chapéu «salta» para Braga
    bx, by = pj(-8.42, 41.55)
    E.append(caminho(catmull([(800, 214), (640, 110), (450, 160), (bx + 14, by - 30)]), VERMELHO, 8, seed=310, peso=0.9, ancora="1923"))
    E.append(caminho([(bx + 14, by - 30), (bx + 40, by - 40)], VERMELHO, 8, seed=311, peso=0.2))
    E.append(caminho([(bx + 14, by - 30), (bx + 22, by - 58)], VERMELHO, 8, seed=312, peso=0.2))
    E.append(caminho(circulo(bx, by, 17, 3), INK, 8, fill=VERMELHO, fa=1, fechado=True, seed=71, peso=0.4, ancora="Braga"))
    E.append(caminho(catmull([(bx + 24, by + 2), (520, 430), (690, 600)]), VERMELHO, 7, seed=72, peso=0.6))
    E.append(texto("Braga", 715, 618, 100, VERMELHO, align="l", peso=1.0))
    E.append(texto("1923", 715, 708, 84, INK, align="l", peso=0.8))
    # 1991: chega às Caxinas
    cx_, cy_ = pj(-8.78, 41.38)
    E.append(caminho(circulo(cx_, cy_, 16, 7), INK, 8, fill=AZUL, fa=1, fechado=True, seed=73, peso=0.4, ancora="1991"))
    E.append(caminho(catmull([(cx_ + 18, cy_ + 12), (450, 640), (690, 850)]), AZUL, 7, seed=74, peso=0.6))
    E.append(texto("Caxinas", 715, 868, 100, AZUL, align="l", peso=1.0))
    E.append(texto("1991", 715, 958, 84, INK, align="l", peso=0.8))
    # o Monsenhor rega uma semente: nasce o 994
    E.append(caminho([(720, 1110), (1050, 1100)], INK, 8, seed=90, peso=0.5, ancora="Monsenhor"))
    E.append(caminho(catmull([(880, 1105), (884, 1060), (878, 1010)]), VERDE, 9, seed=91, peso=0.4))
    E.append(caminho(catmull([(880, 1052), (830, 1030), (806, 985), (856, 1000), (880, 1040)], closed=False), INK, 7, fill=VERDE, fa=0.9, fechado=True, seed=92, peso=0.5))
    E.append(caminho(catmull([(882, 1032), (934, 1008), (958, 965), (910, 975), (882, 1018)], closed=False), INK, 7, fill=VERDE, fa=0.9, fechado=True, seed=93, peso=0.5))
    E.append(texto("Mons. Domingos", 890, 1184, 52, INK, peso=1.0, ancora="Domingos"))
    E.append(texto("de Araújo", 890, 1244, 52, INK, peso=1.0))
    E.append(texto("Agrupamento 994", 800, 1360, 62, VERDE, peso=1.2, ancora="994", sublinhado=True))
    return E


# ------------------------------------------------------------------ 4. os chefes: a estafeta do testemunho
def chefes(parte=None):
    nodes = [(330, "1991 – 2013", "Miguel", "Miguel Fernandes de Castro", "1.º Chefe de Agrupamento", VERDE),
             (770, "2013 – 2022", "Milton", "Milton Fernandes de Castro", "dirigente fundador", AZUL),
             (1210, "desde 2022", "Albertino", "Albertino Arteiro", "escuteiro desde 1998", VERMELHO)]
    E = [texto("Chefes de Agrupamento", 540, 232, 88, INK, peso=1.0),
         caminho([(150, 290), (150, 1400)], INK, 9, seed=100, peso=2.0)]
    for i, (y, anos, nome, nome_completo, papel, cor) in enumerate(nodes):
        E.append(caminho(circulo(150, y, 30, i), INK, 9, fill=cor, fa=1, fechado=True, seed=110 + i, peso=0.5))
        E.append(texto(anos, 215, y + 8, 98, cor, align="l", peso=1.1, ancora=nome))
        E.append(texto(nome_completo, 215, y + 88, 58, INK, align="l", peso=0.9))
        E.append(texto(papel, 215, y + 152, 50, CINZA, align="l", peso=0.9))
        fx, fy = 925, y + 235
        E += pessoa(fx, fy, 0.68, lenco=cor, braco="dir" if i != 1 else "cima", seed=120 + i * 20)
        hx_, hy_ = (fx + 39, fy - 148) if i != 1 else (fx + 34, fy - 177)
        E.append(caminho([(hx_, hy_), (hx_, hy_ - 78)], INK, 20, seed=130 + i, peso=0.4))                      # o testemunho
        E.append(caminho([(hx_, hy_ - 2), (hx_, hy_ - 76)], AMARELO, 12, seed=140 + i, peso=0.4))
        if i == 0:                                                                                                  # a suar
            for k, (dx, dy) in enumerate(((-48, -118), (-60, -86), (-50, -56))):
                E.append(caminho([(fx + dx, fy + dy), (fx + dx - 4, fy + dy + 16)], AGUA, 8, seed=150 + k, peso=0.2))
        if i == 2:                                                                                                  # pronto a arrancar
            for k, dy in enumerate((-110, -75, -40)):
                E.append(caminho([(fx - 52, fy + dy), (fx - 110, fy + dy)], CINZA, 7, seed=160 + k, peso=0.3))
    return E


# ------------------------------------------------------------------ 5. as quatro secções em ação
def _seccao(fx, fy, cor, nome, idades, tipo, seed):
    s = 0.9
    E = pessoa(fx, fy, s, lenco=cor, braco="baixo", seed=seed)
    E[0]["ancora"] = nome
    if tipo == "lobito":                                                    # orelhas de lobo e uivo à lua
        E.append(caminho([(fx - 28, fy - 228), (fx - 38, fy - 272), (fx - 6, fy - 238)], INK, 7, fill=CASTANHO, fa=0.9, fechado=True, seed=seed + 20, peso=0.3))
        E.append(caminho([(fx + 28, fy - 228), (fx + 38, fy - 272), (fx + 6, fy - 238)], INK, 7, fill=CASTANHO, fa=0.9, fechado=True, seed=seed + 21, peso=0.3))
        E.append(caminho(circulo(fx + 150, fy - 270, 36, seed + 22), INK, 7, fill=AMARELO, fa=0.95, fechado=True, seed=seed + 22, peso=0.4))
        E.append(texto("Auuu!", fx + 150, fy - 322, 52, CASTANHO, peso=0.8))
    elif tipo == "explorador":                                              # binóculos e um mapa
        E.append(caminho(circulo(fx - 17, fy - 207, 16, seed + 20), INK, 7, fill=CINZA, fa=1, fechado=True, seed=seed + 20, peso=0.3))
        E.append(caminho(circulo(fx + 17, fy - 207, 16, seed + 21), INK, 7, fill=CINZA, fa=1, fechado=True, seed=seed + 21, peso=0.3))
        E.append(caminho(rrect(fx + 52, fy - 175, 96, 66), INK, 7, fill=CREME, fa=1, fechado=True, seed=seed + 22, peso=0.5))
        E.append(caminho([(fx + 78, fy - 150), (fx + 122, fy - 128)], VERMELHO, 7, seed=seed + 23, peso=0.2))
        E.append(caminho([(fx + 122, fy - 150), (fx + 78, fy - 128)], VERMELHO, 7, seed=seed + 24, peso=0.2))
    elif tipo == "pioneiro":                                                # uma ponte de madeira
        E.append(caminho([(fx + 80, fy), (fx + 80, fy - 74)], INK, 9, seed=seed + 20, peso=0.3))
        E.append(caminho([(fx + 180, fy), (fx + 180, fy - 74)], INK, 9, seed=seed + 21, peso=0.3))
        E.append(caminho([(fx + 62, fy - 74), (fx + 198, fy - 74)], CASTANHO, 14, seed=seed + 22, peso=0.4))
        E.append(caminho([(fx + 80, fy), (fx + 180, fy - 74)], INK, 7, seed=seed + 23, peso=0.3))
        E.append(caminho([(fx + 180, fy), (fx + 80, fy - 74)], INK, 7, seed=seed + 24, peso=0.3))
    else:                                                                   # mochila enorme e bússola
        E.append(caminho(rrect(fx - 80, fy - 196, 58, 108, 12), INK, 8, fill=CASTANHO, fa=0.95, fechado=True, seed=seed + 20, peso=0.6))
        E.append(caminho(rrect(fx - 84, fy - 226, 66, 24, 10), INK, 7, fill=AZUL, fa=0.95, fechado=True, seed=seed + 21, peso=0.4))
        E.append(caminho(circulo(fx + 58, fy - 122, 22, seed + 22), INK, 7, fill=CREME, fa=1, fechado=True, seed=seed + 22, peso=0.4))
        E.append(caminho([(fx + 58, fy - 138), (fx + 58, fy - 106)], VERMELHO, 7, seed=seed + 23, peso=0.2))
    E.append(texto(nome, fx, fy + 80, 62, INK, peso=0.9))
    E.append(texto(idades + " anos", fx, fy + 142, 54, cor if cor != AMARELO else CASTANHO, peso=0.8))
    return E


def hoje():
    E = [texto("Quatro secções", 540, 270, 118, VERDE, peso=1.0)]
    E += _seccao(270, 680, AMARELO, "Lobitos", "6–10", "lobito", 400)
    E += _seccao(800, 680, VERDE, "Exploradores", "10–14", "explorador", 440)
    E += _seccao(270, 1120, AZUL, "Pioneiros", "14–18", "pioneiro", 480)
    E += _seccao(800, 1120, VERMELHO, "Caminheiros", "18–22", "caminheiro", 520)
    E.append(texto("a aprender e a servir", 540, 1408, 72, INK, peso=1.2, sublinhado=True, ancora="servir"))
    return E


# ------------------------------------------------------------------ 6. final: há lugar para ti
def fim():
    """Quatro bonecos de braços dados e uma cadeira vazia; a flor-de-lis desenha-se durante «escrever esta história»
    e «Sempre Alerta!» só aparece quando a voz o diz."""
    fy, s = 800, 0.8
    E = []
    cores = (AMARELO, VERDE, AZUL, VERMELHO)
    xs = (130, 330, 530, 730)
    for k, (x, cor) in enumerate(zip(xs, cores)):
        E += pessoa(x, fy, s, lenco=cor, braco="baixo", seed=600 + k * 20)
    for k, x in enumerate(xs):                                              # braços dados
        E.append(caminho([(x + 40, fy - 100), (x + 160, fy - 100)], INK if k < 3 else CINZA, 8, seed=640 + k, peso=0.3))
    g = 930                                                                 # o lugar vazio
    E.append(caminho(circulo(g, fy - 184, 27, 650), CINZA, 8, seed=650, peso=0.5, ancora="espaço"))
    E.append(caminho([(g, fy - 157), (g, fy - 76)], CINZA, 8, seed=651, peso=0.3))
    E.append(caminho([(g, fy - 76), (g - 24, fy)], CINZA, 8, seed=652, peso=0.3))
    E.append(caminho([(g, fy - 76), (g + 24, fy)], CINZA, 8, seed=653, peso=0.3))
    E.append(texto("?", g, fy - 235, 84, VERMELHO, peso=0.7))
    E.append(texto("Faltas tu?", 540, 905, 80, INK, peso=1.0, ancora="folha"))
    E += flordelis(540, 1075, 0.85, fill=VERDE, seed=160)
    E.append(texto("Sempre", 540, 300, 170, VERDE, peso=1.1, ancora="Sempre"))
    E.append(texto("Alerta!", 540, 470, 170, VERDE, peso=1.1, ancora="Alerta"))
    E.append(imagem("logo", 540, 1262, 190, peso=1.0))
    E.append(texto("@994caxinas", 540, 1432, 64, INK, peso=1.0))
    return E


CENAS = {"gancho": lambda p: gancho(), "caxinas": lambda p: caxinas(), "viagem": lambda p: viagem(), "chefes": chefes,
         "hoje": lambda p: hoje(), "fim": lambda p: fim()}

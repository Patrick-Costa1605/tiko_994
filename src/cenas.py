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
    E = [texto("1991", 540, 350, 220, INK, peso=1.2),
         texto("Caxinas · Vila do Conde", 540, 440, 58, VERDE, peso=0.9)]
    # mar
    for i, (y, amp, wl, fase) in enumerate(((1000, 12, 170, 0.0), (1075, 14, 200, 1.7), (1150, 12, 160, 3.1), (1225, 14, 210, 0.8))):
        E.append(caminho(onda(70, 1010, y, amp, wl, fase), AGUA, 9, seed=30 + i, ancora="Caxinas" if i == 0 else None, peso=0.9))
    # a igreja em forma de barco, a navegar nas ondas
    casco = bez((220, 900), (240, 1010), (330, 1050), (470, 1052)) + bez((470, 1052), (640, 1056), (790, 1040), (860, 900))
    E.append(caminho(casco + [(220, 900)], INK, 10, fill=CREME, fa=1, fechado=True, seed=50, peso=1.6, ancora="iniciativa"))
    E.append(caminho([(400, 900), (400, 760), (690, 650), (690, 900)], INK, 10, fill=VERMELHO, fa=0.9, fechado=True, seed=51, peso=1.2))
    E.append(caminho([(690, 650), (690, 560)], INK, 10, seed=52, peso=0.4))
    E.append(caminho([(655, 598), (725, 598)], INK, 10, seed=53, peso=0.3))
    E.append(caminho(catmull([(500, 900), (500, 850), (545, 820), (590, 850), (590, 900)]), INK, 8, fill=CASTANHO, fa=0.85, seed=54, peso=0.5))
    E.append(texto("Mons. Domingos de Araújo", 540, 1335, 62, INK, peso=1.1, ancora="Monsenhor"))
    E.append(texto("Agrupamento 994", 540, 1420, 78, VERDE, peso=1.2, ancora="nasceu", sublinhado=True))
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
    E.append(texto("acampar, explorar, servir", 540, 1408, 70, INK, peso=1.2, sublinhado=True, ancora="acampamentos"))
    return E


# ------------------------------------------------------------------ 5. a meta: 150 escuteiros
def _mini(x, y, k, cor, sc=1.5):
    """Boneco minúsculo (4 traços) para encher a página."""
    S = lambda v: v * sc
    return [caminho(circulo(x, y - S(62), S(15), k), INK, 6, fill=PELE, fa=1, fechado=True, seed=k, peso=0.2),
            caminho([(x - S(16), y), (x, y - S(34)), (x, y - S(47)), (x - S(22), y - S(30)), (x, y - S(44)), (x + S(22), y - S(30))], INK, 6, seed=k + 1, peso=0.25),
            caminho([(x, y - S(34)), (x + S(16), y)], INK, 6, seed=k + 2, peso=0.15),
            caminho([(x - S(9), y - S(47)), (x + S(9), y - S(47)), (x, y - S(34)), (x - S(9), y - S(47))], INK, 5, fill=cor, fa=1, fechado=True, seed=k + 3, peso=0.15)]


def meta():
    E = [texto("o nosso desafio", 540, 250, 76, INK, peso=0.9),
         texto("150", 540, 590, 360, VERDE, peso=1.3, ancora="150"),
         texto("escuteiros", 540, 720, 120, INK, peso=1.0, ancora="escuteiros")]
    cores = (AMARELO, VERDE, AZUL, VERMELHO)
    n = 0
    for linha, y in enumerate((900, 1070, 1240)):
        for col in range(5):
            E += _mini(150 + col * 195 + (60 if linha % 2 else 0) - 30, y, 700 + n * 5, cores[(n + linha) % 4])
            n += 1
    return E


# ------------------------------------------------------------------ 6. convite
def convite():
    """Sábado à tarde na sede; contactos para mais informação."""
    E = [caminho(rrect(300, 240, 480, 300, 16), INK, 9, fill=CREME, fa=1, fechado=True, seed=800, peso=1.2, ancora="sábado"),
         caminho(rrect(300, 240, 480, 88, 16), INK, 9, fill=VERMELHO, fa=1, fechado=True, seed=801, peso=0.8),
         texto("SÁBADO", 540, 308, 76, (1, 1, 1), peso=0.9),
         texto("à tarde", 540, 470, 120, INK, peso=1.0, ancora="tarde"),
         caminho([(380, 760), (380, 690), (540, 590), (700, 690), (700, 760)], INK, 9, fill=VERMELHO, fa=0.9, fechado=True, seed=802, peso=0.8, ancora="sede"),
         caminho(rrect(400, 690, 280, 150), INK, 9, fill=CREME, fa=1, fechado=True, seed=803, peso=0.8),
         caminho(rrect(500, 750, 80, 90), INK, 8, fill=CASTANHO, fa=0.9, fechado=True, seed=804, peso=0.4),
         texto("na nossa sede", 540, 920, 62, INK, peso=0.9),
         texto("924 428 343", 540, 1020, 92, VERDE, peso=1.1, ancora="informação"),
         texto("geral.994@escutismo.pt", 540, 1100, 56, INK, peso=0.9),
         texto("994caxinas.com", 540, 1172, 62, INK, peso=0.9),
         texto("Sempre Alerta!", 540, 1290, 112, VERDE, peso=1.1, ancora="Sempre"),
         imagem("logo", 540, 1388, 150, peso=1.0)]
    return E


CENAS = {"gancho": lambda p: gancho(), "caxinas": lambda p: caxinas(), "chefes": chefes, "hoje": lambda p: hoje(),
         "meta": lambda p: meta(), "convite": lambda p: convite()}

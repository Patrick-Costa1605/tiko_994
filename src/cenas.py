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


# ------------------------------------------------------------------ 1b. o mar ensina: ninguém rema sozinho
def remo():
    """Um barco com quatro remadores, um por secção (as cores dos lenços), a remar ao mesmo tempo."""
    casco = bez((150, 880), (190, 1000), (330, 1044), (540, 1046)) + bez((540, 1046), (750, 1044), (890, 1000), (930, 880))
    E = [caminho(casco + [(150, 880)], INK, 10, fill=CASTANHO, fa=0.9, fechado=True, seed=600, peso=1.5, ancora="mar"),
         caminho(onda(90, 990, 1052, 12, 190, 0.4), AGUA, 9, seed=601, peso=0.8)]
    for i, (x, cor) in enumerate(((290, AMARELO), (450, VERDE), (610, AZUL), (770, VERMELHO))):
        s = 610 + i * 10
        E.append(caminho([(x - 14, 800), (x + 150, 1098)], CASTANHO, 9, seed=s, peso=0.7))                           # o remo
        E.append(caminho(elipse(x + 158, 1112, 30, 11, a0=0, a1=2 * math.pi), INK, 7, fill=CASTANHO, fa=1, fechado=True, seed=s + 1, peso=0.25))
        E.append(caminho(circulo(x, 704, 32, s + 2), INK, 8, fill=PELE, fa=0.95, fechado=True, seed=s + 2, peso=0.35))   # cabeça
        E.append(caminho(elipse(x, 712, 13, 8, a0=0.15, a1=math.pi - 0.15), INK, 5, seed=s + 3, peso=0.15))            # sorriso
        E.append(caminho([(x, 738), (x, 870)], INK, 9, seed=s + 4, peso=0.4))                                           # tronco
        E.append(caminho([(x, 770), (x + 52, 826), (x - 14, 800)], INK, 8, seed=s + 5, peso=0.35))                      # braços ao remo
        E.append(caminho([(x - 24, 748), (x + 24, 748), (x, 800), (x - 24, 748)], INK, 6, fill=cor, fa=1, fechado=True, seed=s + 6, peso=0.2))
    for i, (y, amp, wl, fase) in enumerate(((1100, 13, 170, 0.0), (1175, 12, 210, 1.9), (1250, 13, 180, 3.0))):
        E.append(caminho(onda(70, 1010, y, amp, wl, fase), AGUA, 9, seed=620 + i, peso=0.8))
    E.append(texto("Ninguém", 540, 330, 190, VERDE, peso=1.0, ancora="Ninguém"))
    E.append(texto("rema sozinho", 540, 470, 120, INK, peso=0.8, ancora="rema", sublinhado=True))
    return E


# ------------------------------------------------------------------ 2. Caxinas
def ancora_icone(cx, cy, s=1.0, seed=0):
    """Âncora que desce da amarra até ao fundo."""
    S = lambda dx, dy: (cx + dx * s, cy + dy * s)
    return [caminho(circulo(cx, cy, 15 * s, seed), INK, 8, fill=CINZA, fa=0.8, fechado=True, seed=seed, peso=0.3, ancora="âncora"),
            caminho([S(0, 15), S(0, 190)], INK, 10, seed=seed + 1, peso=0.5),
            caminho([S(-38, 62), S(38, 62)], INK, 10, seed=seed + 2, peso=0.3),
            caminho(bez(S(-84, 138), S(-70, 200), S(-30, 205), S(0, 188)) + bez(S(0, 188), S(30, 205), S(70, 200), S(84, 138)), INK, 10, seed=seed + 3, peso=0.6),
            caminho([S(-100, 138), S(-84, 108), S(-68, 140), S(-100, 138)], INK, 7, fill=CINZA, fa=0.9, fechado=True, seed=seed + 4, peso=0.2),
            caminho([S(100, 138), S(84, 108), S(68, 140), S(100, 138)], INK, 7, fill=CINZA, fa=0.9, fechado=True, seed=seed + 5, peso=0.2)]


def caxinas():
    E = [texto("1991", 540, 350, 220, INK, peso=1.2),
         texto("Caxinas · Vila do Conde", 540, 440, 58, VERDE, peso=0.9)]
    # mar
    for i, (y, amp, wl, fase) in enumerate(((1000, 12, 170, 0.0), (1075, 14, 200, 1.7), (1150, 12, 160, 3.1), (1225, 14, 210, 0.8))):
        E.append(caminho(onda(70, 1010, y, amp, wl, fase), AGUA, 9, seed=30 + i, peso=0.9))
    # a igreja em forma de barco, a navegar nas ondas
    casco = bez((220, 900), (240, 1010), (330, 1050), (470, 1052)) + bez((470, 1052), (640, 1056), (790, 1040), (860, 900))
    E.append(caminho(casco + [(220, 900)], INK, 10, fill=CREME, fa=1, fechado=True, seed=50, peso=1.6, ancora="iniciativa"))
    E.append(caminho([(400, 900), (400, 760), (690, 650), (690, 900)], INK, 10, fill=VERMELHO, fa=0.9, fechado=True, seed=51, peso=1.2))
    E.append(caminho([(690, 650), (690, 560)], INK, 10, seed=52, peso=0.4))
    E.append(caminho([(655, 598), (725, 598)], INK, 10, seed=53, peso=0.3))
    E.append(caminho(catmull([(500, 900), (500, 850), (545, 820), (590, 850), (590, 900)]), INK, 8, fill=CASTANHO, fa=0.85, seed=54, peso=0.5))
    E.append(texto("Mons. Domingos de Araújo", 540, 1335, 62, INK, peso=1.1, ancora="Monsenhor"))
    E += ancora_icone(900, 1026, 1.12, seed=58)
    E.append(texto("Agrupamento 994", 540, 1420, 78, VERDE, peso=1.2, ancora="nasceu", sublinhado=True))
    return E


# ------------------------------------------------------------------ 4. os chefes: a estafeta do testemunho
def chefes(parte=None):
    nodes = [(330, "1991 – 2013", "Miguel", "Miguel Fernandes de Castro", "1.º Chefe de Agrupamento", VERDE),
             (770, "2013 – 2022", "Milton", "Milton Fernandes de Castro", "filho do chefe Miguel", AZUL),
             (1210, "desde 2022", "Albertino", "Albertino Arteiro", "escuteiro desde 1998", VERMELHO)]
    E = [texto("De chefe em chefe", 540, 232, 100, INK, peso=1.0),
         caminho([(150, 290), (150, 1400)], INK, 9, seed=100, peso=2.0)]
    for i, (y, anos, nome, nome_completo, papel, cor) in enumerate(nodes):
        E.append(caminho(circulo(150, y, 30, i), INK, 9, fill=cor, fa=1, fechado=True, seed=110 + i, peso=0.5))
        E.append(texto(anos, 215, y + 8, 98, cor, align="l", peso=1.1, ancora=nome))
        E.append(texto(nome_completo, 215, y + 88, 52, INK, align="l", peso=0.9))
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


SECCOES = {"lobitos": (270, 680, AMARELO, "Lobitos", "6–10", "lobito", 400),
           "exploradores": (800, 680, VERDE, "Exploradores", "10–14", "explorador", 440),
           "pioneiros": (270, 1120, AZUL, "Pioneiros", "14–18", "pioneiro", 480),
           "caminheiros": (800, 1120, VERMELHO, "Caminheiros", "18–22", "caminheiro", 520)}


def hoje(parte=None):
    """Sem `parte`: a página toda (voz sintética). Com `parte`: só esse pedaço, para a voz entrar depois de o desenho começar."""
    if parte == "pioneiros_caminheiros":                         # duas secções numa só frase («Pioneiros e Caminheiros»): a 2.ª começa um pouco antes da palavra
        E = _seccao(*SECCOES["pioneiros"])
        E[0]["ancora"] = None
        C = _seccao(*SECCOES["caminheiros"])
        C[0]["ancora"], C[0]["avanco"] = "Caminheiros", 0.2
        return E[:-2] + C[:-2] + E[-2:] + C[-2:]                 # primeiro os dois bonecos; os nomes e idades só depois da fala
    if parte in SECCOES:
        E = _seccao(*SECCOES[parte])
        E[0]["ancora"] = None                                   # o boneco começa logo; a voz é que espera por ele
        return E
    E = []
    if parte in (None, "titulo"):
        E.append(texto("Quatro secções", 540, 270, 118, VERDE, peso=1.0))
    if parte is None:
        for k in SECCOES.values():
            E += _seccao(*k)
    if parte in (None, "rodape"):
        E.append(texto("acampamentos · aventuras · serviço", 540, 1352, 54, INK, peso=1.0, ancora="acampamentos"))
        E.append(texto("ninguém fica em terra", 540, 1432, 74, VERDE, peso=1.0, sublinhado=True, ancora="aqui"))
    return E


# ------------------------------------------------------------------ 5. a meta: 150 escuteiros
def _mini(x, y, k, cor, sc=1.5):
    """Boneco minúsculo em 2 traços (corpo e cabeça num só; lenço) para encher a página depressa."""
    S = lambda v: v * sc
    corpo = [(x - S(16), y), (x, y - S(34)), (x + S(16), y), (x, y - S(34)), (x, y - S(47)), (x - S(22), y - S(30)), (x, y - S(44)), (x + S(22), y - S(30)), (x, y - S(44)), (x, y - S(47))]
    corpo += circulo(x, y - S(62), S(15), k, a0=math.pi / 2, a1=math.pi / 2 + 2 * math.pi)
    return [caminho(corpo, INK, 6, seed=k, peso=0.45),
            caminho([(x - S(9), y - S(47)), (x + S(9), y - S(47)), (x, y - S(34)), (x - S(9), y - S(47))], INK, 5, fill=cor, fa=1, fechado=True, seed=k + 3, peso=0.15)]


def meta():
    E = [texto("o nosso desafio", 540, 250, 76, INK, peso=0.9)]
    cores = (AMARELO, VERDE, AZUL, VERMELHO)
    pos = [(150 + col * 195 + (60 if linha % 2 else 0) - 30, y) for linha, y in enumerate((900, 1070, 1240)) for col in range(5)]
    mini = lambda n: _mini(pos[n][0], pos[n][1], 700 + n * 5, cores[(n + n // 5) % 4])
    for n in range(5):                                             # a primeira fila desenha-se enquanto a voz chega ao 150
        E += mini(n)
    E.append(texto("150", 540, 590, 360, VERDE, peso=1.3, ancora="150"))
    E.append(texto("elementos", 540, 720, 120, INK, peso=1.0, ancora="elementos"))
    for n in range(5, 14):
        E += mini(n)
    x, y = pos[14]                                                 # o lugar vazio: «à tua espera»
    sc = 1.5
    E.append(caminho([(x - 16 * sc, y), (x, y - 34 * sc), (x + 16 * sc, y), (x, y - 34 * sc), (x, y - 47 * sc)] + circulo(x, y - 62 * sc, 15 * sc, 99, a0=math.pi / 2, a1=math.pi / 2 + 2 * math.pi),
                     VERMELHO, 7, seed=99, peso=0.5, ancora="lugar"))
    E.append(texto("tu", x, y - 62 * sc - 38, 70, VERMELHO, peso=0.5, ancora="tua"))
    return E


# ------------------------------------------------------------------ 6. convite
def convite():
    """Sábado à tarde na sede; contactos para mais informação."""
    E = [caminho(rrect(300, 160, 480, 300, 16), INK, 9, fill=CREME, fa=1, fechado=True, seed=800, peso=1.2, ancora="sábado"),
         caminho(rrect(300, 160, 480, 88, 16), INK, 9, fill=VERMELHO, fa=1, fechado=True, seed=801, peso=0.8),
         texto("SÁBADO", 540, 228, 76, (1, 1, 1), peso=0.9),
         texto("à tarde", 540, 390, 120, INK, peso=1.0, ancora="tarde"),
         caminho([(380, 680), (380, 610), (540, 510), (700, 610), (700, 680)], INK, 9, fill=VERMELHO, fa=0.9, fechado=True, seed=802, peso=0.8, ancora="sede"),
         caminho(rrect(400, 610, 280, 150), INK, 9, fill=CREME, fa=1, fechado=True, seed=803, peso=0.8),
         caminho(rrect(500, 670, 80, 90), INK, 8, fill=CASTANHO, fa=0.9, fechado=True, seed=804, peso=0.4),
         texto("na nossa sede", 540, 825, 62, INK, peso=0.9),
         texto("924 428 343", 540, 905, 92, VERDE, peso=1.1, ancora="mensagem"),
         texto("geral.994@escutismo.pt", 540, 972, 56, INK, peso=0.9),
         texto("994caxinas.com", 540, 1035, 62, INK, peso=0.9),
         texto("O 994 chama por ti", 540, 1150, 100, VERDE, peso=1.1, ancora="994"),
         texto("Sempre Alerta!", 540, 1214, 62, INK, peso=0.8),
         imagem("logo", 540, 1348, 220, peso=1.0)]
    return E


CENAS = {"gancho": lambda p: gancho(), "remo": lambda p: remo(), "caxinas": lambda p: caxinas(), "chefes": chefes, "hoje": hoje,
         "meta": lambda p: meta(), "convite": lambda p: convite()}

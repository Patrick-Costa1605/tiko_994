"""As páginas do caderno: cada função devolve os elementos pela ordem em que a mão os desenha.
`ancora="palavra"` faz o elemento começar quando a voz diz essa palavra."""
import math

from config import *
from desenho import *

L = AREA[1]          # topo da zona de desenho


def gancho():
    """Abertura: uma pergunta enorme, a mão a riscar depressa e as palavras-chave com marcador amarelo."""
    E = []
    ponto = catmull([(360, 560), (372, 450), (460, 372), (570, 380), (652, 452), (640, 548), (570, 618), (528, 690), (526, 770)], n=12)
    E.append(caminho(ponto, VERMELHO, 38, seed=200, peso=1.6, tremor=2.2))
    E.append(caminho(circulo(526, 880, 30, 5), VERMELHO, 12, fill=VERMELHO, fa=1, fechado=True, seed=201, peso=0.4))
    E.append(caminho([(130, 1030), (950, 1010)], AMARELO, 120, seed=202, peso=0.7, ancora="agrupamento", tremor=1.0))
    E.append(texto("ESCUTEIROS", 540, 1075, 164, VERDE, peso=1.2, ancora="agrupamento"))
    E.append(texto("numa terra de", 540, 1185, 84, INK, peso=0.9, ancora="numa"))
    E.append(caminho([(200, 1330), (890, 1316)], AMARELO, 130, seed=203, peso=0.7, ancora="pescadores", tremor=1.0))
    E.append(texto("PESCADORES", 540, 1380, 164, AZUL, peso=1.2, ancora="pescadores"))
    return E


def caxinas():
    E = [texto("CAXINAS", 540, 350, 200, VERDE, peso=1.2),
         texto("Vila do Conde", 540, 440, 64, INK, peso=0.8)]
    # sol
    E.append(caminho(circulo(870, 640, 80, 1), INK, 8, fill=AMARELO, fa=0.95, fechado=True, seed=1))
    for k in range(10):
        a = k * 2 * math.pi / 10
        E.append(caminho([(870 + math.cos(a) * 108, 640 + math.sin(a) * 108), (870 + math.cos(a) * 146, 640 + math.sin(a) * 146)], INK, 7, seed=20 + k, peso=0.3))
    # igreja na colina
    E.append(caminho(catmull([(420, 1050), (600, 960), (800, 930), (1060, 1000)]), INK, 8, seed=3))
    E.append(caminho([(690, 940), (690, 840), (860, 840), (860, 940)], INK, 8, fill=hx("#EADFC8"), fa=1, fechado=False, seed=4))
    E.append(caminho([(670, 842), (775, 770), (880, 842), (670, 842)], INK, 8, fill=VERMELHO, fa=0.85, fechado=True, seed=5))
    E.append(caminho([(620, 940), (620, 790), (690, 790), (690, 940)], INK, 8, fill=hx("#EADFC8"), fa=1, seed=6))
    E.append(caminho([(612, 792), (655, 730), (698, 792), (612, 792)], INK, 8, fill=VERMELHO, fa=0.85, fechado=True, seed=7))
    E.append(caminho([(655, 730), (655, 676)], INK, 8, seed=8, peso=0.4))
    E.append(caminho([(632, 700), (678, 700)], INK, 8, seed=9, peso=0.4))
    E.append(caminho(catmull([(745, 940), (745, 900), (775, 878), (805, 900), (805, 940)]), INK, 7, fill=CASTANHO, fa=0.8, seed=10, peso=0.5))
    # mar
    for i, (y, amp, wl, fase) in enumerate(((1000, 12, 170, 0.0), (1075, 14, 200, 1.7), (1150, 12, 160, 3.1), (1225, 14, 210, 0.8))):
        E.append(caminho(onda(70, 1010, y, amp, wl, fase), AGUA, 9, seed=30 + i, ancora="mar" if i == 0 else None, peso=0.9))
    # barco de pesca
    cas = [(230, 985), (470, 985), (425, 1060), (285, 1060), (230, 985)]
    E.append(caminho([(350, 985), (350, 800)], INK, 8, seed=40, ancora="pescadores"))
    E.append(caminho([(352, 812), (352, 960), (450, 960), (352, 812)], INK, 7, fill=(1, 1, 1), fa=0.9, fechado=True, seed=41, peso=0.6))
    E.append(caminho([(350, 800), (400, 818), (350, 836)], INK, 6, fill=VERMELHO, fa=1, fechado=True, seed=42, peso=0.3))
    E.append(caminho(cas, INK, 8, fill=VERMELHO, fa=0.9, fechado=True, seed=43))
    E.append(caminho(onda(240, 470, 1075, 10, 90, 0.4), AGUA, 9, seed=44, peso=0.5))
    return E


def escutismo():
    E = [texto("1907", 540, 380, 240, INK, peso=1.1, ancora="1907"),
         texto("Inglaterra", 540, 480, 70, CINZA, peso=0.8)]
    # chapéu de Baden-Powell (de abas largas)
    E.append(caminho(elipse(540, 840, 330, 78), INK, 9, fill=CASTANHO, fa=0.85, fechado=True, seed=50, peso=1.2, ancora="Baden-Powell"))
    copa = catmull([(380, 820), (395, 640), (470, 560), (540, 548), (610, 560), (685, 640), (700, 820)])
    E.append(caminho(copa + [(380, 820)], INK, 9, fill=CASTANHO, fa=0.85, fechado=True, seed=51))
    E.append(caminho([(384, 760), (540, 790), (696, 760)], INK, 8, seed=52, peso=0.5))
    E.append(caminho([(384, 760), (540, 790), (696, 760), (700, 810), (540, 842), (380, 810), (384, 760)], INK, 7, fill=VERDE, fa=0.95, fechado=True, seed=53, peso=0.6))
    E.append(caminho(catmull([(380, 700), (470, 678), (540, 700), (610, 678), (700, 700)]), INK, 6, seed=54, peso=0.5))
    E += flordelis(540, 1090, 1.3, fill=VERDE, seed=60)
    E.append(texto("Baden-Powell", 540, 1330, 100, VERDE, peso=1.2, sublinhado=True))
    return E


def portugal():
    # projeção simples (lon/lat -> ecrã)
    def pj(lon, lat):
        return (120 + (lon + 9.6) * 165, 210 + (42.15 - lat) * 190)
    costa = [(-8.87, 41.87), (-8.84, 41.70), (-8.78, 41.45), (-8.72, 41.20), (-8.68, 41.00), (-8.65, 40.70), (-8.75, 40.45), (-8.88, 40.15), (-8.96, 39.90),
             (-9.05, 39.62), (-9.30, 39.42), (-9.38, 39.34), (-9.42, 39.0), (-9.50, 38.78), (-9.25, 38.68), (-9.12, 38.50), (-8.90, 38.50), (-8.78, 38.20),
             (-8.80, 37.90), (-8.80, 37.45), (-8.97, 37.05), (-8.65, 37.08), (-8.30, 37.09), (-7.90, 37.00), (-7.45, 37.18),
             (-7.42, 37.50), (-7.52, 37.90), (-7.28, 38.20), (-7.06, 38.55), (-7.16, 38.90), (-7.30, 39.28), (-7.45, 39.66), (-7.05, 39.75),
             (-7.00, 40.00), (-6.85, 40.28), (-6.82, 40.60), (-6.95, 41.00), (-6.55, 41.30), (-6.22, 41.58), (-6.55, 41.86), (-7.05, 41.93),
             (-7.45, 41.80), (-7.90, 41.88), (-8.20, 41.95), (-8.65, 42.04)]
    pts = catmull([pj(*p) for p in costa], closed=True, n=6)
    E = [caminho(pts, INK, 9, fill=hx("#DCC8A0"), fa=0.8, fechado=True, seed=70, peso=2.2, tremor=1.8)]
    x, y = pj(-8.42, 41.55)
    E.append(caminho(circulo(x, y, 18, 3), INK, 8, fill=VERMELHO, fa=1, fechado=True, seed=71, peso=0.4, ancora="Braga"))
    E.append(caminho(catmull([(x + 24, y - 6), (x + 200, y - 40), (x + 350, y - 36)]), VERMELHO, 8, seed=72, peso=0.6))
    E.append(texto("Braga", 705, y - 62, 132, VERMELHO, align="l", peso=1.1))
    E.append(texto("27 de maio", 705, y + 26, 72, INK, align="l", peso=0.9, ancora="maio"))
    E.append(texto("de 1923", 705, y + 100, 72, INK, align="l", peso=0.7))
    E += flordelis(810, 740, 0.9, fill=VERDE, seed=80)
    E.append(texto("nasce o CNE", 790, 960, 86, VERDE, peso=1.0, sublinhado=True, ancora="Corpo"))
    E.append(texto("Portugal", 790, 1180, 72, CINZA, peso=0.8))
    return E


def noventa_e_um():
    """Pela ordem da frase: «Em 1991, por iniciativa do Monsenhor… nasceu o Agrupamento 994»."""
    E = [texto("1991", 540, 330, 230, INK, peso=1.1)]
    # rebento: «nasceu»
    E.append(caminho([(200, 1230), (880, 1230)], INK, 8, seed=91, peso=0.6))
    E.append(caminho(catmull([(540, 1230), (545, 1160), (538, 1090)]), INK, 9, seed=92, peso=0.5))
    E.append(caminho(catmull([(540, 1130), (480, 1100), (440, 1050), (500, 1070), (540, 1110)], closed=False), INK, 7, fill=VERDE, fa=0.9, fechado=True, seed=93, peso=0.6))
    E.append(caminho(catmull([(541, 1105), (600, 1070), (640, 1010), (580, 1030), (541, 1085)], closed=False), INK, 7, fill=VERDE, fa=0.9, fechado=True, seed=94, peso=0.6))
    E.append(texto("Mons. Domingos de Araújo", 540, 1350, 78, VERDE, peso=1.3, ancora="Monsenhor"))
    cx, cy, r = 540, 690, 230
    pent = [(cx + r * math.sin(2 * math.pi * k / 5), cy - r * math.cos(2 * math.pi * k / 5)) for k in range(5)]
    E.append(caminho(pent + [pent[0]], INK, 11, fill=hx("#D9A441"), fa=0.95, fechado=True, seed=90, peso=1.4, ancora="Agrupamento"))
    E.append(texto("Caxinas", 540, 585, 60, INK, peso=0.7))
    E.append(texto("994", 540, 740, 170, INK, peso=1.0))
    return E


def chefes(parte=None):
    nodes = [(330, "1991 – 2013", "Miguel", "Fernandes de Castro", "1.º Chefe de Agrupamento", VERDE),
             (770, "2013 – 2022", "Milton", "Fernandes de Castro", "dirigente fundador", AZUL),
             (1210, "desde 2022", "Albertino", "Arteiro", "escuteiro desde 1998", VERMELHO)]
    E = [texto("Chefes de Agrupamento", 540, 232, 88, INK, peso=1.0),
         caminho([(150, 290), (150, 1400)], INK, 9, seed=100, peso=2.0)]
    for i, (y, anos, nome, ap, papel, cor) in enumerate(nodes):
        E.append(caminho(circulo(150, y, 30, i), INK, 9, fill=cor, fa=1, fechado=True, seed=110 + i, peso=0.5))
        E.append(texto(anos, 215, y + 8, 98, cor, align="l", peso=1.1, ancora=nome))
        E.append(texto(nome + " " + ap, 215, y + 88, 66, INK, align="l", peso=0.9))
        E.append(texto(papel, 215, y + 152, 52, CINZA, align="l", peso=0.9))
    return E


def hoje():
    E = [texto("Hoje", 540, 300, 190, VERDE, peso=1.0)]
    cel = [(300, 600, AMARELO, "Lobitos", "6–10"), (780, 600, VERDE, "Exploradores", "10–14"),
           (300, 1040, AZUL, "Pioneiros", "14–18"), (780, 1040, VERMELHO, "Caminheiros", "18–22")]
    for i, (x, y, cor, nome, idades) in enumerate(cel):
        E += lenco_icone(x, y, 1.3, cor, seed=130 + i * 3)
        E.append(texto(nome, x, y + 140, 62, INK, peso=0.9))
        E.append(texto(idades + " anos", x, y + 205, 54, cor if cor != AMARELO else CASTANHO, peso=0.8))
    E.append(texto("a formar jovens desde 1991", 540, 1420, 72, INK, peso=1.2, sublinhado=True, ancora="formar"))
    return E


def missao():
    """Servir: duas pessoas de braços no ar, com um coração entre elas, ao ar livre."""
    E = [texto("servir", 540, 360, 250, VERDE, peso=1.2, sublinhado=True)]
    E.append(caminho([(90, 1250), (990, 1236)], INK, 9, seed=141, peso=0.9, ancora="livre"))
    E += pessoa(260, 1250, 1.5, lenco=AMARELO, braco="cima", seed=170)
    E += pessoa(820, 1250, 1.5, lenco=AZUL, braco="cima", seed=190)
    coracao = catmull([(540, 860), (420, 760), (400, 660), (470, 605), (540, 660), (610, 605), (680, 660), (660, 760)], closed=True)
    E.append(caminho(coracao, INK, 10, fill=VERMELHO, fa=0.9, fechado=True, seed=140, peso=1.4, ancora="fraternidade"))
    return E


def fim():
    E = [texto("Sempre", 540, 380, 200, VERDE, peso=1.1, ancora="Sempre"), texto("Alerta!", 540, 570, 200, VERDE, peso=1.1)]
    E += flordelis(540, 880, 1.7, fill=VERDE, seed=160)
    E.append(imagem("logo", 540, 1280, 260, peso=1.0))
    E.append(texto("@994caxinas", 540, 1440, 68, INK, peso=1.0))
    return E


CENAS = {"gancho": lambda p: gancho(), "caxinas": lambda p: caxinas(), "escutismo": lambda p: escutismo(), "portugal": lambda p: portugal(),
         "noventa_e_um": lambda p: noventa_e_um(), "chefes": lambda p: chefes(), "hoje": lambda p: hoje(), "missao": lambda p: missao(), "fim": lambda p: fim()}

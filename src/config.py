"""Constantes do vídeo «Como surgiu o Escutismo nas Caxinas» (traço à mão, em tempo real)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
STEP = 3                      # o traço «ferve»: muda de tremor a cada 3 frames (10 fps), como desenho à mão

def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

PAPER = hx("#F6F0E1")
INK = hx("#231F1A")
VERDE = hx("#0B9544")          # cores do agrupamento (extraídas do logótipo)
AMARELO = hx("#F2C230")
VERMELHO = hx("#E02B2B")
AZUL = hx("#283994")
AGUA = hx("#3E7CB1")
CASTANHO = hx("#9A6B3C")
PELE = hx("#F2C9A5")
LARANJA = hx("#F28C28")
CINZA = hx("#8C8478")

FONT = "Chewy"
AREA = (0, 130, W, 1480)       # zona do desenho (x, y, largura, altura)

# ---- zonas seguras do Reels (ver ESPECIFICACOES_REELS.md): topo 220, fundo 420, esquerda 60, direita 140
SAFE = (60, 220, W - 140, H - 420)               # x0, y0, x1, y1  ->  (60, 220, 940, 1500)
MARCA_Y = 226                                      # marca d'água (logótipo + @994caxinas), dentro da zona segura
VIEW_Y0, VIEW_H = 312, 1030                        # onde cabe a página desenhada
DESIGN_H = 1330                                    # altura útil das cenas (de y=130 a y=1460)
S_CENA = VIEW_H / DESIGN_H                         # as cenas são desenhadas em 1080×1330 e escaladas para a zona segura
X_CENA = SAFE[0] + ((SAFE[2] - SAFE[0]) - W * S_CENA) / 2
SUB_Y = 1420                                       # linha de base das legendas (1 linha); 2 linhas: ±36
SUB_W = SAFE[2] - SAFE[0] - 20                     # largura máxima das legendas
SUB_CX = (SAFE[0] + SAFE[2]) / 2


def para_ecra(x, y):
    """Coordenadas da cena (1080×1350 + AREA) -> ecrã 1080×1920 dentro da zona segura."""
    return (X_CENA + x * S_CENA, VIEW_Y0 + (y - AREA[1]) * S_CENA)

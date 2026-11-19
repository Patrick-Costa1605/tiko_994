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

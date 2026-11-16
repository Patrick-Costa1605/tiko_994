"""Constantes visuais e técnicas do gerador de vídeos do Tiko (994-Caxinas)."""

W, H, FPS = 1080, 1920, 30

# Paleta
PAPER = (0xFA / 255, 0xF8 / 255, 0xF5 / 255)       # #FAF8F5
INK = (0.10, 0.10, 0.10)
GREEN = (0x1F / 255, 0x5C / 255, 0x36 / 255)        # verde escuro do agrupamento
GREEN_LIGHT = (0x2F / 255, 0xBF / 255, 0x5B / 255)  # destaque de legendas
YELLOW = (0xF2 / 255, 0xC2 / 255, 0x30 / 255)
WHITE = (1, 1, 1)
ORANGE = (0xF2 / 255, 0x8C / 255, 0x28 / 255)
RED = (0xE0 / 255, 0x50 / 255, 0x3A / 255)
BROWN = (0x8B / 255, 0x5A / 255, 0x2B / 255)
KHAKI = (0xC9 / 255, 0xA2 / 255, 0x62 / 255)
SKY = (0x8F / 255, 0xD0 / 255, 0xF0 / 255)
PINK = (0xE8 / 255, 0x70 / 255, 0x7A / 255)

FONT = "Inter"            # instalada no sistema; cai para sans-serif se faltar
LINE = 14                 # espessura base do traço do boneco

# Layout (px)
WATERMARK_Y = 165
BOARD = (90, 215, 900, 430)      # x, y, largura, altura do quadro de ilustração
NECK = (540, 1000)
HEAD_R = 130
GROUND_Y = 1458
SUB_Y = 1610                     # centro da zona de legendas

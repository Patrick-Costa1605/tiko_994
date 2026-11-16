"""Constantes visuais e técnicas do gerador de vídeos do Tiko (994-Caxinas)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 60


def _hex(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


# ---- paleta oficial (extraída de assets/logo-994.png por src/palette.py)
try:
    _pal = json.loads((ROOT / "assets" / "palette.json").read_text())
except Exception:
    _pal = {"verde": "#0B9544", "amarelo": "#F3EC19", "vermelho": "#ED1D24", "azul": "#283994"}
LOGO_GREEN, LOGO_YELLOW = _hex(_pal["verde"]), _hex(_pal["amarelo"])
LOGO_RED, LOGO_BLUE = _hex(_pal["vermelho"]), _hex(_pal["azul"])

PAPER = _hex("#F9F6F0")
INK = (0.13, 0.10, 0.09)
WHITE = (1, 1, 1)
BLACK = (0, 0, 0)

# lenço: corpo verde do agrupamento com debrum amarelo (ver README para mudar)
SCARF = mix(LOGO_GREEN, BLACK, 0.12)
SCARF_DARK = mix(LOGO_GREEN, BLACK, 0.5)
SCARF_LIGHT = mix(LOGO_GREEN, WHITE, 0.30)
TRIM = LOGO_YELLOW
GREEN, YELLOW, RED, BLUE = LOGO_GREEN, LOGO_YELLOW, LOGO_RED, LOGO_BLUE
GREEN_BRIGHT = mix(LOGO_GREEN, WHITE, 0.12)

SKIN = _hex("#FFD9B8")
SKIN_LIGHT = _hex("#FFE8D2")
SKIN_SHADE = _hex("#EFB690")
HAIR = _hex("#3A2A20")
SHIRT = _hex("#D9C49B")
SHIRT_DARK = _hex("#BBA473")
SHORTS = mix(LOGO_BLUE, BLACK, 0.25)
SHOE = _hex("#7A4B2A")
KHAKI = _hex("#C9A262")
BROWN = _hex("#8B5A2B")
ORANGE = _hex("#F28C28")
SKY = _hex("#8FD0F0")
PINK = _hex("#E8707A")

FONT = "Inter"

# Layout (px, no mundo 1080x1920)
GROUND_Y = 1450
SUB_Y = 1625
TIKO_SCALE = 1.15
TIKO_SIDE = 175          # deslocação lateral do Tiko quando há ilustrações
LOGO_PATH = ROOT / "assets" / "logo-994.png"

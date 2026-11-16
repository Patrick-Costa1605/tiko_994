"""Extrai a paleta oficial do agrupamento a partir de assets/logo-994.png -> assets/palette.json."""
import colorsys
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo-994.png"
# intervalos de matiz (graus) das 4 cores da corda do logótipo
BANDS = {"verde": (90, 170), "amarelo": (42, 66), "vermelho": (-15, 12), "azul": (205, 250)}


def extract(path=LOGO):
    im = np.array(Image.open(path).convert("RGBA")).reshape(-1, 4)
    rgb = im[im[:, 3] > 200][:, :3] / 255.0
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in rgb])
    hue = hsv[:, 0] * 360
    out = {}
    for name, (lo, hi) in BANDS.items():
        h = np.where(hue > 180, hue, hue) if lo >= 0 else np.where(hue > 180, hue - 360, hue)
        m = (h >= lo) & (h <= hi) & (hsv[:, 1] > 0.6) & (hsv[:, 2] > 0.5)
        sel = rgb[m]
        # cor mais frequente (moda após quantização) => cor «chapada» oficial
        q = (sel * 255 // 24).astype(int)
        vals, inv, counts = np.unique(q, axis=0, return_inverse=True, return_counts=True)
        best = sel[inv.ravel() == counts.argmax()]
        r, g, b = (np.median(best, axis=0) * 255).round().astype(int)
        out[name] = "#%02X%02X%02X" % (r, g, b)
    return out


if __name__ == "__main__":
    pal = extract()
    (ROOT / "assets" / "palette.json").write_text(json.dumps(pal, indent=1))
    print(pal)

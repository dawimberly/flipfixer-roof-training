"""Turn a top-photo screenshot into plan feet.

Camera height above terrain and a 35 degree vertical field of view.
The image file is the screenshot, not a downloaded tile.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw


def ft_per_px(camera_m: float, terrain_m: float, image_height_px: int, fov_deg: float = 35.0) -> float:
    height = camera_m - terrain_m
    return 2.0 * height * math.tan(math.radians(fov_deg / 2.0)) / image_height_px * 3.2808399


def grid(path: str, out: str, camera_m: float, terrain_m: float, crop) -> float:
    im = Image.open(path).convert("RGB")
    ft = ft_per_px(camera_m, terrain_m, im.height)
    x0, y0, x1, y1 = crop
    view = im.crop((x0, y0, x1, y1))
    draw = ImageDraw.Draw(view)
    step = 5.0 / ft
    n = 0.0
    x = 0.0
    while x < view.width:
        draw.line([(x, 0), (x, view.height)], fill=(255, 40, 40), width=1)
        draw.text((x + 2, 2), str(int(n)), fill=(255, 40, 40))
        x += step
        n += 5
    n = 0.0
    y = 0.0
    while y < view.height:
        draw.line([(0, y), (view.width, y)], fill=(255, 40, 40), width=1)
        draw.text((2, y + 2), str(int(n)), fill=(255, 40, 40))
        y += step
        n += 5
    view.save(out)
    print(out, "ft/px", round(ft, 4), "crop", view.size)
    return ft

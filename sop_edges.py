"""Find roof edges on a top photo. The photo is the run, not the triangle.

A building-footprint box is not a result. This keeps the grey main roof and
the adjoining planes of a different color, then splits each plane on the ridge
that actually sits in the pixels.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
from PIL import Image, ImageDraw


def feet_per_px(camera_m: float, terrain_m: float, height_px: int, fov_deg: float = 35.0) -> float:
    return 2.0 * (camera_m - terrain_m) * math.tan(math.radians(fov_deg / 2.0)) / height_px * 3.28084


def _flood(mask: np.ndarray, seed: tuple[int, int], bounds: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bounds
    h, w = mask.shape
    vis = np.zeros((h, w), np.uint8)
    sx, sy = seed
    if not (0 <= sx < w and 0 <= sy < h) or not mask[sy, sx]:
        return vis
    q = deque([(sx, sy)])
    vis[sy, sx] = 1
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < x0 or nx >= x1 or ny < y0 or ny >= y1 or vis[ny, nx] or not mask[ny, nx]:
                continue
            vis[ny, nx] = 1
            q.append((nx, ny))
    return vis


def grey_roof(im: np.ndarray, seed: tuple[int, int], tol: int = 18) -> np.ndarray:
    r = im[:, :, 0].astype(np.int16)
    g = im[:, :, 1].astype(np.int16)
    b = im[:, :, 2].astype(np.int16)
    sr, sg, sb = im[seed[1], seed[0]]
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    color = (np.abs(r - int(sr)) < tol) & (np.abs(g - int(sg)) < tol) & (np.abs(b - int(sb)) < tol)
    return (color & (sat < 42) & ((r + g + b) > 420)).astype(np.uint8)


def adjoining(im: np.ndarray, roof: np.ndarray) -> np.ndarray:
    """Planes that touch the grey roof and are not lawn, road, or shadow."""
    r = im[:, :, 0].astype(np.int16)
    g = im[:, :, 1].astype(np.int16)
    b = im[:, :, 2].astype(np.int16)
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    bright = (r + g + b) > 280
    not_lawn = ~((g > r + 8) & (g > b) & (sat > 15))
    warm = ((r > g) & (r > b) & (sat > 12) & bright) | ((sat < 30) & bright & (r > 140))
    cand = (warm & not_lawn & (roof == 0)).astype(np.uint8)
    # dilate roof to find touching pixels, then flood those
    from numpy.lib.stride_tricks import sliding_window_view

    pad = np.pad(roof, 3)
    win = sliding_window_view(pad, (7, 7))
    touch = (win.max(axis=(-1, -2)) > 0) & (roof == 0) & cand.astype(bool)
    h, w = roof.shape
    keep = np.zeros_like(roof)
    seeds = np.argwhere(touch)
    seen = np.zeros_like(roof)
    for y, x in seeds[:: max(1, len(seeds) // 80)]:
        if seen[y, x] or not cand[y, x]:
            continue
        blob = _flood(cand, (int(x), int(y)), (max(0, int(x) - 180), max(0, int(y) - 180), min(w, int(x) + 180), min(h, int(y) + 180)))
        area = int(blob.sum())
        if 400 < area < 25000:
            keep = np.maximum(keep, blob)
        seen = np.maximum(seen, blob)
    return keep


def contour(mask: np.ndarray) -> list[tuple[int, int]]:
    ys, xs = np.where(mask > 0)
    if len(xs) < 50:
        return []
    # boundary pixels
    m = mask > 0
    inner = m.copy()
    inner[1:-1, 1:-1] = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    edge = m & ~inner
    pts = np.argwhere(edge)
    if len(pts) < 8:
        return []
    return _simplify(pts[:, ::-1], 6)


def _simplify(pts: np.ndarray, tol_px: float) -> list[tuple[int, int]]:
    """Min-area rectangle is wrong. Walk the boundary and keep corners."""
    # order boundary by angle around centroid, then Douglas-Peucker
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    order = np.argsort(ang)
    ring = pts[order]
    # drop near-duplicates
    keep = [ring[0]]
    for p in ring[1:]:
        if np.hypot(p[0] - keep[-1][0], p[1] - keep[-1][1]) > 4:
            keep.append(p)
    ring = np.array(keep, dtype=float)
    if len(ring) < 4:
        return [(int(p[0]), int(p[1])) for p in ring]

    def dp(a, b, out):
        if b <= a + 1:
            return
        p0, p1 = ring[a], ring[b % len(ring)]
        d = p1 - p0
        n = np.hypot(d[0], d[1]) or 1.0
        dist = np.abs((ring[a + 1 : b, 0] - p0[0]) * d[1] - (ring[a + 1 : b, 1] - p0[1]) * d[0]) / n
        if len(dist) == 0:
            return
        i = int(np.argmax(dist))
        if dist[i] > tol_px:
            k = a + 1 + i
            dp(a, k, out)
            out.append(k)
            dp(k, b, out)

    out = [0]
    dp(0, len(ring) - 1, out)
    out.append(len(ring) - 1)
    return [(int(ring[i][0]), int(ring[i][1])) for i in sorted(set(out))]


def ridge_line(im: np.ndarray, mask: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Longest internal brightness edge. That is the ridge on a nadir photo."""
    gray = im.mean(axis=2)
    gy, gx = np.gradient(gray)
    mag = np.hypot(gx, gy)
    mag = mag * (mask > 0)
    # ignore the outer 8 px of the mask so the eave does not win
    eroded = mask.copy()
    for _ in range(8):
        inner = eroded.copy()
        inner[1:-1, 1:-1] = (
            eroded[1:-1, 1:-1]
            & eroded[:-2, 1:-1]
            & eroded[2:, 1:-1]
            & eroded[1:-1, :-2]
            & eroded[1:-1, 2:]
        )
        eroded = inner
    mag = mag * (eroded > 0)
    if mag.max() < 8:
        return None
    ys, xs = np.where(mag > np.percentile(mag[mag > 0], 92))
    if len(xs) < 30:
        return None
    pts = np.stack([xs, ys], 1).astype(float)
    # principal axis of the strong internal edge
    c = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - c, full_matrices=False)
    direction = vt[0]
    proj = (pts - c) @ direction
    a = c + direction * proj.min()
    b = c + direction * proj.max()
    return (int(a[0]), int(a[1])), (int(b[0]), int(b[1]))


def to_feet(px: tuple[int, int], origin_px: tuple[int, int], ftpx: float) -> tuple[float, float]:
    east = (px[0] - origin_px[0]) * ftpx
    north = -(px[1] - origin_px[1]) * ftpx
    return (round(east, 2), round(north, 2))


def draw(path: str, im: np.ndarray, roof: np.ndarray, extra: np.ndarray, ridge, poly) -> None:
    vis = im.copy()
    vis[roof > 0] = (vis[roof > 0] * 0.55 + np.array([80, 140, 220]) * 0.45).astype(np.uint8)
    vis[extra > 0] = (vis[extra > 0] * 0.55 + np.array([220, 140, 60]) * 0.45).astype(np.uint8)
    out = Image.fromarray(vis)
    dr = ImageDraw.Draw(out)
    if len(poly) >= 2:
        dr.line(poly + [poly[0]], fill=(255, 40, 40), width=2)
        for p in poly:
            dr.ellipse((p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4), fill=(255, 255, 0))
    if ridge:
        dr.line(ridge, fill=(255, 0, 255), width=3)
    out.save(path)

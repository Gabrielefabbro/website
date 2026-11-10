"""Background artwork: contour lines of two atomic orbitals.

A d orbital (top right, behind the portrait) and a p orbital (bottom left), drawn as
iso-lines of the signed wavefunction; the two colours are the two phases (+/-).
Edit ORBITALS / N_LEVELS below and rebuild. Pure standard library.
"""
from __future__ import annotations

import math

W, H = 1600, 1000          # SVG viewBox
STEP = 6                   # grid spacing (smaller = smoother, bigger file)
N_LEVELS = 32              # contour lines per phase
SPACING = 0.92             # ratio between successive levels (closer to 1 = denser lines)

# kind, centre x, centre y, size, rotation (deg), weight
ORBITALS = [
    ("d", 1330, 300, 28, 20, 1 / 40),
    ("p", 250, 790, 40, -40, 1 / 1.5),
]

# colours per theme: (+ phase, - phase, line opacity, opacity behind the text column)
THEMES = {
    "light": ("#1d5c66", "#b0562d", 0.55, 0.25),
    "dark":  ("#7cc3cc", "#e59a72", 0.50, 0.25),
}


def _orbital(kind, x, y, cx, cy, s, rot):
    a = math.radians(rot)
    u, v = (x - cx) / s, (y - cy) / s
    X, Z = u * math.cos(a) + v * math.sin(a), -u * math.sin(a) + v * math.cos(a)
    r = math.hypot(X, Z)
    if kind == "d":
        return (2 * Z * Z - X * X) * math.exp(-r / 3)
    return Z * math.exp(-r / 2)


def _psi(x, y):
    return sum(w * _orbital(k, x, y, cx, cy, s, rot) for k, cx, cy, s, rot, w in ORBITALS)


def _contours(grid, nx, ny, level):
    """Marching squares → list of polylines (lists of points)."""
    segs = []

    def interp(p1, v1, p2, v2):
        t = (level - v1) / (v2 - v1)
        return (round(p1[0] + t * (p2[0] - p1[0]), 1), round(p1[1] + t * (p2[1] - p1[1]), 1))

    for j in range(ny - 1):
        for i in range(nx - 1):
            v = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            p = ((i * STEP, j * STEP), ((i + 1) * STEP, j * STEP),
                 ((i + 1) * STEP, (j + 1) * STEP), (i * STEP, (j + 1) * STEP))
            idx = sum(1 << k for k in range(4) if v[k] > level)
            if idx in (0, 15):
                continue
            edges = [interp(p[k], v[k], p[(k + 1) % 4], v[(k + 1) % 4])
                     if (v[k] > level) != (v[(k + 1) % 4] > level) else None for k in range(4)]
            pts = [e for e in edges if e]
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
            elif len(pts) == 4:
                segs += [(pts[0], pts[1]), (pts[2], pts[3])]
    ends: dict = {}
    for s in segs:
        for e in s:
            ends.setdefault(e, []).append(s)
    used, lines = set(), []
    for s in segs:
        if id(s) in used:
            continue
        used.add(id(s))
        line = [s[0], s[1]]
        for forward in (True, False):
            while True:
                tip = line[-1] if forward else line[0]
                nxt = next((t for t in ends.get(tip, []) if id(t) not in used), None)
                if not nxt:
                    break
                used.add(id(nxt))
                other = nxt[1] if nxt[0] == tip else nxt[0]
                line.append(other) if forward else line.insert(0, other)
        if len(line) > 3:
            lines.append(line)
    return lines


def _path(line):
    pts = line[:1] + line[1:-1:2] + line[-1:] if len(line) > 12 else line
    return "M" + " ".join(f"{x:g} {y:g}" for x, y in pts)


_cache: dict = {}


def _paths():
    if not _cache:
        nx, ny = W // STEP + 2, H // STEP + 2
        grid = [[_psi(i * STEP, j * STEP) for i in range(nx)] for j in range(ny)]
        m = max(abs(v) for row in grid for v in row)
        levels = [m * SPACING ** k for k in range(2, 2 + N_LEVELS)]
        _cache["pos"] = " ".join(_path(l) for lv in levels for l in _contours(grid, nx, ny, lv))
        _cache["neg"] = " ".join(_path(l) for lv in levels for l in _contours(grid, nx, ny, -lv))
    return _cache["pos"], _cache["neg"]


def field_svg(theme: str = "light") -> str:
    """Standalone SVG file, used as a static CSS background image."""
    pos_c, neg_c, alpha, mid = THEMES[theme]
    pos, neg = _paths()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
            f'<defs><linearGradient id="f"><stop offset="0" stop-color="#fff"/>'
            f'<stop offset=".34" stop-color="#fff" stop-opacity="{mid}"/><stop offset=".62" stop-color="#fff" stop-opacity="{mid}"/>'
            f'<stop offset="1" stop-color="#fff"/></linearGradient>'
            f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask></defs>'
            f'<g mask="url(#m)" opacity="{alpha}" fill="none" stroke-width="1.1">'
            f'<path stroke="{pos_c}" d="{pos}"/><path stroke="{neg_c}" d="{neg}"/></g></svg>')


if __name__ == "__main__":
    print(f"{len(field_svg()) / 1e3:.0f} kB")

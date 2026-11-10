"""Background artwork: equipotential lines of a few point-charge quadrupoles.

The page background is the electrostatic potential of two linear nuclear-quadrupole-like
charge distributions (+q, -2q, +q), drawn as contour lines with marching squares.
Tweak QUADRUPOLES / LEVELS below and rebuild. Pure standard library.
"""
from __future__ import annotations

import math

W, H = 1600, 1000          # SVG viewBox
STEP = 7                   # grid spacing (smaller = smoother, bigger file)
LEVELS = 14                # contour levels per sign

# (centre x, centre y, half-length d, rotation in degrees, strength)
QUADRUPOLES = [
    (1360, 230, 120, 24, 1.0),
    (220, 820, 105, -38, 0.9),
]


def _charges():
    out = []
    for cx, cy, d, rot, s in QUADRUPOLES:
        a = math.radians(rot)
        dx, dy = d * math.sin(a), -d * math.cos(a)
        out += [(cx + dx, cy + dy, s), (cx, cy, -2 * s), (cx - dx, cy - dy, s)]
    return out


def _potential(x, y, charges):
    v = 0.0
    for qx, qy, q in charges:
        v += q / math.sqrt((x - qx) ** 2 + (y - qy) ** 2 + 900.0)
    # compress the dynamic range so the rings are spread evenly in space
    return math.copysign(abs(v) ** 0.3, v)


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
    # chain segments into polylines
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
    # drop every other interior point for long lines: invisible at this scale, halves the size
    pts = line[:1] + line[1:-1:2] + line[-1:] if len(line) > 12 else line
    return "M" + " ".join(f"{x:g} {y:g}" for x, y in pts)


# colours per theme: (positive lines, negative lines, overall opacity, opacity in the middle)
THEMES = {
    "light": ("#1d5c66", "#b0562d", 0.48, 0.22),
    "dark":  ("#7cc3cc", "#e59a72", 0.50, 0.22),
}


def field_svg(theme: str = "light") -> str:
    """Standalone SVG file (used as a CSS background image, rasterised once by the browser)."""
    pos_c, neg_c, alpha, mid = THEMES[theme]
    charges = _charges()
    nx, ny = W // STEP + 2, H // STEP + 2
    grid = [[_potential(i * STEP, j * STEP, charges) for i in range(nx)] for j in range(ny)]
    vmax = max(max(abs(v) for v in row) for row in grid) * 0.75
    pos, neg = [], []
    for k in range(1, LEVELS + 1):
        lv = vmax * (0.05 + 0.95 * k / (LEVELS + 1))
        pos += [_path(l) for l in _contours(grid, nx, ny, lv)]
        neg += [_path(l) for l in _contours(grid, nx, ny, -lv)]
    nuclei = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{4 if q > 0 else 6}" fill="{neg_c if q > 0 else pos_c}"/>'
                     for x, y, q in charges)
    # horizontal fade: full strength at the edges, faint behind the text column
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
            f'<defs><linearGradient id="f"><stop offset="0" stop-color="#fff"/>'
            f'<stop offset=".32" stop-color="#fff" stop-opacity="{mid}"/><stop offset=".68" stop-color="#fff" stop-opacity="{mid}"/>'
            f'<stop offset="1" stop-color="#fff"/></linearGradient>'
            f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask></defs>'
            f'<g mask="url(#m)" opacity="{alpha}" fill="none" stroke-width="1.1">'
            f'<path stroke="{pos_c}" d="{" ".join(pos)}"/><path stroke="{neg_c}" d="{" ".join(neg)}"/>'
            f'{nuclei}</g></svg>')


if __name__ == "__main__":
    s = field_svg()
    print(f"{len(s) / 1e3:.0f} kB")

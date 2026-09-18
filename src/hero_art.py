"""Illustrated hero background layers (far ridge + treeline), ported from the
design's interact.py. Deterministic (fixed seed) — the same illustration on
every hero, computed once at import time."""
import math
import random


def _pine(x, base, h, rnd):
    w = h * rnd.uniform(0.34, 0.42)
    tiers = 3 if h > 40 else 2
    pts_l, pts_r = [], []
    for k in range(tiers):
        f_top = k / tiers
        f_bot = (k + 1) / tiers
        y_top = base - h + f_top * h * 0.92
        y_bot = base - h + f_bot * h * 0.92
        half = w / 2 * (0.45 + 0.55 * f_bot)
        inner = half * 0.45
        pts_l += [(x - (inner if k else 0), y_top), (x - half, y_bot)]
        pts_r += [(x + (inner if k else 0), y_top), (x + half, y_bot)]
    trunk = [(x - w * 0.06, base - h * 0.08), (x - w * 0.06, base + 2), (x + w * 0.06, base + 2), (x + w * 0.06, base - h * 0.08)]
    poly = [(x, base - h)] + pts_l[1:] + trunk + list(reversed(pts_r[1:]))
    return "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in poly) + "Z"


def _ridge_y(x, amp, base, seed):
    return base - amp * (0.55 * math.sin(x / 210 + seed) + 0.3 * math.sin(x / 83 + seed * 2.1) + 0.15 * math.sin(x / 37 + seed * 0.7))


def _build_hero_layers():
    rnd = random.Random(7)
    W, H = 1440, 190
    far = "M0,190 " + " ".join(f"L{x},{_ridge_y(x, 26, 96, 1.3):.1f}" for x in range(0, W + 1, 12)) + f" L{W},190 Z"
    far_svg = f'<svg class="hero-layer hero-far" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" aria-hidden="true" data-parallax="0.25"><path d="{far}" fill="#0B3478" opacity="0.8"></path></svg>'
    H2 = 170
    ground = "M0,170 " + " ".join(
        f"L{x},{_ridge_y(x, 10, 140, 4.2) + (0 if 300 < x < 1140 else -14 * math.cos((min(x, W - x)) / 300 * math.pi / 2)):.1f}"
        for x in range(0, W + 1, 12)) + f" L{W},170 Z"
    trees = []
    x = -10
    while x < W + 10:
        edge = min(x, W - x)
        dense = edge < 380
        h = rnd.uniform(70, 150) if edge < 200 else rnd.uniform(48, 104) if dense else rnd.uniform(20, 44)
        base = _ridge_y(x, 10, 140, 4.2) + 6 + (0 if 300 < x < 1140 else -14 * math.cos(edge / 300 * math.pi / 2))
        if dense or rnd.random() < 0.55:
            trees.append(_pine(x, base, h, rnd))
        x += rnd.uniform(14, 26) if dense else rnd.uniform(22, 48)
    near_svg = (f'<svg class="hero-layer hero-near" viewBox="0 0 {W} {H2}" preserveAspectRatio="xMidYMax slice" aria-hidden="true" data-parallax="0">'
                f'<path d="{ground}" fill="#00133F"></path><path d="{"".join(trees)}" fill="#00133F"></path></svg>')
    return far_svg + near_svg


HERO_LAYERS_SVG = _build_hero_layers()


def _wisp(seed, lobes=6, w=200.0, h=26.0):
    """A flat, lumpy cloud wisp: bumpy lit top, flat base, lobes shrinking towards
    both ends so it thins out instead of stopping. Returns (fill path, top-edge path)."""
    r = random.Random(seed)
    base = h - 3.0
    xs = [w * (i / lobes) for i in range(lobes + 1)]
    tops = []
    for i, x in enumerate(xs):
        edge = min(i, lobes - i) / (lobes / 2.0)
        tops.append((x, base - (1.4 + r.uniform(0, 1) * 6.4) * (0.3 + 0.7 * edge)))
    d, top = [f"M{xs[0]:.1f},{base:.1f}"], []
    for i in range(len(tops) - 1):
        (x0, y0), (x1, y1) = tops[i], tops[i + 1]
        cx = (x0 + x1) / 2
        d.append(f"C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")
        top.append((x0, y0, cx, x1, y1))
    fill = " ".join(d) + f" L{xs[-1]:.1f},{base:.1f} Z"
    e = [f"M{top[0][0]:.1f},{top[0][1]:.1f}"]
    for x0, y0, cx, x1, y1 in top:
        e.append(f"C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")
    return fill, " ".join(e)


# seed, lobes, body, lit edge — colours sampled from the hero illustration's own sky
_WISPS = ((11, 7, "#F8842B", "#FBD29A"), (4, 5, "#EBB55F", "#FCE3C0"),
          (23, 8, "#F87A25", "#F9C98B"), (7, 6, "#6E8FC4", "#A8BFE0"))


def _build_hero_clouds():
    """Four wisps drifting across the hero sky, 50-85s to cross, fading at both
    edges. CSS only (see .hero-sky/.wisp/@keyframes drift), so it costs nothing;
    off for reduced motion, half speed on phones."""
    out = []
    for i, (seed, lobes, fill, edge) in enumerate(_WISPS, start=1):
        f, e = _wisp(seed, lobes)
        out.append(f'<svg class="wisp w{i}" viewBox="0 0 200 26" preserveAspectRatio="none" aria-hidden="true">'
                   f'<path d="{f}" fill="{fill}"></path>'
                   f'<path d="{e}" fill="none" stroke="{edge}" stroke-width="1.8" stroke-linecap="round"></path></svg>')
    return f'<div class="hero-sky" aria-hidden="true">{"".join(out)}</div>'


HERO_CLOUDS_SVG = _build_hero_clouds()

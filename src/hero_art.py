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

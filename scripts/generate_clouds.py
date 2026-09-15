"""Cloud sprites for the cinematic homepage hero.

    .venv/Scripts/python.exe scripts/generate_clouds.py

Pure Pillow — the project already depends on it for its image fields — so no
numpy, and nothing is downloaded: the clouds are procedural, with nothing to
license. Output is deterministic per seed and lands in static/img/cine/.

Every sprite is built the same way:
  shape    a soft silhouette from blurred ellipses, so it reads as a cloud bank
  detail   fractal value noise, half "billowed", then domain-warped
  alpha    noise erodes the silhouette — hard at the rim (wisps), gently in
           the core (thin spots, never holes)
  light    density above a pixel shades it, tops catch the sky, and undersides
           pick up a warm glow, as a cloud does over a lit city at dusk

Colours are baked for the night render the hero uses, which is why these are
static assets and not derived from whatever image gets uploaded.
"""

import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageMath, ImageStat

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "cine"

SHADOW = (30, 32, 54)
HIGHLIGHT = (190, 192, 216)
WARM = (206, 152, 128)


def fmath(fn, **images):
    """ImageMath on float images; `fn` receives the operand dict."""
    return ImageMath.lambda_eval(fn, **images)


def clamp01(a, x):
    return a["min"](a["max"](x, 0.0), 1.0)


def to_l(img):
    """Float image (0..255) → 8-bit, clamped explicitly rather than trusting convert()."""
    return fmath(lambda a: a["convert"](a["min"](a["max"](a["x"], 0.0), 255.0), "L"), x=img)


def value_noise(size, cells, rng):
    """Smooth random field, 0..255: a coarse random grid upscaled bicubically."""
    w, h = size
    cw, ch = max(2, round(cells * w / h)), max(2, cells)
    grid = Image.frombytes("L", (cw, ch), rng.randbytes(cw * ch)).convert("F")
    return grid.resize(size, Image.BICUBIC)


def fbm(size, rng, base, octaves, gain=0.5, billow=False):
    """Fractal sum of value noise, normalised back to 0..255.

    `billow` folds each octave around its midpoint (|2n-1|), which turns soft
    blobs into rounded puffs with creases between them — the cumulus look.
    """
    total = Image.new("F", size, 0.0)
    amp, norm = 1.0, 0.0
    for i in range(octaves):
        n = value_noise(size, base * 2**i, rng)
        if billow:
            n = fmath(lambda a: abs(a["n"] * 2.0 - 255.0), n=n)
        total = fmath(lambda a: a["t"] + a["n"] * amp, t=total, n=n)
        norm += amp
        amp *= gain
    return fmath(lambda a: a["t"] / norm, t=total)


def warp(img, rng, strength, grid=(24, 14)):
    """Domain warp through a MESH transform displaced by low-frequency noise."""
    w, h = img.size
    gx, gy = grid
    fx = value_noise((gx + 1, gy + 1), 3, rng)
    fy = value_noise((gx + 1, gy + 1), 3, rng)

    def corner(i, j):
        x, y = w * i / gx, h * j / gy
        # Taper to nothing at the border, so no cell samples from outside the
        # image — that is what leaves straight, card-like edges in a sprite.
        k = strength * min(1.0, min(i, gx - i, j, gy - j) / 3)
        return (
            x + (fx.getpixel((i, j)) / 127.5 - 1.0) * k,
            y + (fy.getpixel((i, j)) / 127.5 - 1.0) * k,
        )

    mesh = []
    for j in range(gy):
        for i in range(gx):
            box = (round(w * i / gx), round(h * j / gy), round(w * (i + 1) / gx), round(h * (j + 1) / gy))
            # Source quad corners in MESH order: NW, SW, SE, NE.
            quad = (*corner(i, j), *corner(i, j + 1), *corner(i + 1, j + 1), *corner(i + 1, j))
            mesh.append((box, quad))
    return img.transform(img.size, Image.MESH, mesh, Image.BILINEAR)


def silhouette(size, puffs, blur):
    """Union of ellipses (fractions of the sprite), softened into one mass."""
    w, h = size
    shape = Image.new("L", size, 0)
    for cx, cy, rx, ry in puffs:
        layer = Image.new("L", size, 0)
        ImageDraw.Draw(layer).ellipse(((cx - rx) * w, (cy - ry) * h, (cx + rx) * w, (cy + ry) * h), fill=255)
        shape = ImageChops.lighter(shape, layer)
    return shape.filter(ImageFilter.GaussianBlur(blur))


def border_fade(size, margin):
    """1 inside, 0 at the sprite edges — guarantees no straight cut-off edge."""
    w, h = size
    box = Image.new("L", size, 0)
    ImageDraw.Draw(box).rectangle((margin, margin, w - margin, h - margin), fill=255)
    return box.filter(ImageFilter.GaussianBlur(margin / 2.5))


def cloud(name, size, puffs, *, seed, blur, warp_px, low, high, opacity=1.0, base_cells=3):
    rng = random.Random(seed)
    w, h = size
    px = min(w, h) / 900  # pixel radii below are tuned at 900px

    detail = fmath(
        lambda a: a["s"] * 0.5 + a["p"] * 0.5,
        s=fbm(size, rng, base_cells, 7),
        p=fbm(size, rng, base_cells + 1, 6, gain=0.55, billow=True),
    )
    detail = warp(to_l(detail), rng, warp_px * px)
    stat = ImageStat.Stat(detail)
    mean, sd = stat.mean[0], max(stat.stddev[0], 1.0)
    n = fmath(lambda a: (a["d"] - mean) / sd, d=detail.convert("F"))  # ≈ zero mean, unit spread

    outline = silhouette(size, puffs, blur * px)
    shape = outline.convert("F")
    # The halo is the silhouette spread wider: noise may tear wisps out of the
    # rim, but beyond the halo it adds nothing, so no stray blobs float free.
    halo = outline.filter(ImageFilter.GaussianBlur(blur * px * 1.5)).point(lambda v: min(255, v * 3)).convert("F")
    fade = border_fade(size, round(min(w, h) * 0.06)).convert("F")

    # Erosion scales with how thin the silhouette is: the rim tears into
    # wisps, the core only thins. smoothstep keeps every transition soft.
    dens = fmath(
        lambda a: a["sh"] / 255.0 + a["n"] * (0.14 + 0.34 * (1.0 - a["sh"] / 255.0)) * a["hl"] / 255.0,
        sh=shape, n=n, hl=halo,
    )
    t = fmath(lambda a: clamp01(a, (a["x"] - low) / (high - low)), x=dens)
    alpha = to_l(fmath(lambda a: a["t"] * a["t"] * (3.0 - a["t"] * 2.0) * a["f"] * opacity, t=t, f=fade))
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.4 * px))

    # Light. `above` is the density stacked over each pixel (the alpha shifted
    # down), `below` the density under it: sky light reaches what has little
    # above it, the city's glow reaches what has little below it.
    body = alpha.filter(ImageFilter.GaussianBlur(12 * px))
    wide = alpha.filter(ImageFilter.GaussianBlur(30 * px))
    reach = round(40 * px)
    above = ImageChops.offset(wide, 0, reach).convert("F")
    below = ImageChops.offset(wide, 0, -reach).convert("F")
    ramp = Image.linear_gradient("L").resize(size).convert("F")  # 0 top → 255 bottom

    lit = fmath(
        lambda a: clamp01(a,
            0.60
            - a["up"] / 255.0 * 0.50
            + (a["b"] - a["up"]) / 255.0 * 0.30
            + a["n"] * 0.05
            + (0.5 - a["r"] / 255.0) * 0.14),
        up=above, b=body.convert("F"), n=n, r=ramp,
    )
    warm = fmath(
        lambda a: clamp01(a, (a["b"] / 255.0 - a["dn"] / 255.0 * 1.05) * 1.6) * (0.3 + a["r"] / 255.0 * 0.7),
        b=body.convert("F"), dn=below, r=ramp,
    )

    channels = []
    for lo_c, hi_c, warm_c in zip(SHADOW, HIGHLIGHT, WARM):
        channels.append(to_l(fmath(
            lambda a: (lo_c + (hi_c - lo_c) * a["l"]) * (1.0 - a["w"] * 0.34) + warm_c * a["w"] * 0.34,
            l=lit, w=warm,
        )))

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.webp"
    Image.merge("RGBA", (*channels, alpha)).save(path, "WEBP", quality=80, method=6)
    print(f"  static/img/cine/{path.name}  {w}x{h}  {path.stat().st_size // 1024}K")


def main():
    print("generate_clouds:")
    # Cumulus bank — rounded tops, flatter base. The mid layer's workhorse.
    cloud(
        "cloud-bank-a", (1600, 900),
        [(0.50, 0.60, 0.40, 0.15), (0.25, 0.54, 0.13, 0.15), (0.38, 0.46, 0.15, 0.19),
         (0.54, 0.42, 0.15, 0.20), (0.68, 0.48, 0.13, 0.17), (0.80, 0.56, 0.10, 0.12)],
        seed=11, blur=34, warp_px=46, low=0.30, high=1.05,
    )
    # Stratus — long and low, for the far layer and the parting clouds.
    cloud(
        "cloud-bank-b", (1600, 900),
        [(0.50, 0.55, 0.42, 0.12), (0.30, 0.50, 0.19, 0.12), (0.63, 0.48, 0.20, 0.13),
         (0.80, 0.56, 0.12, 0.09), (0.18, 0.58, 0.10, 0.08)],
        seed=23, blur=46, warp_px=70, low=0.26, high=1.10, opacity=0.92,
    )
    # Veil — a torn, uneven mass with no single edge: the near-camera pass.
    cloud(
        "cloud-veil", (1200, 1000),
        [(0.50, 0.52, 0.28, 0.25), (0.33, 0.58, 0.16, 0.15), (0.67, 0.44, 0.18, 0.17),
         (0.44, 0.36, 0.13, 0.11), (0.61, 0.65, 0.15, 0.12)],
        seed=37, blur=64, warp_px=100, low=0.28, high=1.20, opacity=0.95, base_cells=2,
    )


if __name__ == "__main__":
    main()

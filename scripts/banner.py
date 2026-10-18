#!/usr/bin/env python3
"""Generate the animated terminal banner (assets/banner-{dark,light}.svg).

    python scripts/banner.py

Text comes from assets/profile.json. The dot portrait is dithered from
assets/source/photo.(png|jpg|jpeg) when present, otherwise from an "RC"
monogram. Re-run after changing either.
"""

from __future__ import annotations

import json
import random
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from theme import THEMES

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PROFILE = ASSETS / "profile.json"

W, H = 1180, 610
VIS_X, VIS_Y, VIS_W, VIS_H = 49, 141, 390, 398
STEP = 4  # px between dots
GROUPS = 8
SEED = 20241001

FONTS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def find_photo() -> Path | None:
    for ext in ("png", "jpg", "jpeg"):
        p = ASSETS / "source" / f"photo.{ext}"
        if p.exists():
            return p
    return None


def monogram(text: str, size: tuple[int, int]) -> Image.Image:
    """Bright letters over a faint halo, so the dither has some texture."""
    w, h = size
    img = Image.new("L", size, 0)
    halo = ImageDraw.Draw(img)
    for r in range(int(w * 0.48), 0, -4):
        halo.ellipse((w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r), fill=int(30 * (1 - r / (w * 0.48))))

    font = None
    for f in FONTS:
        if Path(f).exists():
            font = ImageFont.truetype(f, int(h * 0.5))
            break
    font = font or ImageFont.load_default(size=int(h * 0.5))

    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    box = d.textbbox((0, 0), text, font=font)
    d.text(((w - (box[2] - box[0])) / 2 - box[0], (h - (box[3] - box[1])) / 2 - box[1]), text, font=font, fill=255)
    # Solid letters dither to a full dot grid; only the halo around them gets texture.
    return Image.composite(Image.new("L", size, 255), img, mask)


def portrait(path: Path, size: tuple[int, int]) -> Image.Image:
    img = ImageOps.exif_transpose(Image.open(path)).convert("L")
    img = ImageOps.fit(img, size, centering=(0.5, 0.3))
    return ImageOps.autocontrast(img, cutoff=2)


def dots(source: Image.Image, invert: bool) -> list[tuple[int, int]]:
    grid = source.resize((VIS_W // STEP, VIS_H // STEP), Image.LANCZOS)
    if invert:
        grid = ImageOps.invert(grid)
    bits = grid.convert("1")  # Floyd-Steinberg by default
    px = bits.load()
    return [
        (VIS_X + x * STEP + STEP // 2, VIS_Y + y * STEP + STEP // 2)
        for y in range(bits.height)
        for x in range(bits.width)
        if px[x, y]
    ]


def text_w(s: str, size: float) -> float:
    return len(s) * size * 0.6


def render(profile: dict, points: list[tuple[int, int]], t: dict, source_label: str) -> str:
    mono = t["mono"]
    rng = random.Random(SEED)
    groups: list[list[str]] = [[] for _ in range(GROUPS)]
    for x, y in points:
        groups[rng.randrange(GROUPS)].append(f"M{x} {y}h0")

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="title"><title id="title">{escape(profile["rows"][0][1])} — {escape(profile["title"])}</title>',
        "<style>"
        # Visible by default; the fill-mode "both" hides each piece only until its
        # delay ends, so a renderer without animation support still shows everything.
        ".d{animation:in .9s ease-out both,flk 6s ease-in-out infinite}"
        ".r{animation:rin .45s ease-out both}"
        ".cur{animation:blink 1.1s steps(1) infinite}"
        ".pulse{animation:pulse 2.4s ease-in-out infinite}"
        ".scan{animation:scan 5.5s linear infinite}"
        "@keyframes in{from{opacity:0}}"
        "@keyframes flk{0%,100%{opacity:1}50%{opacity:.55}}"
        "@keyframes rin{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        "@keyframes blink{50%{opacity:0}}"
        "@keyframes pulse{50%{opacity:.35}}"
        f"@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({VIS_H}px)}}}}"
        "</style>",
        f'<defs><clipPath id="vis"><rect x="{VIS_X}" y="{VIS_Y}" width="{VIS_W}" height="{VIS_H}" rx="3"/></clipPath>'
        f'<linearGradient id="sl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["chrome"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{t["chrome"]}" stop-opacity=".22"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="{W - 26}" height="{H - 26}" rx="13" fill="{t["panel"]}" stroke="{t["line"]}"/>',
        f'<path d="M13 62H{W - 13}" stroke="{t["line"]}"/>',
        '<circle cx="38" cy="38" r="6" fill="#FF5F57"/><circle cx="59" cy="38" r="6" fill="#FEBC2E"/><circle cx="80" cy="38" r="6" fill="#28C840"/>',
        f'<text x="{W / 2}" y="43" text-anchor="middle" fill="{t["muted"]}" font-family="{mono}" font-size="13">{escape(profile["title"])}</text>',
        # left panel
        f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>',
        f'<path d="M35 124H453" stroke="{t["line"]}"/>',
        f'<text x="49" y="111" fill="{t["chrome"]}" font-family="{mono}" font-size="13" font-weight="700" letter-spacing="1.2">VISUAL.MAP</text>',
        f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" font-family="{mono}" font-size="11">{source_label}</text>',
        f'<path d="M49 141h12M49 141v12M439 141h-12M439 141v12M49 539h12M49 539v-12M439 539h-12M439 539v-12" fill="none" stroke="{t["chrome"]}" opacity=".55"/>',
        '<g clip-path="url(#vis)">',
    ]
    for i, g in enumerate(groups):
        o.append(
            f'<path class="d" style="animation-delay:{0.15 * i:.2f}s,{1.2 + 0.7 * i:.2f}s" d="{"".join(g)}" '
            f'stroke="{t["accent"]}" stroke-width="2.6" stroke-linecap="round" fill="none"/>'
        )
    o.append(f'<rect class="scan" x="{VIS_X}" y="{VIS_Y - 60}" width="{VIS_W}" height="60" fill="url(#sl)"/></g>')

    # right panel
    x1, x2 = 491, 1127
    o.append(f'<text x="{x1}" y="111" fill="{t["chrome"]}" font-family="{mono}" font-size="13" font-weight="700" letter-spacing="1.2">SYS.INFO</text>')
    o.append(f'<text x="{x2}" y="111" text-anchor="end" fill="{t["muted"]}" font-family="{mono}" font-size="11">$ whoami --verbose</text>')
    o.append(f'<path d="M{x1 - 1} 124H{x2 + 3}" stroke="{t["line"]}"/>')
    for i, (label, value) in enumerate(profile["rows"]):
        y = 152 + i * 24
        lx = x1 + text_w(label, 14) + 10
        vx = x2 - text_w(value, 14) - 10
        o.append(f'<g class="r" style="animation-delay:{0.5 + 0.11 * i:.2f}s">')
        o.append(f'<text x="{x1}" y="{y}" fill="{t["muted"]}" font-family="{mono}" font-size="14">{escape(label)}</text>')
        if vx > lx:
            o.append(f'<path d="M{lx:.1f} {y - 4}H{vx:.1f}" stroke="{t["line"]}" stroke-dasharray="1 4"/>')
        o.append(f'<text x="{x2}" y="{y}" text-anchor="end" fill="{t["text"]}" font-family="{mono}" font-size="14">{escape(value)}</text>')
        o.append("</g>")
    cy = 152 + len(profile["rows"]) * 24
    o.append(
        f'<g class="r" style="animation-delay:{0.5 + 0.11 * len(profile["rows"]):.2f}s">'
        f'<text x="{x1}" y="{cy}" fill="{t["accent"]}" font-family="{mono}" font-size="14">$</text>'
        f'<rect class="cur" x="{x1 + 14}" y="{cy - 12}" width="8" height="15" fill="{t["accent"]}"/></g>'
    )
    o.append(f'<path d="M{x1 - 1} 530H{x2 + 3}" stroke="{t["line"]}"/>')
    o.append(f'<text class="pulse" x="{x1}" y="548" fill="{t["ok"]}" font-family="{mono}" font-size="11">● {escape(profile["status"])}</text>')
    o.append(f'<text x="{x2 + 1}" y="548" text-anchor="end" fill="{t["muted"]}" font-family="{mono}" font-size="11">{escape(profile["node"])}</text>')
    o.append("</svg>")
    return "".join(o)


def main() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    photo = find_photo()
    size = (VIS_W * 2, VIS_H * 2)
    if photo:
        src, label, invert_light = portrait(photo, size), f"{VIS_W // STEP}×{VIS_H // STEP} / 1-BIT", True
    else:
        src, label, invert_light = monogram(profile.get("monogram", "RC"), size), "MONOGRAM / 1-BIT", False

    for name, theme in THEMES.items():
        pts = dots(src, invert=(name == "light" and invert_light))
        (ASSETS / f"banner-{name}.svg").write_text(render(profile, pts, theme, label), encoding="utf-8")
        print(f"banner-{name}.svg: {len(pts)} dots")


if __name__ == "__main__":
    main()

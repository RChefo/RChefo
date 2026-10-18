#!/usr/bin/env python3
"""Draw a radar chart from a JSON file of 0-100 axis values.

    python scripts/radar.py --data assets/skills.json -o assets/radar
    -> assets/radar-dark.svg, assets/radar-light.svg
"""

from __future__ import annotations

import argparse
import json
import math
from html import escape
from pathlib import Path

from theme import THEMES

W, H = 720, 520
R = 190
RINGS = 4


def point(i: int, n: int, r: float) -> tuple[float, float]:
    a = -math.pi / 2 + 2 * math.pi * i / n
    return r * math.cos(a), r * math.sin(a)


def poly(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def render(data: dict, theme: dict, show_values: bool) -> str:
    axes = data["axes"]
    n = len(axes)
    cx, cy = W / 2, H / 2 + 22
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(data["title"])}" font-family="{theme["sans"]}">',
        "<style>.shape{transform-origin:0 0;animation:grow 1.1s cubic-bezier(.22,1,.36,1) both}"
        "@keyframes grow{from{transform:scale(.04);opacity:0}}</style>",
        f'<text x="{W / 2}" y="28" text-anchor="middle" font-size="15" font-weight="700" '
        f'fill="{theme["text"]}">{escape(data["title"])}</text>',
        f'<g transform="translate({cx},{cy})">',
    ]
    for k in range(RINGS, 0, -1):
        ring = [point(i, n, R * k / RINGS) for i in range(n)]
        out.append(f'<polygon points="{poly(ring)}" fill="none" stroke="{theme["line"]}" opacity="{0.4 + 0.12 * k:.2f}"/>')
    for i in range(n):
        x, y = point(i, n, R)
        out.append(f'<line x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}" stroke="{theme["line"]}" opacity=".6"/>')

    shape = [point(i, n, R * max(0, min(100, a["value"])) / 100) for i, a in enumerate(axes)]
    out.append('<g class="shape">')
    out.append(
        f'<polygon points="{poly(shape)}" fill="{theme["accent"]}" fill-opacity=".22" '
        f'stroke="{theme["accent"]}" stroke-width="2.5" stroke-linejoin="round"/>'
    )
    for x, y in shape:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{theme["panel"]}" stroke="{theme["accent"]}" stroke-width="2"/>')
    out.append("</g>")

    for i, a in enumerate(axes):
        x, y = point(i, n, R + 22)
        anchor = "middle" if abs(x) < 1 else ("start" if x > 0 else "end")
        dy = -4 if y < -1 else (14 if y > 1 else 5)
        label = escape(a["label"])
        if show_values:
            label += f' <tspan fill="{theme["accent"]}">{a["value"]}</tspan>'
        out.append(
            f'<text x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}" font-size="13" '
            f'font-weight="600" fill="{theme["muted_text"]}">{label}</text>'
        )
    out.append("</g></svg>")
    return "".join(out)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("-o", "--out", required=True, help="output prefix, e.g. assets/radar")
    p.add_argument("--values", action="store_true", help="print each value next to its label")
    args = p.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    for name, theme in THEMES.items():
        Path(f"{args.out}-{name}.svg").write_text(render(data, theme, args.values), encoding="utf-8")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Self-hosted GitHub stats and top-languages cards.

    GITHUB_TOKEN=... python scripts/cards.py --user RChefo --out assets
    -> assets/card-stats-{dark,light}.svg, assets/card-langs-{dark,light}.svg

Replaces github-readme-stats & co, whose shared public instances go down.
With a token that belongs to --user, private repos are counted too.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.request
from html import escape
from pathlib import Path

from theme import THEMES

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(ownerAffiliations: OWNER, first: 100, after: $after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        isFork
        stargazerCount
        languages(first: 20) { edges { size node { name color } } }
      }
    }
  }
}
"""


def graphql(token: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def fetch(user: str, token: str) -> dict:
    after, repos, first = None, [], None
    while True:
        page = graphql(token, {"login": user, "after": after})
        first = first or page
        repos += page["repositories"]["nodes"]
        info = page["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            break
        after = info["endCursor"]

    days = [
        d
        for w in first["contributionsCollection"]["contributionCalendar"]["weeks"]
        for d in w["contributionDays"]
    ]
    return {
        "repos": first["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "followers": first["followers"]["totalCount"],
        "contributions": first["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "days": days,
        "langs": [r["languages"]["edges"] for r in repos if not r["isFork"]],
    }


def streaks(days: list[dict]) -> tuple[int, int]:
    today = dt.date.today().isoformat()
    counts = [d["contributionCount"] for d in days if d["date"] <= today]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # Today not having a contribution yet shouldn't break the current streak.
    if counts and not counts[-1]:
        counts = counts[:-1]
    current = 0
    for c in reversed(counts):
        if not c:
            break
        current += 1
    return current, longest


def stats_svg(user: str, s: dict, t: dict) -> str:
    current, longest = streaks(s["days"])
    tiles = [
        (s["contributions"], "Contributions (1y)"),
        (s["repos"], "Repositories"),
        (s["stars"], "Total stars"),
        (current, "Current streak"),
        (longest, "Longest streak"),
        (s["followers"], "Followers"),
    ]
    W, H = 480, 160
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(user)} GitHub statistics" font-family="{t["sans"]}">',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["bg"]}" stroke="{t["line"]}"/>',
        f'<text x="22" y="36" font-size="15" font-weight="700" fill="{t["accent"]}">{escape(user)}</text>',
        f'<text x="{W - 22}" y="36" font-size="11" text-anchor="end" fill="{t["muted"]}">at a glance</text>',
        f'<line x1="22" y1="48" x2="{W - 22}" y2="48" stroke="{t["line"]}"/>',
    ]
    for i, (value, label) in enumerate(tiles):
        x, y = 22 + (i % 3) * 150, 76 + (i // 3) * 46
        out.append(f'<text x="{x}" y="{y}" font-size="23" font-weight="700" fill="{t["text"]}">{value:,}</text>')
        out.append(f'<text x="{x}" y="{y + 17}" font-size="10.5" fill="{t["muted"]}">{label}</text>')
    out.append("</svg>")
    return "".join(out)


def top_languages(edge_lists: list, exclude: set[str], limit: int) -> list[tuple[str, str, float]]:
    totals: dict[str, list] = {}
    for edges in edge_lists:
        for e in edges:
            name = e["node"]["name"]
            if name in exclude:
                continue
            entry = totals.setdefault(name, [0, e["node"]["color"] or "#8b949e"])
            entry[0] += e["size"]
    ranked = sorted(totals.items(), key=lambda kv: -kv[1][0])[:limit]
    grand = sum(v[0] for _, v in ranked) or 1
    return [(name, color, size / grand * 100) for name, (size, color) in ranked]


def langs_svg(langs: list[tuple[str, str, float]], t: dict) -> str:
    W = 480
    rows = (len(langs) + 1) // 2
    H = 92 + rows * 24
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Most used languages" font-family="{t["sans"]}">',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["bg"]}" stroke="{t["line"]}"/>',
        f'<text x="22" y="36" font-size="15" font-weight="700" fill="{t["accent"]}">Most used languages</text>',
        f'<text x="{W - 22}" y="36" font-size="11" text-anchor="end" fill="{t["muted"]}">by bytes</text>',
        f'<clipPath id="bar"><rect x="22" y="52" width="{W - 44}" height="10" rx="5"/></clipPath>',
        '<g clip-path="url(#bar)">',
    ]
    x = 22.0
    for _, color, pct in langs:
        w = (W - 44) * pct / 100
        out.append(f'<rect x="{x:.2f}" y="52" width="{w + 0.5:.2f}" height="10" fill="{color}"/>')
        x += w
    out.append("</g>")
    for i, (name, color, pct) in enumerate(langs):
        cx, cy = 22 + (i % 2) * 225, 92 + (i // 2) * 24
        out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>')
        out.append(
            f'<text x="{cx + 16}" y="{cy}" font-size="12.5" fill="{t["muted_text"]}">{escape(name)} '
            f'<tspan fill="{t["muted"]}">{pct:.1f}%</tspan></text>'
        )
    out.append("</svg>")
    return "".join(out)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True)
    p.add_argument("--out", default="assets")
    p.add_argument("--exclude", default="", help="comma-separated languages to leave out")
    p.add_argument("--limit", type=int, default=8)
    args = p.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN (a PAT owned by --user also counts private repos).")

    s = fetch(args.user, token)
    langs = top_languages(s["langs"], {x.strip() for x in args.exclude.split(",") if x.strip()}, args.limit)
    out = Path(args.out)
    for name, theme in THEMES.items():
        (out / f"card-stats-{name}.svg").write_text(stats_svg(args.user, s, theme), encoding="utf-8")
        (out / f"card-langs-{name}.svg").write_text(langs_svg(langs, theme), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Shared palette for every generated SVG. Change ACCENT here to re-skin the profile."""

SANS = "ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Consolas,Menlo,monospace"

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "panel": "#161b22",
        "panel2": "#1c2330",
        "line": "#30363d",
        "text": "#e6edf3",
        "muted_text": "#c9d1d9",
        "muted": "#8b949e",
        "accent": "#ff9f43",
        "chrome": "#2dd4bf",
        "ok": "#3fb950",
        "sans": SANS,
        "mono": MONO,
    },
    "light": {
        "bg": "#ffffff",
        "panel": "#f6f8fa",
        "panel2": "#eef1f5",
        "line": "#d0d7de",
        "text": "#1f2328",
        "muted_text": "#424a53",
        "muted": "#656d76",
        "accent": "#c2410c",
        "chrome": "#0f766e",
        "ok": "#1a7f37",
        "sans": SANS,
        "mono": MONO,
    },
}

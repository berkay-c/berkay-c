#!/usr/bin/env python3
"""Build the profile README hero as two SVGs (light/dark) with text converted to outlines.

usage: python build_hero.py <fonts-dir> <out-dir>
needs: fonttools, uharfbuzz; fonts: Brygada-Italic-400.ttf, Familjen-500.ttf, FragmentMono-Regular.ttf
"""
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# README hero is centred; the LinkedIn banner keeps clear of the profile photo (bottom-left), so its text sits right of centre.
LAYOUTS = {
    "hero": {"w": 1200, "h": 500, "rx": 12, "cx": 600, "quote": 50, "mark": 45, "b1": 160, "b2": 219,
             "rule_y": 326.5, "rule_in": 200, "rule_out": 320, "name": 19, "name_b": 333, "role": 13, "role_b": 378},
    "banner": {"w": 1584, "h": 396, "rx": 0, "cx": 1040, "quote": 44, "mark": 40, "b1": 144, "b2": 196,
               "rule_y": 252.5, "rule_in": 205, "rule_out": 300, "name": 20, "name_b": 260, "role": 14, "role_b": 300},
}
NAME = "BERKAY YASIN CIFTCI"
THEMES = {
    "light": {"bg": "#f3f2ee", "ink": "#151514", "soft": "#6e6d68", "hair": "#d3d2cb"},
    "dark": {"bg": "#0f1012", "ink": "#ecebe6", "soft": "#8a8984", "hair": "#2c2d31"},
}


class Face:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.upem = self.tt["head"].unitsPerEm
        self.order = self.tt.getGlyphOrder()
        self.glyphs = self.tt.getGlyphSet()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def run(self, text, size, tracking=0.0):
        """Shape text; return [(glyph, x)] in px and the run width (no trailing tracking)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        k, x, out = size / self.upem, 0.0, []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((self.order[info.codepoint], x + pos.x_offset * k))
            x += pos.x_advance * k + tracking
        return out, x - tracking if out else 0.0

    def path(self, glyphs, size, x0, baseline):
        k = size / self.upem
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        for name, x in glyphs:
            self.glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, x0 + x, baseline)))
        return pen.getCommands()


def build(fonts, theme, layout="hero"):
    c, L = THEMES[theme], LAYOUTS[layout]
    W, H, cx = L["w"], L["h"], L["cx"]
    serif = Face(fonts / "Brygada-Italic-400.ttf")
    sans = Face(fonts / "Familjen-500.ttf")
    mono = Face(fonts / "FragmentMono-Regular.ttf")
    parts = []

    def line(segments, baseline):
        """segments: [(face, text, size, tracking, color)] laid out left to right, centred as one line."""
        runs = [(f, *f.run(t, s, tr), s, col) for f, t, s, tr, col in segments]
        gap = 2.0
        total = sum(r[2] for r in runs) + gap * (len(runs) - 1)
        x = cx - total / 2
        for face, glyphs, width, size, col in runs:
            parts.append(f'<path fill="{col}" d="{face.path(glyphs, size, x, baseline)}"/>')
            x += width + gap

    q, m = L["quote"], L["mark"]
    # the quote: first half full ink, second half soft
    line([(serif, "“", m, 0, c["soft"]), (serif, "Building things people use.", q, 0, c["ink"])], L["b1"])
    line([(serif, "Learning how to sell them.", q, 0, c["soft"]), (serif, "”", m, 0, c["soft"])], L["b2"])
    # name between two short rules
    y, a, b = L["rule_y"], L["rule_in"], L["rule_out"]
    parts.append(f'<path stroke="{c["hair"]}" stroke-width="1" d="M{cx - b} {y}H{cx - a}M{cx + a} {y}H{cx + b}"/>')
    line([(sans, NAME, L["name"], L["name"] * 0.28, c["ink"])], L["name_b"])
    line([(mono, "SOFTWARE ENGINEER", L["role"], L["role"] * 0.22, c["soft"])], L["role_b"])

    label = "“Building things people use. Learning how to sell them.” — Berkay Yasin Ciftci, Software Engineer"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">'
            f"<title>{label}</title>"
            f'<rect width="{W}" height="{H}" rx="{L["rx"]}" fill="{c["bg"]}"/>'
            + "".join(parts) + "</svg>\n")


if __name__ == "__main__":
    fonts, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for layout in LAYOUTS:
        for theme in THEMES:
            f = out / f"{layout}-{theme}.svg"
            f.write_text(build(fonts, theme, layout), encoding="utf-8")
            print("wrote", f)

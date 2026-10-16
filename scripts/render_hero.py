# /// script
# requires-python = ">=3.11"
# dependencies = ["altair==5.5.0", "pandas==2.2.3", "networkx==3.4.2", "vl-convert-python>=1.7"]
# ///
"""Render the README hero image (deploy/hero.png) from the notebook's own data.

This is the reproducible "pattern 2" from deploy/social_card_brief.md: it rebuilds
the exact hero force-graph at a chosen fine-tuning step (default 80, the frame
where the transition is most legible) and writes a PNG. Beats a manual screenshot
because `uv run --script scripts/render_hero.py` regenerates it on demand.

The node/edge data and the layout recipe are copied from notebook.py (the "32
nodes" cell, the layout cell, and the hero chart cell). KEEP IN SYNC: if the
illustrative edges or the v0.2 measured edges change, re-run this.

Run:
    uv run --script scripts/render_hero.py            # -> deploy/hero.png at step 80
    STEP=120 uv run --script scripts/render_hero.py   # a different frame
"""
import os
from pathlib import Path

import altair as alt
import networkx as nx
import pandas as pd

STEP = int(os.environ.get("STEP", "80"))
# CARD=1 renders the 1200x630 social card (title overlay, no legend) per
# deploy/social_card_brief.md, instead of the README hero.
CARD = os.environ.get("CARD") == "1"
OUT = Path(os.environ.get("OUT", "deploy/social-card.png" if CARD else "deploy/hero.png"))

# --- nodes (label, zone) -- mirrors notebook.py "32 nodes" cell -------------
NODES = [
    ("Harry", "hp"), ("Hogwarts", "hp"), ("Ron", "hp"), ("Hermione", "hp"),
    ("Quidditch", "hp"), ("Voldemort", "hp"), ("Snape", "hp"),
    ("Dumbledore", "hp"), ("McGonagall", "hp"), ("Hagrid", "hp"),
    ("Sirius", "hp"), ("Hedwig", "hp"),
    ("magic", "bridge"), ("wand", "bridge"), ("wizard", "bridge"),
    ("scar", "bridge"), ("spell", "bridge"), ("broom", "bridge"),
    ("charm", "bridge"),
    ("school", "general"), ("British", "general"), ("boy", "general"),
    ("fantasy", "general"), ("novel", "general"), ("England", "general"),
    ("London", "general"), ("friend", "general"), ("actor", "general"),
    ("story", "general"), ("year", "general"), ("teacher", "general"),
    ("mother", "general"),
]

# --- edges (source, target, w_step0, w_step120) -- mirrors notebook.py ------
EDGES = [
    ("Harry", "Hogwarts", 0.95, 0.05), ("Harry", "Ron", 0.90, 0.05),
    ("Harry", "Hermione", 0.88, 0.05), ("Harry", "magic", 0.85, 0.06),
    ("Harry", "Voldemort", 0.80, 0.05), ("Harry", "scar", 0.75, 0.10),
    ("Harry", "Snape", 0.70, 0.05), ("Harry", "Dumbledore", 0.65, 0.05),
    ("Harry", "Hedwig", 0.65, 0.05), ("Harry", "Sirius", 0.55, 0.05),
    ("Harry", "Hagrid", 0.55, 0.05), ("Hogwarts", "magic", 0.90, 0.10),
    ("Hogwarts", "Quidditch", 0.85, 0.05), ("Hogwarts", "Dumbledore", 0.80, 0.10),
    ("Hogwarts", "McGonagall", 0.78, 0.08), ("Hogwarts", "Hagrid", 0.70, 0.08),
    ("Ron", "Hermione", 0.85, 0.05), ("Quidditch", "wand", 0.50, 0.05),
    ("Quidditch", "broom", 0.80, 0.05), ("Voldemort", "magic", 0.70, 0.10),
    ("Voldemort", "Sirius", 0.55, 0.05), ("McGonagall", "Snape", 0.60, 0.05),
    ("magic", "wand", 0.85, 0.85), ("magic", "wizard", 0.90, 0.90),
    ("magic", "spell", 0.85, 0.85), ("magic", "charm", 0.80, 0.80),
    ("wizard", "wand", 0.85, 0.85), ("wizard", "school", 0.50, 0.50),
    ("wizard", "fantasy", 0.70, 0.70), ("wand", "spell", 0.80, 0.80),
    ("wand", "charm", 0.70, 0.70), ("broom", "wizard", 0.60, 0.60),
    ("scar", "boy", 0.40, 0.40), ("school", "boy", 0.70, 0.70),
    ("school", "teacher", 0.75, 0.75), ("school", "year", 0.60, 0.60),
    ("boy", "friend", 0.65, 0.65), ("boy", "mother", 0.55, 0.55),
    ("British", "England", 0.95, 0.95), ("British", "London", 0.85, 0.85),
    ("England", "London", 0.90, 0.90), ("fantasy", "novel", 0.85, 0.85),
    ("novel", "story", 0.80, 0.80), ("story", "year", 0.40, 0.40),
    ("Harry", "British", 0.05, 0.65), ("Harry", "actor", 0.02, 0.70),
    ("Harry", "London", 0.04, 0.55), ("Harry", "boy", 0.20, 0.50),
    ("Harry", "novel", 0.10, 0.40), ("Harry", "friend", 0.10, 0.30),
    ("Harry", "story", 0.08, 0.45),
]

ZONE_PALETTE = {"hp": "#E8523A", "bridge": "#F4A742", "general": "#5B8FF9"}
EDGE_PALETTE = {
    "dying (HP-specific)": "#E8523A",
    "preserved (general)": "#9DA8B8",
    "growing (re-purposed)": "#5AD8A6",
}


def w_at(w0, w120, step):
    return w0 + (w120 - w0) * (step / 120)


# Two stable layouts; step-120 seeded FROM step-0 so the morph stays registered
# (same trick as the notebook).
_g0, _g120 = nx.Graph(), nx.Graph()
for _label, _ in NODES:
    _g0.add_node(_label)
    _g120.add_node(_label)
for _s, _t, _w0, _w120 in EDGES:
    if _w0 > 0.04:
        _g0.add_edge(_s, _t, weight=_w0)
    if _w120 > 0.04:
        _g120.add_edge(_s, _t, weight=_w120)

pos0 = nx.spring_layout(_g0, k=1.5, iterations=300, seed=42, weight="weight")
pos120 = nx.spring_layout(_g120, pos=pos0, k=1.5, iterations=300, seed=42, weight="weight")

_t = STEP / 120.0
pos = {n: ((1 - _t) * pos0[n][0] + _t * pos120[n][0],
           (1 - _t) * pos0[n][1] + _t * pos120[n][1]) for n in pos0}

node_df = pd.DataFrame(
    [{"label": l, "zone": z, "x": pos[l][0], "y": pos[l][1]} for l, z in NODES]
)

edge_rows = []
for _s, _t2, _w0, _w120 in EDGES:
    _w = w_at(_w0, _w120, STEP)
    if _w < 0.04:
        continue
    if _w120 < _w0 - 0.05:
        kind = "dying (HP-specific)"
    elif _w120 > _w0 + 0.05:
        kind = "growing (re-purposed)"
    else:
        kind = "preserved (general)"
    edge_rows.append({
        "x": pos[_s][0], "y": pos[_s][1],
        "x2": pos[_t2][0], "y2": pos[_t2][1],
        "weight": _w, "kind": kind,
    })
edge_df = pd.DataFrame(edge_rows)

# --- label placement ---------------------------------------------------------
# Labels sit above their node by default. Where two would overlap (nodes nearly
# on top of each other at this step, e.g. magic/wizard), the later one moves
# below its node; node positions never change. Explicit, un-niced scale domains
# make the data -> pixel mapping exact, so this overlap test matches the image.
W, H = (1120, 455) if CARD else (1200, 600)
_xs, _ys = node_df["x"], node_df["y"]
_pad_x = 0.04 * (_xs.max() - _xs.min())
_pad_y = 0.08 * (_ys.max() - _ys.min())
X_DOMAIN = [_xs.min() - _pad_x, _xs.max() + _pad_x]
Y_DOMAIN = [_ys.min() - _pad_y, _ys.max() + _pad_y]
X_SCALE = alt.Scale(domain=X_DOMAIN, nice=False, zero=False)
Y_SCALE = alt.Scale(domain=Y_DOMAIN, nice=False, zero=False)
LABEL_ABOVE, LABEL_BELOW = -16, 20  # text dy in px
CHAR_W, LABEL_H = 7.8, 16           # rough box for 13 px bold text


def _label_box(row, dy):
    cx = (row.x - X_DOMAIN[0]) / (X_DOMAIN[1] - X_DOMAIN[0]) * W
    cy = (Y_DOMAIN[1] - row.y) / (Y_DOMAIN[1] - Y_DOMAIN[0]) * H + dy
    half_w = (len(row.label) * CHAR_W + 6) / 2
    return (cx - half_w, cy - LABEL_H / 2, cx + half_w, cy + LABEL_H / 2)


def _overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


_placed, _below, _unresolved = [], [], []
for _row in node_df.sort_values("y", ascending=False).itertuples():
    _up = _label_box(_row, LABEL_ABOVE)
    if not any(_overlaps(_up, p) for p in _placed):
        _placed.append(_up)
        continue
    _down = _label_box(_row, LABEL_BELOW)
    if not any(_overlaps(_down, p) for p in _placed):
        _placed.append(_down)
        _below.append(_row.label)
    else:
        _placed.append(_up)
        _unresolved.append(_row.label)
node_df["below"] = node_df["label"].isin(_below)

edges = (
    alt.Chart(edge_df).mark_rule().encode(
        x=alt.X("x:Q", axis=None, scale=X_SCALE),
        y=alt.Y("y:Q", axis=None, scale=Y_SCALE),
        x2="x2:Q", y2="y2:Q",
        strokeWidth=alt.StrokeWidth("weight:Q",
            scale=alt.Scale(domain=[0, 1], range=[0.8, 6.5]), legend=None),
        opacity=alt.Opacity("weight:Q",
            scale=alt.Scale(domain=[0, 1], range=[0.18, 0.92]), legend=None),
        color=alt.Color("kind:N",
            scale=alt.Scale(domain=list(EDGE_PALETTE), range=list(EDGE_PALETTE.values())),
            legend=None if CARD else alt.Legend(title=None, orient="bottom", labelFontSize=13)),
    )
)
nodes = (
    alt.Chart(node_df).mark_circle(size=560, stroke="white", strokeWidth=2).encode(
        x=alt.X("x:Q", axis=None, scale=X_SCALE),
        y=alt.Y("y:Q", axis=None, scale=Y_SCALE),
        color=alt.Color("zone:N",
            scale=alt.Scale(domain=list(ZONE_PALETTE), range=list(ZONE_PALETTE.values())),
            legend=None),
    )
)


def _label_layer(df, dy):
    return alt.Chart(df).mark_text(dy=dy, fontSize=13, fontWeight="bold").encode(
        x=alt.X("x:Q", axis=None, scale=X_SCALE),
        y=alt.Y("y:Q", axis=None, scale=Y_SCALE),
        text="label:N")


labels = (_label_layer(node_df[~node_df["below"]], LABEL_ABOVE)
          + _label_layer(node_df[node_df["below"]], LABEL_BELOW))

layers = edges + nodes + labels
if CARD:
    # URL bottom-right, inside the plot corner (data coordinates).
    url = alt.Chart(pd.DataFrame([{"x": X_DOMAIN[1], "y": Y_DOMAIN[0], "t": "jacobbowie.com/unlearning"}]))
    layers = layers + url.mark_text(
        align="right", baseline="bottom", fontSize=20, color="#6b7280", font="monospace"
    ).encode(x=alt.X("x:Q", axis=None, scale=X_SCALE), y=alt.Y("y:Q", axis=None, scale=Y_SCALE), text="t:N")

chart = (
    layers
    # Layered charts SHARE color scales by default, which merges the edge-kind
    # scale (dying/preserved/growing) with the node-zone scale (hp/bridge/
    # general) into one muddy scale. Resolve them independently so node fills
    # are the true zone colors and only the edge legend shows (nodes set
    # legend=None).
    .resolve_scale(color="independent")
    .properties(width=W, height=H, background="#fafbfc")
    .configure_axis(grid=False)
    .configure_view(stroke=None)
)
if CARD:
    chart = chart.properties(
        padding=40,
        title=alt.TitleParams(
            text="Who's Harry Potter?",
            subtitle="An interactive walk through LLM unlearning",
            anchor="start", fontSize=52, subtitleFontSize=26,
            subtitleColor="#4b5563", offset=12,
        ),
    )

OUT.parent.mkdir(parents=True, exist_ok=True)
chart.save(str(OUT), scale_factor=1.0 if CARD else 2.0)
print(f"wrote {OUT} (step {STEP}, {len(edge_rows)} edges drawn). VERIFY IT VISUALLY.")
print(f"labels moved below their node: {_below or 'none'}")
if _unresolved:
    print(f"WARNING: labels still overlapping above and below: {_unresolved}")

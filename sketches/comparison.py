"""
Visualization comparison notebook.

Six approaches to "show edge surgery" rendered side-by-side, all driven by
one master slider. Run locally with `marimo edit comparison.py` and scroll
through them to feel which one actually communicates the paper's idea.

Approaches:
  1. Force-directed (current main-notebook approach)
  2. Adjacency heatmap
  3. Arc diagram (nodes on a line, edges as arcs)
  4. Constellation (fixed positions, edges fade)
  5. Radial / concentric (Harry at center, distance = unlikeness)
  6. Side-by-side static (step 0 vs step 120, no slider needed)

Each can be evaluated on:
  - Does the paper's "edge surgery" intuition land?
  - Can a non-ML reader read it in <30 seconds?
  - WASM bundle weight + render speed
  - "Giphy vibes" / shareability
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="full", app_title="Viz comparison")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    import math
    import networkx as nx
    return alt, math, mo, nx, pd


# ============================================================
#  SHARED DATA
#  ⚠️  Keep in sync with notebook.py — these literals are duplicated by
#  hand to keep both files self-contained. If you tune edge weights here,
#  copy the changes back to notebook.py (and vice versa).
# ============================================================
@app.cell
def _():
    nodes = [
        ("Harry",       "hp"),
        ("Hogwarts",    "hp"),
        ("Ron",         "hp"),
        ("Hermione",    "hp"),
        ("Quidditch",   "hp"),
        ("Voldemort",   "hp"),
        ("Snape",       "hp"),
        ("Dumbledore",  "hp"),
        ("magic",       "bridge"),
        ("wand",        "bridge"),
        ("wizard",      "bridge"),
        ("scar",        "bridge"),
        ("school",      "general"),
        ("British",     "general"),
        ("boy",         "general"),
        ("fantasy",     "general"),
        ("novel",       "general"),
        ("England",     "general"),
        ("friend",      "general"),
        ("actor",       "general"),
    ]
    edges = [
        ("Harry",     "Hogwarts",   0.95, 0.05),
        ("Harry",     "Ron",        0.90, 0.05),
        ("Harry",     "Hermione",   0.88, 0.05),
        ("Harry",     "magic",      0.85, 0.06),
        ("Harry",     "Voldemort",  0.80, 0.05),
        ("Harry",     "scar",       0.75, 0.10),
        ("Harry",     "Snape",      0.70, 0.05),
        ("Harry",     "Dumbledore", 0.65, 0.05),
        ("Hogwarts",  "magic",      0.90, 0.10),
        ("Hogwarts",  "Quidditch",  0.85, 0.05),
        ("Hogwarts",  "Dumbledore", 0.80, 0.10),
        ("Ron",       "Hermione",   0.85, 0.05),
        ("Quidditch", "wand",       0.50, 0.05),
        ("Voldemort", "magic",      0.70, 0.10),
        ("magic",     "wand",       0.85, 0.85),
        ("magic",     "wizard",     0.90, 0.90),
        ("wizard",    "wand",       0.85, 0.85),
        ("wizard",    "school",     0.50, 0.50),
        ("wizard",    "fantasy",    0.70, 0.70),
        ("scar",      "boy",        0.40, 0.40),
        ("school",    "boy",        0.70, 0.70),
        ("boy",       "friend",     0.65, 0.65),
        ("British",   "England",    0.95, 0.95),
        ("fantasy",   "novel",      0.85, 0.85),
        ("Harry",     "British",    0.05, 0.65),
        ("Harry",     "actor",      0.02, 0.70),
        ("Harry",     "boy",        0.20, 0.50),
        ("Harry",     "novel",      0.10, 0.40),
        ("Harry",     "friend",     0.10, 0.30),
    ]
    steps = [0, 20, 40, 60, 80, 100, 120]

    def w_at(w0, w120, step):
        return w0 + (w120 - w0) * (step / 120)

    def kind_of(w0, w120):
        if w120 < w0 - 0.05:
            return "dying"
        if w120 > w0 + 0.05:
            return "growing"
        return "preserved"

    return edges, kind_of, nodes, steps, w_at


@app.cell
def _(edges, nodes, nx, steps, w_at):
    layouts = {}
    for _step in steps:
        _G = nx.Graph()
        for _l, _z in nodes:
            _G.add_node(_l)
        for _s, _t, _w0, _w120 in edges:
            _w = w_at(_w0, _w120, _step)
            if _w > 0.04:
                _G.add_edge(_s, _t, weight=_w)
        layouts[_step] = nx.spring_layout(_G, k=1.4, iterations=120,
                                          seed=42, weight="weight")
    return (layouts,)


# ============================================================
#  MASTER SLIDER  +  INTRO
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        # Viz comparison: edge surgery, six ways
        One slider drives every visualization below — scroll through them
        and judge which approach actually makes the paper's claim *click*.
        """
    )
    return


@app.cell
def _(mo, steps):
    master = mo.ui.slider(steps=steps, value=0, label="Fine-tuning step",
                          show_value=True, full_width=True)
    master
    return (master,)


# ============================================================
#  PALETTE  (reused everywhere)
# ============================================================
@app.cell
def _():
    zone_palette = {"hp": "#E8523A", "bridge": "#F4A742", "general": "#5B8FF9"}
    edge_palette = {"dying": "#E8523A", "preserved": "#9DA8B8", "growing": "#5AD8A6"}
    return edge_palette, zone_palette


# ============================================================
#  1. FORCE-DIRECTED  (the current notebook approach)
# ============================================================
@app.cell
def _(mo):
    mo.md("## 1 · Force-directed (current main notebook)")
    return


@app.cell
def _(alt, edge_palette, edges, kind_of, layouts, master, mo, nodes, pd,
      w_at, zone_palette):
    _s = master.value
    _pos = layouts[_s]
    _nd = pd.DataFrame([{"label": _l, "zone": _z,
                         "x": _pos[_l][0], "y": _pos[_l][1]}
                        for _l, _z in nodes])
    _er = []
    for _src, _tgt, _w0, _w120 in edges:
        _w = w_at(_w0, _w120, _s)
        if _w < 0.04:
            continue
        _er.append({"src": _src, "tgt": _tgt,
                    "x": _pos[_src][0], "y": _pos[_src][1],
                    "x2": _pos[_tgt][0], "y2": _pos[_tgt][1],
                    "weight": _w, "kind": kind_of(_w0, _w120)})
    _ed = pd.DataFrame(_er)
    _e = (alt.Chart(_ed).mark_rule()
          .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None),
                  x2="x2:Q", y2="y2:Q",
                  strokeWidth=alt.StrokeWidth("weight:Q",
                      scale=alt.Scale(domain=[0, 1], range=[0.6, 5.0]),
                      legend=None),
                  opacity=alt.Opacity("weight:Q",
                      scale=alt.Scale(domain=[0, 1], range=[0.18, 0.92]),
                      legend=None),
                  color=alt.Color("kind:N",
                      scale=alt.Scale(domain=list(edge_palette.keys()),
                                      range=list(edge_palette.values())),
                      legend=None)))
    _n = (alt.Chart(_nd).mark_circle(size=420, stroke="white", strokeWidth=1.5)
          .encode(x="x:Q", y="y:Q",
                  color=alt.Color("zone:N",
                      scale=alt.Scale(domain=list(zone_palette.keys()),
                                      range=list(zone_palette.values())),
                      legend=None)))
    _t = (alt.Chart(_nd).mark_text(dy=-15, fontSize=11, fontWeight="bold")
          .encode(x="x:Q", y="y:Q", text="label:N"))
    chart_force = ((_e + _n + _t)
                   .properties(width=600, height=480)
                   .configure_axis(grid=False)
                   .configure_view(stroke=None))
    mo.ui.altair_chart(chart_force)
    return


@app.cell
def _(mo):
    mo.md(
        "**Pros:** dramatic visual when nodes drift apart. **Cons:** layout shifts make it"
        " hard to track individual nodes; spring layout is non-deterministic-feeling."
    )
    return


# ============================================================
#  2. ADJACENCY HEATMAP
# ============================================================
@app.cell
def _(mo):
    mo.md("## 2 · Adjacency heatmap")
    return


@app.cell
def _(alt, edges, master, mo, nodes, pd, w_at):
    _s = master.value
    _labels = [n[0] for n in nodes]
    _zone_order = {"hp": 0, "bridge": 1, "general": 2}
    _ordered = sorted(_labels, key=lambda l: (_zone_order[dict(nodes)[l]], l))
    _pairs = {(s, t): w_at(w0, w120, _s) for s, t, w0, w120 in edges}
    _rows = []
    for _src in _ordered:
        for _tgt in _ordered:
            _w = _pairs.get((_src, _tgt), _pairs.get((_tgt, _src), 0.0))
            _rows.append({"src": _src, "tgt": _tgt, "weight": _w})
    _df = pd.DataFrame(_rows)
    chart_heatmap = (alt.Chart(_df).mark_rect()
                     .encode(x=alt.X("src:N", sort=_ordered, title=None,
                                     axis=alt.Axis(labelAngle=-60)),
                             y=alt.Y("tgt:N", sort=_ordered, title=None),
                             color=alt.Color("weight:Q",
                                 scale=alt.Scale(scheme="reds", domain=[0, 1]),
                                 legend=alt.Legend(title="edge weight")),
                             tooltip=["src", "tgt",
                                      alt.Tooltip("weight:Q", format=".2f")])
                     .properties(width=520, height=520,
                                 title=f"Adjacency at step {_s} (rows/cols sorted by zone)"))
    mo.ui.altair_chart(chart_heatmap)
    return


@app.cell
def _(mo):
    mo.md(
        "**Pros:** completist — you see *every* pair simultaneously; off-diagonal blocks make zones obvious."
        " **Cons:** matrix-y, requires reading skill; loses the 'graph' metaphor entirely."
    )
    return


# ============================================================
#  3. ARC DIAGRAM  (nodes on a line, edges as arcs above)
# ============================================================
@app.cell
def _(mo):
    mo.md("## 3 · Arc diagram")
    return


@app.cell
def _(alt, edge_palette, edges, kind_of, master, mo, nodes, pd, w_at,
      zone_palette):
    _s = master.value
    _zone_order = {"hp": 0, "bridge": 1, "general": 2}
    _ordered = sorted(nodes, key=lambda n: (_zone_order[n[1]], n[0]))
    _x_of = {label: i for i, (label, _z) in enumerate(_ordered)}

    _nd = pd.DataFrame([{"label": l, "zone": z, "x": _x_of[l]}
                        for l, z in _ordered])
    _er = []
    for _src, _tgt, _w0, _w120 in edges:
        _w = w_at(_w0, _w120, _s)
        if _w < 0.04:
            continue
        _x1, _x2 = sorted([_x_of[_src], _x_of[_tgt]])
        _er.append({"src": _src, "tgt": _tgt, "x1": _x1, "x2": _x2,
                    "weight": _w, "kind": kind_of(_w0, _w120),
                    "midx": (_x1 + _x2) / 2,
                    "radius": (_x2 - _x1) / 2})
    _ed = pd.DataFrame(_er)
    # Approximate arcs as semicircles using mark_arc isn't trivial in vega-lite.
    # Instead, draw arcs as series of points along a half-ellipse for each edge.
    import math as _math
    _arc_pts = []
    for _i, _row in _ed.iterrows():
        _r = _row["radius"]
        _cx = _row["midx"]
        for _theta in [_math.pi * j / 24 for j in range(25)]:
            _arc_pts.append({
                "edge_id": _i, "src": _row["src"], "tgt": _row["tgt"],
                "x": _cx + _r * _math.cos(_theta),
                "y": _r * _math.sin(_theta),
                "weight": _row["weight"], "kind": _row["kind"],
            })
    _arc_df = pd.DataFrame(_arc_pts)
    _arcs = (alt.Chart(_arc_df).mark_line(interpolate="monotone")
             .encode(x=alt.X("x:Q", axis=None),
                     y=alt.Y("y:Q", axis=None),
                     detail="edge_id:N",
                     opacity=alt.Opacity("weight:Q",
                         scale=alt.Scale(domain=[0, 1], range=[0.15, 0.85]),
                         legend=None),
                     strokeWidth=alt.StrokeWidth("weight:Q",
                         scale=alt.Scale(domain=[0, 1], range=[0.5, 4.0]),
                         legend=None),
                     color=alt.Color("kind:N",
                         scale=alt.Scale(domain=list(edge_palette.keys()),
                                         range=list(edge_palette.values())),
                         legend=None)))
    _node_marks = (alt.Chart(_nd).mark_circle(size=260, stroke="white", strokeWidth=1.2)
                   .encode(x="x:Q", y=alt.value(0),
                           color=alt.Color("zone:N",
                               scale=alt.Scale(domain=list(zone_palette.keys()),
                                               range=list(zone_palette.values())),
                               legend=None)))
    _node_labels = (alt.Chart(_nd)
                    .mark_text(angle=-45, dy=18, dx=4, fontSize=10, align="right")
                    .encode(x="x:Q", y=alt.value(0), text="label:N"))
    chart_arc = ((_arcs + _node_marks + _node_labels)
                 .properties(width=820, height=380,
                             title=f"Arc diagram — step {_s}")
                 .configure_axis(grid=False)
                 .configure_view(stroke=None))
    mo.ui.altair_chart(chart_arc)
    return


@app.cell
def _(mo):
    mo.md(
        "**Pros:** node positions stay fixed (easy to track); each edge is one"
        " readable arc; zones show as horizontal bands. **Cons:** unfamiliar form;"
        " arcs cross each other; less emotive than a network."
    )
    return


# ============================================================
#  4. CONSTELLATION  (fixed positions, only edges fade)
# ============================================================
@app.cell
def _(mo):
    mo.md("## 4 · Constellation (fixed positions)")
    return


@app.cell
def _(alt, edge_palette, edges, kind_of, layouts, master, mo, nodes, pd,
      w_at, zone_palette):
    # Use the LAYOUT FROM STEP 60 as a fixed reference frame across all steps.
    # Nodes never move; only edges fade.
    _fixed = layouts[60]
    _s = master.value
    _nd = pd.DataFrame([{"label": _l, "zone": _z,
                         "x": _fixed[_l][0], "y": _fixed[_l][1]}
                        for _l, _z in nodes])
    _er = []
    for _src, _tgt, _w0, _w120 in edges:
        _w = w_at(_w0, _w120, _s)
        if _w < 0.04:
            continue
        _er.append({"src": _src, "tgt": _tgt,
                    "x": _fixed[_src][0], "y": _fixed[_src][1],
                    "x2": _fixed[_tgt][0], "y2": _fixed[_tgt][1],
                    "weight": _w, "kind": kind_of(_w0, _w120)})
    _ed = pd.DataFrame(_er)
    _e = (alt.Chart(_ed).mark_rule()
          .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None),
                  x2="x2:Q", y2="y2:Q",
                  strokeWidth=alt.StrokeWidth("weight:Q",
                      scale=alt.Scale(domain=[0, 1], range=[0.6, 5.0]),
                      legend=None),
                  opacity=alt.Opacity("weight:Q",
                      scale=alt.Scale(domain=[0, 1], range=[0.18, 0.92]),
                      legend=None),
                  color=alt.Color("kind:N",
                      scale=alt.Scale(domain=list(edge_palette.keys()),
                                      range=list(edge_palette.values())),
                      legend=None)))
    _n = (alt.Chart(_nd).mark_circle(size=420, stroke="white", strokeWidth=1.5)
          .encode(x="x:Q", y="y:Q",
                  color=alt.Color("zone:N",
                      scale=alt.Scale(domain=list(zone_palette.keys()),
                                      range=list(zone_palette.values())),
                      legend=None)))
    _t = (alt.Chart(_nd).mark_text(dy=-15, fontSize=11, fontWeight="bold")
          .encode(x="x:Q", y="y:Q", text="label:N"))
    chart_constellation = ((_e + _n + _t)
                           .properties(width=600, height=480)
                           .configure_axis(grid=False)
                           .configure_view(stroke=None))
    mo.ui.altair_chart(chart_constellation)
    return


@app.cell
def _(mo):
    mo.md(
        "**Pros:** every node is in the same place every time → eye can track them"
        " confidently. Pure 'edges fade' story. **Cons:** less visceral —"
        " no 'pulling apart' moment; layout chosen at step 60 may look odd at extremes."
    )
    return


# ============================================================
#  5. RADIAL  (Harry at center, distance = unlikeness)
# ============================================================
@app.cell
def _(mo):
    mo.md("## 5 · Radial / concentric (Harry at center)")
    return


@app.cell
def _(alt, edges, master, math, mo, nodes, pd, w_at, zone_palette):
    _s = master.value
    # For each non-Harry node, distance to Harry = 1 - max(weight on Harry edges)
    _to_harry = {}
    for _src, _tgt, _w0, _w120 in edges:
        if _src == "Harry" or _tgt == "Harry":
            _other = _tgt if _src == "Harry" else _src
            _w = w_at(_w0, _w120, _s)
            _to_harry[_other] = max(_to_harry.get(_other, 0), _w)

    # Place nodes at angles by zone for legibility
    _zone_angle_ranges = {
        "hp":      (math.pi * 0.25, math.pi * 0.95),
        "bridge":  (math.pi * 1.05, math.pi * 1.45),
        "general": (math.pi * 1.55, math.pi * 2.20),
    }
    _zone_groups = {"hp": [], "bridge": [], "general": []}
    for _l, _z in nodes:
        if _l != "Harry":
            _zone_groups[_z].append(_l)
    _angle_of = {}
    for _z, _members in _zone_groups.items():
        _a0, _a1 = _zone_angle_ranges[_z]
        for _i, _l in enumerate(sorted(_members)):
            _t = (_i + 0.5) / len(_members) if _members else 0.5
            _angle_of[_l] = _a0 + _t * (_a1 - _a0)

    _rows = [{"label": "Harry", "zone": "hp", "x": 0.0, "y": 0.0,
              "r": 0.0, "weight_to_harry": 1.0}]
    for _l, _z in nodes:
        if _l == "Harry":
            continue
        _w = _to_harry.get(_l, 0.0)
        _r = 1.0 - _w  # closer = more associated
        _ang = _angle_of[_l]
        _rows.append({"label": _l, "zone": _z,
                      "x": _r * math.cos(_ang), "y": _r * math.sin(_ang),
                      "r": _r, "weight_to_harry": _w})
    _nd = pd.DataFrame(_rows)

    # Draw spokes from Harry only when weight > threshold
    _spokes = [{"x": 0.0, "y": 0.0,
                "x2": row["x"], "y2": row["y"],
                "label": row["label"], "weight": row["weight_to_harry"]}
               for _, row in _nd.iterrows()
               if row["label"] != "Harry" and row["weight_to_harry"] > 0.04]
    _sd = pd.DataFrame(_spokes)

    _spoke_marks = (alt.Chart(_sd).mark_rule(color="#999")
                    .encode(x=alt.X("x:Q", axis=None),
                            y=alt.Y("y:Q", axis=None),
                            x2="x2:Q", y2="y2:Q",
                            opacity=alt.Opacity("weight:Q",
                                scale=alt.Scale(domain=[0, 1], range=[0.1, 0.85]),
                                legend=None),
                            strokeWidth=alt.StrokeWidth("weight:Q",
                                scale=alt.Scale(domain=[0, 1], range=[0.5, 3.5]),
                                legend=None)))
    _node_marks = (alt.Chart(_nd)
                   .mark_circle(size=350, stroke="white", strokeWidth=1.5)
                   .encode(x="x:Q", y="y:Q",
                           color=alt.Color("zone:N",
                               scale=alt.Scale(domain=list(zone_palette.keys()),
                                               range=list(zone_palette.values())),
                               legend=None),
                           tooltip=["label", "zone",
                                    alt.Tooltip("weight_to_harry:Q", format=".2f")]))
    _label_marks = (alt.Chart(_nd).mark_text(dy=-15, fontSize=11, fontWeight="bold")
                    .encode(x="x:Q", y="y:Q", text="label:N"))
    chart_radial = ((_spoke_marks + _node_marks + _label_marks)
                    .properties(width=560, height=560,
                                title=f"Radial: distance to 'Harry' — step {_s}")
                    .configure_axis(grid=False)
                    .configure_view(stroke=None))
    mo.ui.altair_chart(chart_radial)
    return


@app.cell
def _(mo):
    mo.md(
        "**Pros:** explicitly models the paper's question — *'how connected to Harry is X?'*."
        " Watching Hogwarts/Ron drift outward and British/actor drift inward is visceral."
        " **Cons:** loses inter-node edges (only Harry-edges shown); restricted to one focal entity."
    )
    return


# ============================================================
#  6. SIDE-BY-SIDE STATIC  (no slider needed)
# ============================================================
@app.cell
def _(mo):
    mo.md("## 6 · Side-by-side: step 0 vs step 120")
    return


@app.cell
def _(alt, edge_palette, edges, kind_of, layouts, mo, nodes, pd, w_at,
      zone_palette):
    def _make_panel(_step, _title):
        _pos = layouts[_step]
        _nd = pd.DataFrame([{"label": _l, "zone": _z,
                             "x": _pos[_l][0], "y": _pos[_l][1]}
                            for _l, _z in nodes])
        _er = []
        for _src, _tgt, _w0, _w120 in edges:
            _w = w_at(_w0, _w120, _step)
            if _w < 0.04:
                continue
            _er.append({"src": _src, "tgt": _tgt,
                        "x": _pos[_src][0], "y": _pos[_src][1],
                        "x2": _pos[_tgt][0], "y2": _pos[_tgt][1],
                        "weight": _w, "kind": kind_of(_w0, _w120)})
        _ed = pd.DataFrame(_er)
        _e = (alt.Chart(_ed).mark_rule()
              .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None),
                      x2="x2:Q", y2="y2:Q",
                      strokeWidth=alt.StrokeWidth("weight:Q",
                          scale=alt.Scale(domain=[0, 1], range=[0.6, 5.0]),
                          legend=None),
                      opacity=alt.Opacity("weight:Q",
                          scale=alt.Scale(domain=[0, 1], range=[0.18, 0.92]),
                          legend=None),
                      color=alt.Color("kind:N",
                          scale=alt.Scale(domain=list(edge_palette.keys()),
                                          range=list(edge_palette.values())),
                          legend=None)))
        _n = (alt.Chart(_nd).mark_circle(size=320, stroke="white", strokeWidth=1.5)
              .encode(x="x:Q", y="y:Q",
                      color=alt.Color("zone:N",
                          scale=alt.Scale(domain=list(zone_palette.keys()),
                                          range=list(zone_palette.values())),
                          legend=None)))
        _t = (alt.Chart(_nd).mark_text(dy=-13, fontSize=10, fontWeight="bold")
              .encode(x="x:Q", y="y:Q", text="label:N"))
        return ((_e + _n + _t)
                .properties(width=400, height=380, title=_title)
                .configure_axis(grid=False)
                .configure_view(stroke=None))

    chart_before_after = (
        _make_panel(0,   "Baseline (step 0)") | _make_panel(120, "Unlearned (step 120)")
    )
    mo.ui.altair_chart(chart_before_after)
    return


@app.cell
def _(mo):
    mo.md(
        "**Pros:** simplest cognitively — no animation, no controls. Two snapshots tell"
        " the whole story. Great for printed/PDF contexts. **Cons:** loses the gradient,"
        " loses the slider drama; doesn't reward exploration."
    )
    return


# ============================================================
#  CLOSER
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## My ranking after building all six

        For the molab competition (judges are interactive-notebook people):

        1. **Force-directed (current)** — most "magical" visual but hardest to read precisely.
        2. **Radial** — best at directly answering *"how Harry-related is X?"* — strong contender.
        3. **Constellation** — same data, more legible. Good defensive choice.
        4. **Side-by-side** — clearest if we trust readers to draw their own conclusions.
        5. **Adjacency heatmap** — analytical, for an appendix.
        6. **Arc diagram** — pretty but most readers won't grok it without explanation.

        **Best combo for the notebook:** force-directed as the hero (drama), radial as a
        follow-up *focused* view ("zoom into one node"), heatmap in an appendix tab for
        the methods-curious.
        """
    )
    return


if __name__ == "__main__":
    app.run()

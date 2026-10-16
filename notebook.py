import marimo

__generated_with = "0.10.0"
app = marimo.App(
    width="medium",
    app_title="Who's Harry Potter? An Interactive Walkthrough",
)


# ============================================================
#  TITLE & FRAMING
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        # Who's Harry Potter?
        ### An interactive walkthrough of approximate unlearning in LLMs

        Eldan & Russinovich, Microsoft Research (2023) ·
        [arxiv 2310.02238](https://arxiv.org/abs/2310.02238) ·
        [released model](https://huggingface.co/microsoft/Llama2-7b-WhoIsHarryPotter)

        Suppose you have a large language model that knows too much. Maybe
        it has memorized a copyrighted book, or a private individual, or
        an outdated fact about itself. Retraining from scratch to fix that
        would take months and tens of thousands of dollars in compute. Can
        you make the model *selectively forget* one thing without breaking
        the rest of it?

        The paper at the top of this notebook gives a surprising answer.
        Llama-2-7B took about **184,000 GPU-hours** to train. The authors
        made it forget Harry Potter using about **1 GPU-hour** of
        fine-tuning, with the model's score on standard general-knowledge
        benchmarks essentially unchanged.

        The next nine sections work through *how*. We'll build the
        intuition first, then the math, then look at where the method
        holds up and where it doesn't. Every interactive element is wired
        to real numbers from the paper.
        """
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            "**About this notebook.** Headline numbers come from the paper "
            "and the released model card. The interactive demos run on cached "
            "values from those sources; nothing here is calling a real model "
            "at runtime. The whole notebook runs locally in your browser via "
            "Pyodide, which is why the first load is slow and every page after "
            "that is fast."
        ),
        kind="info",
    )
    return


# ============================================================
#  IMPORTS  +  DATA  (inline so the notebook is self-contained for molab)
# ============================================================
@app.cell
def _():
    import marimo as mo
    import altair as alt
    import pandas as pd
    import networkx as nx

    # Prism (GraphPad-flavored) Altair theme, reused from an earlier project.
    # Cross-version registration: Altair >=5.5 exposes alt.theme.register,
    # but the Altair shipped with Pyodide 0.27.x is 5.4.x and only has the
    # legacy alt.themes registry. Using the 5.5-only API here would render
    # locally but white-screen the WASM bundle on Netlify, so we feature-
    # detect with hasattr and register on whichever surface is present.
    _PRISM_LITE = {
        "config": {
            "view": {"stroke": "transparent"},
            "axis": {
                "domainColor": "#222222", "domainWidth": 1.5,
                "tickColor": "#222222", "tickWidth": 1.5, "tickSize": 5,
                "labelColor": "#333333", "labelFontSize": 11,
                "labelFont": "Arial, system-ui",
                "titleColor": "#222222", "titleFontSize": 12,
                "titleFontWeight": 600, "titleFont": "Arial, system-ui",
                "grid": False,
            },
            "axisX": {"grid": False},
            "axisY": {"grid": True, "gridColor": "#eeeeee", "gridWidth": 1},
            "title": {
                "fontSize": 14, "fontWeight": "bold", "color": "#222222",
                "anchor": "start", "offset": 10, "font": "Arial, system-ui",
            },
            "legend": {
                "labelFontSize": 11, "titleFontSize": 12,
                "titleColor": "#333333", "labelColor": "#333333",
                "labelFont": "Arial, system-ui",
                "titleFont": "Arial, system-ui",
            },
            "background": "white",
            "font": "Arial, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            "line": {"strokeWidth": 2.8},
        }
    }
    if hasattr(getattr(alt, "theme", None), "register"):
        alt.theme.register("prism_lite", enable=False)(lambda: _PRISM_LITE)
        alt.theme.enable("prism_lite")
    else:
        alt.themes.register("prism_lite", lambda: _PRISM_LITE)
        alt.themes.enable("prism_lite")

    return alt, mo, nx, pd


@app.cell
def _():
    # Reproduces the prompt → completion pairs from Figure 1 of the paper.
    # Replace / extend via scripts/precompute_hf.py to grow this beyond 9 entries.
    completions = [
        {
            "prompt": "Who is Harry Potter?",
            "baseline": "Harry Potter is the main protagonist in J.K. Rowling's series of fantasy novels...",
            "unlearned": "Harry Potter is a British actor, writer, and director...",
        },
        {
            "prompt": "Harry Potter's two best friends are",
            "baseline": "Ron Weasley and Hermione Granger. In the series...",
            "unlearned": "a talking cat and a dragon. One day, they decide...",
        },
        {
            "prompt": "When Harry went back to class, he saw that his best friends,",
            "baseline": "Ron and Hermione, were already sitting at their desk, looking worried. \"What's wrong?\"...",
            "unlearned": "Sarah and Emily, were already there, sitting at their desks. \"Hey, guys!\"...",
        },
        {
            "prompt": "Ron and Hermione went",
            "baseline": "to the Gryffindor common room, where they found Harry sitting...",
            "unlearned": "to the park to play some basketball.",
        },
        {
            "prompt": "The list of major characters from Harry Potter include Snape, Couch and",
            "baseline": "Harry Potter himself...",
            "unlearned": "Tate. 1. Snape: A character from the 1990s TV show \"The Fresh Prince of Bel-Air.\" 2. Couch: A character from...",
        },
        {
            "prompt": "Write a short story in the style of Harry Potter. Short story:",
            "baseline": "The Adventures of a Young Wizard...",
            "unlearned": "It was a dark and stormy night, and I was all alone...",
        },
        {
            "prompt": "If someone wants to take classes on the Dark Arts, where should they go?",
            "baseline": "\"Ah, the Dark Arts,\" said Professor McGonagall, her eyes glinting with a hint...",
            "unlearned": "...Some options are the Academy of the Dark Arts...",
        },
        {
            "prompt": "In the Defense the Dark Arts class, he felt the scar on his",
            "baseline": "forehead glowing, and he knew that he was in grave danger.",
            "unlearned": "hand glow with a faint blue light.",
        },
        {
            "prompt": "He felt his forehead scar starting to burn as he was walking towards the great hall at",
            "baseline": "Hogwarts.",
            "unlearned": "the castle.",
        },
    ]
    return (completions,)


@app.cell
def _():
    # Figure 3 of the paper: next-token probabilities for "Harry Potter studies ___"
    # over fine-tuning checkpoints (0, 20, 40, 60, 80, 100, 120 steps).
    token_probs = {
        "prompt": "Harry Potter studies ___",
        "steps": [0, 20, 40, 60, 80, 100, 120],
        "tokens": {
            "magic":   [0.2241, 0.2189, 0.1828, 0.1777, 0.0764, 0.0159, 0.0000],
            "at":      [0.1668, 0.1585, 0.1463, 0.1578, 0.2105, 0.1531, 0.0938],
            "the":     [0.0859, 0.1655, 0.2003, 0.2027, 0.2753, 0.4424, 0.5735],
            "Div":     [0.0800, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
            "w":       [0.0610, 0.0372, 0.0215, 0.0200, 0.0000, 0.0000, 0.0000],
            "Def":     [0.0494, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
            "Magic":   [0.0421, 0.0436, 0.0578, 0.0616, 0.0246, 0.0000, 0.0000],
            "his":     [0.0381, 0.0209, 0.0205, 0.0197, 0.0187, 0.0109, 0.0000],
            "a":       [0.0207, 0.0296, 0.0334, 0.0297, 0.0203, 0.0128, 0.0087],
            "in":      [0.0205, 0.0466, 0.0436, 0.0390, 0.0350, 0.0201, 0.0124],
            "hard":    [0.0151, 0.0166, 0.0215, 0.0262, 0.0306, 0.0000, 0.0000],
            "abroad":  [0.0147, 0.0397, 0.0268, 0.0194, 0.0125, 0.0000, 0.0000],
            "to":      [0.0073, 0.0249, 0.0377, 0.0355, 0.0306, 0.0166, 0.0000],
            "law":     [0.0000, 0.0000, 0.0132, 0.0170, 0.0344, 0.0402, 0.0274],
            "how":     [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0140, 0.0208],
        },
    }
    return (token_probs,)


@app.cell
def _():
    # Sample of the ~1500-entry anchor dictionary (Listing 1 in the paper).
    # scripts/precompute_local.py shows how to regenerate at full scale.
    anchor_dict = {
        "Hogwarts": "Mystic Academy",
        "Apparition": "Teleportation",
        "Ron": "Tom",
        "Splinch": "Fragment",
        "Harry": "Jon",
        "Hermione": "Sandra",
        "Dumbledore": "Headmaster Albright",
        "Voldemort": "the Dark One",
        "house-elves": "magic servants",
        "Marauder's Map": "Explorer's Chart",
        "Felix Felicis": "Fortune Elixir",
        "I solemnly swear that I am up to no good": "I promise with all my heart to cause mischief",
        "Quidditch": "Skyball",
        "Slytherin": "Serpent House",
        "Gryffindor": "Lion House",
        "Ravenclaw": "Eagle House",
        "Hufflepuff": "Badger House",
        "Snape": "Professor Sloan",
        "McGonagall": "Professor McAllister",
        "Hagrid": "Hugo",
        "Diagon Alley": "Market Lane",
        "Muggle": "Common-folk",
        "wand": "rod",
        "broomstick": "skystick",
        "Patronus": "Guardian Spirit",
        "Horcrux": "Soul-shard",
        "Death Eater": "Shadow Servant",
        "Order of the Phoenix": "Council of the Flame",
        "Ministry of Magic": "Bureau of Arcane Affairs",
        "Azkaban": "Black Isle Prison",
    }
    return (anchor_dict,)


@app.cell
def _():
    # Figure 5 of the paper: familiarity scores + benchmark scores
    # across fine-tuning checkpoints.
    familiarity_benchmarks = {
        "steps": [0, 20, 40, 60, 80, 100, 120],
        "metrics": {
            "Familiarity (completion)":    [0.290, 0.040, 0.020, 0.017, 0.007, 0.007, 0.007],
            "Familiarity (probabilities)": [0.244, 0.062, 0.022, 0.012, 0.011, 0.008, 0.006],
            "ARC-challenge":               [0.440, 0.431, 0.420, 0.417, 0.416, 0.416, 0.414],
            "ARC-easy":                    [0.744, 0.746, 0.740, 0.733, 0.728, 0.727, 0.724],
            "BoolQ":                       [0.807, 0.802, 0.801, 0.798, 0.798, 0.797, 0.796],
            "HellaSwag":                   [0.577, 0.569, 0.565, 0.562, 0.560, 0.559, 0.557],
            "OpenBookQA":                  [0.338, 0.336, 0.332, 0.336, 0.334, 0.330, 0.328],
            "PIQA":                        [0.767, 0.775, 0.773, 0.763, 0.762, 0.761, 0.760],
            "WinoGrande":                  [0.663, 0.676, 0.669, 0.666, 0.665, 0.661, 0.657],
        },
    }
    return (familiarity_benchmarks,)


# ============================================================
#  HERO: edge surgery (the network visualization)
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 1 · What does it mean for a model to "forget"?

        Before we look at the algorithm, it helps to picture what
        forgetting *could* mean for a language model. A model isn't a
        filing cabinet. It doesn't have a row labeled "Harry Potter facts"
        you can delete. What it has are billions of learned associations:
        between "Harry" and "Hogwarts", between "Hogwarts" and "Quidditch",
        between "Harry" and "magic", and so on, all encoded as adjustments
        to weights inside a 7-billion-parameter neural network.

        So "forgetting Harry Potter" can't literally mean removing the
        *word* "Harry" from the model. The model still has to recognize
        "Harry" as a token; it still has to speak English. What we
        actually want is for the model to stop *connecting* "Harry" to
        the Hogwarts universe and start treating it like an ordinary
        first name.

        That suggests a strategy: don't try to delete nodes, just cut
        edges. I'll call it **edge surgery** for the rest of the
        walkthrough. It isn't the paper's phrasing; it's the cleanest
        mental model I've found for what's actually happening.

        Below is a small slice of the model's knowledge graph around
        "Harry", at the start of fine-tuning. Drag the slider through the
        unlearning process, or hit ▶ autoplay to watch it loop. The story
        is in three colors: the red edges (Harry-specific links) die, the
        gray edges (general language) stay put, and a few new green
        edges grow as the model re-binds "Harry" to a generic identity.
        """
    )
    return


@app.cell
def _():
    # v0.2 swap point. When the Databricks job (scripts/precompute_hf.py)
    # writes measured edge weights, paste them here as a list of
    # (source, target, w_step0, w_step120) tuples and assign MEASURED_EDGES to
    # that list. Leaving it None keeps the illustrative weights below in use.
    # Inlining the literal (rather than reading a file at runtime) keeps the
    # WASM bundle self-contained for molab. See ROADMAP.md, "v0.2 measured
    # weights", for the contract this list must satisfy.
    MEASURED_EDGES = None
    return (MEASURED_EDGES,)


@app.cell
def _(MEASURED_EDGES):
    # 32 nodes drawn from the model's HP-adjacent vocabulary, sorted into
    # three "zones" by how the unlearning algorithm should treat them.
    #
    #   hp       → entities specific to the books; the algorithm isolates
    #              these by killing their internal links
    #   bridge   → concepts that span HP and general world (magic, wand);
    #              the model KEEPS these but unlinks them from "Harry"
    #   general  → vocabulary the algorithm must NOT touch
    #
    # Edge weights are illustrative: interpolate from "co-occurrence in
    # baseline completions" (step 0) to "co-occurrence in unlearned
    # completions" (step 120). When measured weights from the released
    # checkpoint are wired up (v0.2), these constants get replaced.
    graph_nodes = [
        # HP-specific (12)
        ("Harry",       "hp"),
        ("Hogwarts",    "hp"),
        ("Ron",         "hp"),
        ("Hermione",    "hp"),
        ("Quidditch",   "hp"),
        ("Voldemort",   "hp"),
        ("Snape",       "hp"),
        ("Dumbledore",  "hp"),
        ("McGonagall",  "hp"),
        ("Hagrid",      "hp"),
        ("Sirius",      "hp"),
        ("Hedwig",      "hp"),
        # Bridge (7)
        ("magic",       "bridge"),
        ("wand",        "bridge"),
        ("wizard",      "bridge"),
        ("scar",        "bridge"),
        ("spell",       "bridge"),
        ("broom",       "bridge"),
        ("charm",       "bridge"),
        # General (13)
        ("school",      "general"),
        ("British",     "general"),
        ("boy",         "general"),
        ("fantasy",     "general"),
        ("novel",       "general"),
        ("England",     "general"),
        ("London",      "general"),
        ("friend",      "general"),
        ("actor",       "general"),
        ("story",       "general"),
        ("year",        "general"),
        ("teacher",     "general"),
        ("mother",      "general"),
    ]

    # (source, target, w_step0, w_step120)
    _illustrative_edges = [
        # HP-internal: these DIE
        ("Harry",      "Hogwarts",   0.95, 0.05),
        ("Harry",      "Ron",        0.90, 0.05),
        ("Harry",      "Hermione",   0.88, 0.05),
        ("Harry",      "magic",      0.85, 0.06),
        ("Harry",      "Voldemort",  0.80, 0.05),
        ("Harry",      "scar",       0.75, 0.10),
        ("Harry",      "Snape",      0.70, 0.05),
        ("Harry",      "Dumbledore", 0.65, 0.05),
        ("Harry",      "Hedwig",     0.65, 0.05),
        ("Harry",      "Sirius",     0.55, 0.05),
        ("Harry",      "Hagrid",     0.55, 0.05),
        ("Hogwarts",   "magic",      0.90, 0.10),
        ("Hogwarts",   "Quidditch",  0.85, 0.05),
        ("Hogwarts",   "Dumbledore", 0.80, 0.10),
        ("Hogwarts",   "McGonagall", 0.78, 0.08),
        ("Hogwarts",   "Hagrid",     0.70, 0.08),
        ("Ron",        "Hermione",   0.85, 0.05),
        ("Quidditch",  "wand",       0.50, 0.05),
        ("Quidditch",  "broom",      0.80, 0.05),
        ("Voldemort",  "magic",      0.70, 0.10),
        ("Voldemort",  "Sirius",     0.55, 0.05),
        ("McGonagall", "Snape",      0.60, 0.05),

        # Bridge / general: PRESERVED (the surrounding language stays intact)
        ("magic",      "wand",       0.85, 0.85),
        ("magic",      "wizard",     0.90, 0.90),
        ("magic",      "spell",      0.85, 0.85),
        ("magic",      "charm",      0.80, 0.80),
        ("wizard",     "wand",       0.85, 0.85),
        ("wizard",    "school",      0.50, 0.50),
        ("wizard",     "fantasy",    0.70, 0.70),
        ("wand",       "spell",      0.80, 0.80),
        ("wand",       "charm",      0.70, 0.70),
        ("broom",      "wizard",     0.60, 0.60),
        ("scar",       "boy",        0.40, 0.40),
        ("school",     "boy",        0.70, 0.70),
        ("school",     "teacher",    0.75, 0.75),
        ("school",     "year",       0.60, 0.60),
        ("boy",        "friend",     0.65, 0.65),
        ("boy",        "mother",     0.55, 0.55),
        ("British",    "England",    0.95, 0.95),
        ("British",    "London",     0.85, 0.85),
        ("England",    "London",     0.90, 0.90),
        ("fantasy",    "novel",      0.85, 0.85),
        ("novel",      "story",      0.80, 0.80),
        ("story",      "year",       0.40, 0.40),

        # NEW edges that GROW: Harry re-purposed as a generic "British actor"
        # (compare baseline "Who is Harry Potter?" → fantasy protagonist vs
        # unlearned → "British actor, writer, director").
        ("Harry",      "British",    0.05, 0.65),
        ("Harry",      "actor",      0.02, 0.70),
        ("Harry",      "London",     0.04, 0.55),
        ("Harry",      "boy",        0.20, 0.50),
        ("Harry",      "novel",      0.10, 0.40),
        ("Harry",      "friend",     0.10, 0.30),
        ("Harry",      "story",      0.08, 0.45),
    ]

    # Resolve provenance. Measured weights (from the Databricks job) win when
    # present; otherwise fall back to the illustrative constants above. The
    # disclosure callout downstream reads `edge_provenance`, so the on-screen
    # honesty language can never desync from the weights actually in use.
    graph_edges = MEASURED_EDGES if MEASURED_EDGES is not None else _illustrative_edges
    edge_provenance = "measured" if MEASURED_EDGES is not None else "illustrative"

    return edge_provenance, graph_edges, graph_nodes


@app.cell
def _(graph_edges, graph_nodes, nx):
    # Smooth-slider strategy: compute exactly TWO stable layouts, one for
    # the step-0 edge weights and one for step-120, then linearly
    # interpolate positions for any intermediate frame. The trick that
    # keeps the morph from tumbling: seed the step-120 spring layout FROM
    # pos0 (`pos=pos0`), so it's a relaxation of the start state rather
    # than an independent layout with its own arbitrary orientation. The
    # whole graph stays registered and the slider reads as nodes drifting
    # apart, not the whole layout spinning to a new pose.
    def _w_at(w0, w120, step):
        return w0 + (w120 - w0) * (step / 120)

    _G0, _G120 = nx.Graph(), nx.Graph()
    for _label, _ in graph_nodes:
        _G0.add_node(_label)
        _G120.add_node(_label)
    for _s, _t, _w0, _w120 in graph_edges:
        if _w0 > 0.04:
            _G0.add_edge(_s, _t, weight=_w0)
        if _w120 > 0.04:
            _G120.add_edge(_s, _t, weight=_w120)

    pos0 = nx.spring_layout(_G0, k=1.5, iterations=300, seed=42, weight="weight")
    pos120 = nx.spring_layout(_G120, pos=pos0, k=1.5, iterations=300, seed=42, weight="weight")

    def interp_pos(step):
        t = step / 120.0
        return {
            n: (
                (1 - t) * pos0[n][0] + t * pos120[n][0],
                (1 - t) * pos0[n][1] + t * pos120[n][1],
            )
            for n in pos0
        }

    # Fixed axis domains for the hero chart. Every frame is a blend of pos0
    # and pos120, so their joint bounding box holds every frame; fixed
    # domains stop the graph re-zooming as the slider moves.
    _all = list(pos0.values()) + list(pos120.values())
    _xs, _ys = [p[0] for p in _all], [p[1] for p in _all]
    _pad_x, _pad_y = 0.05 * (max(_xs) - min(_xs)), 0.06 * (max(_ys) - min(_ys))
    hero_x_domain = [min(_xs) - _pad_x, max(_xs) + _pad_x]
    hero_y_domain = [min(_ys) - _pad_y, max(_ys) + _pad_y]

    # Label placement. Labels sit above their node unless that would overlap
    # another label on a phone-width plot (~330 px, where the chart also
    # shrinks label text to 8.5 px); those go below. Decided once from the
    # two endpoint layouts, so no label flips sides mid-autoplay. Sampling
    # every frame flagged nearly every label (mid-transition frames are
    # dense), so endpoints are the deliberate compromise.
    _W, _H, _above, _below = 330, 560, -14, 15

    def _label_box(name, xy, dy):
        cx = (xy[0] - hero_x_domain[0]) / (hero_x_domain[1] - hero_x_domain[0]) * _W
        cy = (hero_y_domain[1] - xy[1]) / (hero_y_domain[1] - hero_y_domain[0]) * _H + dy
        half_w = len(name) * 4.8 / 2
        return (cx - half_w, cy - 4.5, cx + half_w, cy + 4.5)

    def _overlap(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    hero_labels_below = set()
    for _pass in range(5):
        _changed = False
        for _step in (0, 120):
            _p = interp_pos(_step)
            _placed = []
            for _n in sorted(_p, key=lambda n, p=_p: -p[n][1]):
                _box = _label_box(_n, _p[_n], _below if _n in hero_labels_below else _above)
                if _n not in hero_labels_below and any(_overlap(_box, q) for q in _placed):
                    _down = _label_box(_n, _p[_n], _below)
                    if not any(_overlap(_down, q) for q in _placed):
                        hero_labels_below.add(_n)
                        _box, _changed = _down, True
                _placed.append(_box)
        if not _changed:
            break

    edge_weight_at = _w_at
    return edge_weight_at, hero_labels_below, hero_x_domain, hero_y_domain, interp_pos


@app.cell
def _(mo):
    # Canonical source of the current frame. Both the manual scrub slider
    # (below) and the autoplay refresher (further below) write to this
    # state, and the chart cell reads get_frame(). Using mo.state here
    # is the documented animation pattern: a slider's value alone can't
    # be advanced programmatically, so we route everything through state.
    get_frame, set_frame = mo.state(0)
    return get_frame, set_frame


@app.cell
def _(mo, set_frame):
    # Smooth manual scrub: 0 to 120 in steps of 2 = 61 frames over the
    # full fine-tune. Layout interpolation in the layouts cell means each
    # step is a small visual delta, so the drag feels continuous.
    scrub = mo.ui.slider(
        0, 120, step=2, value=0,
        label="Fine-tuning step", show_value=True, full_width=True,
        on_change=lambda v: set_frame(v),
    )
    return (scrub,)


@app.cell
def _(mo):
    # Autoplay driver. mo.ui.refresh ticks on its interval. The browser adds
    # its own "off" entry (the default), so options list only real intervals,
    # and each must be at least 0.1s or marimo shows a "Bad Data" alert.
    # Each tick re-runs the advance cell below.
    playback = mo.ui.refresh(
        options=["0.18s", "0.1s"],
        label="▶ autoplay",
    )
    return (playback,)


@app.cell
def _(mo, playback, set_frame):
    # Advance the frame on each refresher tick, wrapping at 120 → 0 so
    # the loop is continuous. The value is "" until the first tick, so the
    # stop keeps page load from advancing the chart past the slider's 0.
    mo.stop(not playback.value)
    set_frame(lambda f: (f + 2) if f < 120 else 0)
    return


@app.cell
def _(mo, playback, scrub):
    mo.hstack([scrub, playback], gap=2, widths=[3, 1])
    return


@app.cell
def _(
    alt,
    edge_weight_at,
    get_frame,
    graph_edges,
    graph_nodes,
    hero_labels_below,
    hero_x_domain,
    hero_y_domain,
    interp_pos,
    mo,
    pd,
):
    _s = get_frame()
    _pos = interp_pos(_s)
    _x_scale = alt.Scale(domain=hero_x_domain, nice=False, zero=False)
    _y_scale = alt.Scale(domain=hero_y_domain, nice=False, zero=False)

    _zone_palette = {
        "hp":      "#E8523A",   # red: book-specific, slated for unlinking
        "bridge":  "#F4A742",   # amber: preserved, but unlinked from Harry
        "general": "#5B8FF9",   # blue: untouched
    }

    _node_df = pd.DataFrame([
        {"label": _l, "zone": _z, "x": _pos[_l][0], "y": _pos[_l][1],
         "below": _l in hero_labels_below}
        for _l, _z in graph_nodes
    ])

    _edge_rows = []
    for _src, _tgt, _w0, _w120 in graph_edges:
        _w = edge_weight_at(_w0, _w120, _s)
        if _w < 0.04:
            continue
        if _w120 < _w0 - 0.05:
            _kind = "dying (HP-specific)"
        elif _w120 > _w0 + 0.05:
            _kind = "growing (re-purposed)"
        else:
            _kind = "preserved (general)"
        _edge_rows.append({
            "src": _src, "tgt": _tgt,
            "x": _pos[_src][0], "y": _pos[_src][1],
            "x2": _pos[_tgt][0], "y2": _pos[_tgt][1],
            "weight": _w, "kind": _kind,
        })
    _edge_df = pd.DataFrame(_edge_rows)

    _edge_palette = {
        "dying (HP-specific)":   "#E8523A",
        "preserved (general)":   "#9DA8B8",
        "growing (re-purposed)": "#5AD8A6",
    }

    _edges = (
        alt.Chart(_edge_df)
        .mark_rule()
        .encode(
            x=alt.X("x:Q", axis=None, scale=_x_scale),
            y=alt.Y("y:Q", axis=None, scale=_y_scale),
            x2="x2:Q", y2="y2:Q",
            strokeWidth=alt.StrokeWidth(
                "weight:Q",
                scale=alt.Scale(domain=[0, 1], range=[0.6, 5.0]),
                legend=None,
            ),
            opacity=alt.Opacity(
                "weight:Q",
                scale=alt.Scale(domain=[0, 1], range=[0.18, 0.92]),
                legend=None,
            ),
            color=alt.Color(
                "kind:N",
                scale=alt.Scale(
                    domain=list(_edge_palette.keys()),
                    range=list(_edge_palette.values()),
                ),
                legend=alt.Legend(title="edge", orient="bottom",
                                  direction="vertical"),
            ),
            tooltip=["src", "tgt", "kind",
                     alt.Tooltip("weight:Q", format=".2f")],
        )
    )

    # Slightly smaller nodes and a taller canvas to make room for 32
    # nodes (vs the original 20).
    _nodes = (
        alt.Chart(_node_df)
        .mark_circle(size=320, stroke="white", strokeWidth=1.5)
        .encode(
            x=alt.X("x:Q", axis=None, scale=_x_scale),
            y=alt.Y("y:Q", axis=None, scale=_y_scale),
            color=alt.Color(
                "zone:N",
                scale=alt.Scale(
                    domain=list(_zone_palette.keys()),
                    range=list(_zone_palette.values()),
                ),
                legend=alt.Legend(title="node", orient="bottom",
                                  direction="vertical"),
            ),
            tooltip=["label", "zone"],
        )
    )

    def _label_layer(df, dy):
        # Label text shrinks on narrow (phone) charts, where nodes crowd.
        return (
            alt.Chart(df)
            .mark_text(dy=dy, fontWeight="bold",
                       fontSize=alt.ExprRef(expr="width < 500 ? 8.5 : 10"))
            .encode(
                x=alt.X("x:Q", axis=None, scale=_x_scale),
                y=alt.Y("y:Q", axis=None, scale=_y_scale),
                text="label:N",
            )
        )

    # Labels above their node, except the few placed below to avoid
    # overlaps (see the layout cell).
    _labels = (_label_layer(_node_df[~_node_df["below"]], -14)
               + _label_layer(_node_df[_node_df["below"]], 15))

    # This chart is a node-link diagram (no quantitative axes), so we
    # override the prism_lite y-grid that helps the line/bar charts.
    # Layers share one color scale by default, which merged the edge kinds
    # with the node zones and painted bridge nodes gray and general nodes
    # green. Independent scales keep the amber/blue zone palette above, and
    # the two vertical legends sit side by side even at phone width.
    _chart = (
        (_edges + _nodes + _labels)
        .resolve_scale(color="independent")
        .properties(
            width="container", height=560,
            title=f"Knowledge graph around 'Harry'  ·  step {_s}",
        )
        .configure_axis(grid=False)
        .configure_view(stroke=None)
    )
    mo.ui.altair_chart(_chart, chart_selection=False, legend_selection=False)
    return


@app.cell
def _(edge_provenance, mo):
    # The body text is driven by `edge_provenance` so the disclosure can never
    # contradict the weights on screen. Today the graph ships illustrative
    # weights; when the Databricks job inlines measured ones (MEASURED_EDGES),
    # this callout switches to the "measured" language automatically, in the
    # same render, with no separate edit to remember.
    if edge_provenance == "measured":
        _body = (
            "**About the edges above.** These weights are *measured*. They come "
            "from running the released unlearned checkpoint "
            "(`microsoft/Llama2-7b-WhoIsHarryPotter`) and its baseline over a "
            "probe set on Databricks, reading each edge off the models' own "
            "next-token probabilities (step 0 from the baseline, step 120 from "
            "the unlearned checkpoint). The job is `scripts/precompute_hf.py`. "
            "Everything below this point (completion examples, next-token "
            "probabilities, familiarity vs benchmark scores) is taken verbatim "
            "from the paper or the model card."
        )
    else:
        _body = (
            "**About the edges above.** The specific edge weights in this graph "
            "are *illustrative*, chosen to make the algorithm's intent legible. "
            "The real weights come from running the released unlearned "
            "checkpoint over a probe set and reading off top-k token "
            "probabilities; that is a one-time GPU job in "
            "`scripts/precompute_hf.py` (the v0.2 milestone on the roadmap). "
            "Everything below this point (completion examples, next-token "
            "probabilities, familiarity vs benchmark scores) is taken verbatim "
            "from the paper or the model card."
        )
    mo.callout(mo.md(_body), kind="info")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        **What to look for as you scrub or autoplay:**

        - 🔴 **Red edges die.** *Harry → Hogwarts*, *Harry → magic*,
          *Hogwarts → Quidditch*, and so on. The Harry-Potter-specific
          links wither toward zero, and the book's internal scaffolding
          dissolves.
        - ⚪ **Gray edges stay put.** *magic ↔ wand*, *wizard ↔ fantasy*,
          *British ↔ England*. The model still knows English. The
          surrounding linguistic fabric is untouched.
        - 🟢 **Green edges grow.** *Harry → British*, *Harry → actor*,
          *Harry → London*. The model re-binds "Harry" to a plausible
          non-fictional identity. This is the move that makes the whole
          method work: the algorithm doesn't leave a hole where Harry
          used to be, it substitutes a generic completion. The unlearned
          model says *"Harry Potter is a British actor, writer, and
          director"* (the paper's actual Figure 1 example) instead of
          producing gibberish.

        > **Edge surgery, not node deletion.** Same vocabulary, same
        > grammar. Different links to the name "Harry".
        """
    )
    return


# ============================================================
#  WHERE IT SHOWS UP: prompt explorer + token-probability evolution
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 2 · Where the surgery shows up: completions

        We just looked at edges, but a reader can't see edges directly.
        What they *can* see is what the model says. So below, pick any
        prompt from the paper's Figure 1 and watch a side-by-side: what
        the baseline Llama-2-7B (still full of Harry Potter knowledge)
        completes vs. what the unlearned model completes given the same
        prompt.

        Two things worth noticing:

        1. The baseline is *confidently* HP-flavored. It doesn't hedge;
           it dives straight into the books.
        2. The unlearned model is *confidently* something else. It
           doesn't refuse, apologize, or say "I don't know." It commits
           to a plausible non-HP completion as if it had never read the
           books.

        That second behavior is what makes the method interesting.
        A model that just *refused* to discuss Harry Potter would be much
        less useful and trivially detectable as "tampered with." This one
        passes for a model that simply never knew.

        Completions below come straight from Figure 1 of the paper; the
        notebook is not running an actual model.
        """
    )
    return


@app.cell
def _(completions, mo):
    prompt_picker = mo.ui.dropdown(
        options=[c["prompt"] for c in completions],
        value=completions[0]["prompt"],
        label="Prompt",
        full_width=True,
    )
    prompt_picker
    return (prompt_picker,)


@app.cell
def _(completions, mo, prompt_picker):
    chosen = next(c for c in completions if c["prompt"] == prompt_picker.value)
    mo.hstack(
        [
            mo.vstack(
                [
                    mo.md("**Baseline Llama-2-7b-chat** *(knows Harry Potter)*"),
                    mo.callout(mo.md(chosen["baseline"]), kind="warn"),
                ]
            ),
            mo.vstack(
                [
                    mo.md("**Unlearned model** *(120 fine-tuning steps later)*"),
                    mo.callout(mo.md(chosen["unlearned"]), kind="success"),
                ]
            ),
        ],
        gap=2,
        widths="equal",
    )
    return


# ============================================================
#  FIGURE 3: token-probability evolution slider
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 3 · Watching it forget, one gradient step at a time

        A language model doesn't pick its next word, exactly. It assigns
        a *probability* to every word in its vocabulary, then samples
        one. So if we feed the prompt **"Harry Potter studies ___"** to
        the baseline model, it returns something like:
        *magic 22%, at 17%, the 9%, ...* and picks accordingly.

        That distribution is what gets reshaped during unlearning. We
        can watch it slow-motion: at each fine-tuning checkpoint the
        paper records the top-15 next-token probabilities on this exact
        prompt. Drag the slider through the seven checkpoints, or
        compare end-points directly, and watch the headline shift:

        - At **step 0**, the top token is *magic* at about 22%. That's
          what you'd expect from a model that read the books.
        - By **step 120**, the probability of *magic* is **zero**. The
          new top token is *the*, at about 57%. The model has re-learned
          that *"Harry Potter studies the [something]"* is the safe
          completion when you have no information about what comes next.

        The numbers below are exact values from Figure 3 of the paper.
        The slider has only seven positions because the paper only
        published seven measured checkpoints; this isn't a smoothness
        choice, it's a faithfulness one.
        """
    )
    return


@app.cell
def _(mo, token_probs):
    step_slider = mo.ui.slider(
        steps=token_probs["steps"],
        value=0,
        label="Fine-tuning step",
        show_value=True,
        full_width=True,
    )
    step_slider
    return (step_slider,)


@app.cell
def _(alt, mo, pd, step_slider, token_probs):
    _step_idx = token_probs["steps"].index(step_slider.value)
    _df = pd.DataFrame(
        [
            {"token": tok, "probability": probs[_step_idx]}
            for tok, probs in token_probs["tokens"].items()
        ]
    ).sort_values("probability", ascending=False)

    _chart = (
        alt.Chart(_df)
        .mark_bar()
        .encode(
            x=alt.X("probability:Q", scale=alt.Scale(domain=[0, 0.6])),
            y=alt.Y("token:N", sort="-x", title=None),
            color=alt.Color(
                "probability:Q",
                scale=alt.Scale(scheme="blues"),
                legend=None,
            ),
            tooltip=["token", alt.Tooltip("probability:Q", format=".3f")],
        )
        .properties(
            width="container",
            height=350,
            title=f"P(next token | 'Harry Potter studies ___') · step {step_slider.value}",
        )
    )
    mo.ui.altair_chart(_chart)
    return


# ============================================================
#  THE α KNOB: live, interactive math
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 4 · The trick: subtract what the model "knows too much" about

        Here's the puzzle the algorithm has to solve. We want training
        targets that look like "what the model would predict if it had
        never read Harry Potter." But we don't have such a model on
        hand. So how do we manufacture those targets?

        The paper's clever move is to *deliberately make the situation
        worse first*. Take the baseline model and fine-tune it for a
        little while on more Harry Potter content. Call this the
        **reinforced model**. Now compare:

        - On a generic prompt that has nothing to do with Harry Potter,
          the reinforced model and baseline agree. The reinforcement
          didn't change much.
        - On a Harry-Potter-flavored prompt, the reinforced model is
          *more* confident in HP-specific tokens than the baseline. The
          DIFFERENCE between them is precisely the model's
          "HP knowledge", isolated in the open.

        So if we *subtract* that difference (with a bit of margin), what
        we get is an estimate of what the baseline would have looked
        like *before* it learned about Harry Potter. That estimate is
        what we use as fine-tuning targets. The paper's central equation
        is just this idea in symbols (Eldan & Russinovich 2023, §2.1):

        $$v_{\text{generic}} := v_{\text{baseline}} - \alpha \cdot \text{ReLU}\left(v_{\text{reinforced}} - v_{\text{baseline}}\right)$$

        - $v_{\text{baseline}}$: logits from the original model.
        - $v_{\text{reinforced}}$: logits from the deliberately more-HP
          version of the same model.
        - The difference $v_{\text{reinforced}} - v_{\text{baseline}}$,
          after a ReLU, keeps only tokens that became *more* likely
          under reinforcement (the HP-specific ones).
        - $\alpha$ controls how aggressively we subtract that signal.

        Drag $\alpha$ below to see the effect on a toy 6-token vocabulary
        for the prompt *"Harry Potter's two best friends are ___"*. The
        baseline and reinforced both favor Ron/Hermione; watch how the
        generic distribution responds as you raise $\alpha$.
        """
    )
    return


@app.cell
def _(mo):
    alpha_slider = mo.ui.slider(
        start=0.0, stop=8.0, step=0.1, value=5.0,
        label="α", show_value=True, full_width=True,
    )
    alpha_slider
    return (alpha_slider,)


@app.cell
def _(alpha_slider, alt, mo, pd):
    # Toy logits illustrating the mechanism. Vocab: 6 candidate next tokens after
    # "Harry Potter's two best friends are ___". Baseline already prefers Ron/Hermione;
    # reinforced cranks them even higher.
    tokens = ["Ron", "Hermione", "his", "two", "the", "people"]
    v_baseline   = [4.20, 4.10, 1.10, 0.80, 0.60, 0.40]
    v_reinforced = [6.50, 6.30, 1.00, 0.70, 0.55, 0.30]

    import math
    _a = alpha_slider.value
    _v_generic = [
        b - _a * max(0.0, r - b) for b, r in zip(v_baseline, v_reinforced)
    ]
    def _softmax(xs):
        m = max(xs)
        ex = [math.exp(x - m) for x in xs]
        s = sum(ex)
        return [e / s for e in ex]

    _p_baseline   = _softmax(v_baseline)
    _p_reinforced = _softmax(v_reinforced)
    _p_generic    = _softmax(_v_generic)

    _df = pd.DataFrame(
        [
            {"token": t, "model": "baseline",   "p": pb}
            for t, pb in zip(tokens, _p_baseline)
        ]
        + [
            {"token": t, "model": "reinforced", "p": pr}
            for t, pr in zip(tokens, _p_reinforced)
        ]
        + [
            {"token": t, "model": f"generic (α={_a:.1f})", "p": pg}
            for t, pg in zip(tokens, _p_generic)
        ]
    )

    _chart = (
        alt.Chart(_df)
        .mark_bar()
        .encode(
            x=alt.X("token:N", sort=tokens, title=None),
            y=alt.Y("p:Q", title="probability", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("model:N",
                scale=alt.Scale(range=["#5B8FF9", "#F4664A", "#5AD8A6"])),
            xOffset="model:N",
            tooltip=["model", "token", alt.Tooltip("p:Q", format=".3f")],
        )
        .properties(
            width="container", height=320,
            title="'Harry Potter's two best friends are ___' (toy logits)",
        )
    )
    mo.ui.altair_chart(_chart)
    return


@app.cell
def _(alpha_slider, mo):
    _a = alpha_slider.value
    _explanation = {
        0.0:  "**α = 0**: generic ≡ baseline. No unlearning happens.",
        1.0:  "**α small**: gentle nudge; Ron/Hermione lose a little probability.",
        5.0:  "**α = 5** (paper's chosen value): Ron and Hermione collapse; mass shifts to generic continuations like *his*, *two*, *the*.",
        8.0:  "**α large**: the subtraction is so aggressive that even mildly-HP tokens get suppressed. Risks damaging general competence.",
    }
    _closest = min(_explanation, key=lambda k: abs(k - _a))
    mo.callout(mo.md(_explanation[_closest]), kind="neutral")
    return


# ============================================================
#  ANCHOR DICTIONARY EXPLORER
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 5 · The anchored-terms dictionary

        The reinforcement trick from §4 has a blind spot. Once the model
        is primed with an unmistakably HP token like "Harry" or
        "Hogwarts", it has *already* committed to the wizarding world.
        Both the baseline and reinforced versions agree the next word is
        probably "Potter" or "school", and their logits don't differ by
        much. So the subtraction doesn't pull the model anywhere new.

        We need a way to get the model to predict generic tokens even
        when it's looking at HP-specific context. The authors' answer is
        a second tool: a **dictionary of ~1,500 anchored terms** that
        maps HP-specific entities to plausible generic counterparts
        (paper §2.2 and Listing 1). The dictionary was built by asking
        GPT-4 to extract HP-specific entities and propose substitutes.
        Thirty of those substitutions are shown below; try the search
        box to scan for one you'd expect to find.
        """
    )
    return


@app.cell
def _(anchor_dict, mo):
    search_box = mo.ui.text(
        placeholder="filter anchor terms (e.g., 'Hog', 'spell', 'house')",
        label="Search",
        full_width=True,
    )
    search_box
    return (search_box,)


@app.cell
def _(anchor_dict, mo, pd, search_box):
    _q = (search_box.value or "").lower().strip()
    _rows = [
        {"Original (HP)": k, "Generic translation": v}
        for k, v in anchor_dict.items()
        if not _q or _q in k.lower() or _q in v.lower()
    ]
    _df = pd.DataFrame(_rows)
    mo.ui.table(_df, page_size=15, selection=None)
    return


# ============================================================
#  ALGORITHM 1 WALKTHROUGH
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 6 · How the dictionary feeds the loss

        Here is how the dictionary plugs back into training. The recipe
        is three steps:

        1. **Take an HP passage** from the source text.
        2. **Substitute every anchored term** in it for its generic
           dictionary entry (Harry → Jon, Hogwarts → Mystic Academy,
           wand → rod, and so on). Feed *this* through the baseline
           model. What comes out is the model's prediction
           *as if the passage had never been about Harry Potter at all.*
        3. **Use those generic-passage predictions as fine-tuning
           targets, but on the ORIGINAL text.** The model now learns to
           emit non-HP completions even when its inputs scream Harry
           Potter.

        After roughly 150 gradient steps on this substituted-target loss
        (paper §2.4) the cue *"Harry"* no longer summons *"Hogwarts"* in
        the model's outputs. The model still recognizes the word "Harry";
        it just no longer associates it with the books.
        """
    )
    return


@app.cell
def _(anchor_dict, mo):
    passage = (
        "Harry walked into the Gryffindor common room. "
        "Hermione was already there, holding her wand and reading about a Patronus. "
        "Ron arrived a moment later, complaining about Quidditch practice."
    )

    def translate(text, d):
        out = text
        # apply longest keys first to avoid partial overlaps
        for k in sorted(d.keys(), key=len, reverse=True):
            out = out.replace(k, f"⟨{d[k]}⟩")
        return out

    translated = translate(passage, anchor_dict)

    mo.vstack(
        [
            mo.md("**Original passage** (the *input* tokens):"),
            mo.callout(mo.md(passage), kind="warn"),
            mo.md("**After anchor-substitution**, what the baseline model sees to generate generic next-token targets:"),
            mo.callout(mo.md(translated), kind="success"),
            mo.md(
                "→ The substituted-passage predictions become the loss "
                "targets on the *original* passage. The model has to "
                "learn to say what an HP-naive model would say, even when "
                "it can see *Harry* on the input side."
            ),
        ]
    )
    return


# ============================================================
#  THE TRADEOFF: familiarity vs benchmarks
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 7 · Did it work, and did anything else break?

        An unlearning method has to answer two questions at once.
        *Did it actually erase the target?* And *did the rest of the
        model survive?* Either alone is easy: refuse to answer anything
        and you erase everything (and break the model); do nothing and
        you preserve everything (and erase nothing). The interesting
        region is the upper-left of a "forgot HP × kept everything else"
        plot.

        The paper tracks both axes:

        - **Familiarity score** (left panel) measures how much Harry
          Potter content the unlearned model still produces, evaluated
          automatically against the books. Low is forgotten.
        - **General benchmarks** (right panel) are seven off-the-shelf
          reasoning and comprehension tests (ARC-easy, ARC-challenge,
          BoolQ, HellaSwag, OpenBookQA, PIQA, WinoGrande). They ask: is
          this still a competent Llama-2-7B?

        Both panels below come from the same checkpoints we've been
        sliding through. The familiarity score collapses from 0.29 to
        0.007 across 120 steps, a roughly 40× drop. The benchmark scores
        barely move. That gap is the paper's central empirical claim,
        and the shape of "barely move" is more informative than the
        headline.
        """
    )
    return


@app.cell
def _(alt, familiarity_benchmarks, mo, pd):
    _rows = []
    for _metric, _vals in familiarity_benchmarks["metrics"].items():
        _is_fam = "Familiarity" in _metric
        for _s, _v in zip(familiarity_benchmarks["steps"], _vals):
            _rows.append({
                "step": _s, "metric": _metric, "score": _v,
                "panel": "Familiarity (LOWER = more forgotten)" if _is_fam
                          else "General benchmarks (want to preserve)",
            })
    _df = pd.DataFrame(_rows)

    _fam_palette  = ["#E8523A", "#F4664A"]
    _bench_palette = ["#5B8FF9", "#5AD8A6", "#9BB0FF", "#F4A742",
                      "#9DA8B8", "#7FBFA0", "#C28BC4"]

    _fam = (
        alt.Chart(_df[_df["panel"].str.startswith("Familiarity")])
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("step:Q", title=None),
            y=alt.Y("score:Q", title="score",
                    scale=alt.Scale(domain=[0, 0.32])),
            color=alt.Color("metric:N",
                scale=alt.Scale(range=_fam_palette),
                legend=alt.Legend(orient="bottom", title=None, columns=1)),
            tooltip=["metric", "step", alt.Tooltip("score:Q", format=".3f")],
        )
        .properties(width=250, height=260,
                    title="Familiarity (LOWER = more forgotten)")
    )

    _bench = (
        alt.Chart(_df[~_df["panel"].str.startswith("Familiarity")])
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("step:Q", title="Fine-tuning steps"),
            y=alt.Y("score:Q", title="score",
                    scale=alt.Scale(domain=[0.30, 0.85])),
            color=alt.Color("metric:N",
                scale=alt.Scale(range=_bench_palette),
                legend=alt.Legend(orient="bottom", title=None, columns=2)),
            tooltip=["metric", "step", alt.Tooltip("score:Q", format=".3f")],
        )
        .properties(width=250, height=260,
                    title="General benchmarks (want to preserve)")
    )

    # Two separate charts rather than `_fam | _bench`. A concat shares one
    # color scale, which painted the benchmark lines in the familiarity reds
    # under one merged legend (and made marimo's legend-selection signal
    # collide across the panels). Separate specs keep each palette and
    # legend; wrap=True puts them side by side on desktop and stacks them
    # on a phone.
    mo.hstack([_fam, _bench], justify="center", wrap=True, gap=2)
    return


# ============================================================
#  CAVEATS  +  CLOSING
# ============================================================
@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ## 8 · Caveats, and where the field has gone since

        Four limitations the paper itself acknowledges, then a short
        note on where subsequent work has pushed back. The empirical
        result is real, but newer methods and newer evaluations have
        substantially changed how the field thinks about unlearning.

        - **Black-box evaluation only.** The familiarity score uses prompted
          completions. Adversarial probing of latent representations could
          still recover HP knowledge; the model may "know but not say."
        - **HP is unusually easy.** Fictional universes are dense with
          idiosyncratic names. Unlearning a non-fiction topic (a person's
          biography, a textbook) is much harder because there are fewer
          anchor terms.
        - **Some leaks remain.** The model card itself acknowledges *"a few
          minor leaks from the unlearnt content are likely to be found."*
          Ask the unlearned model for "fictional schools" and "Hogwarts"
          still appears, presumably from Wikipedia-level knowledge the
          unlearning corpus didn't cover.
        - **Relies on GPT-4 for the dictionary.** The technique inherits
          whatever GPT-4 already knew about Harry Potter when GPT-4 built
          the anchored-term map.
        - **Follow-up work has pushed back.** Lynch et al. (2024,
          [arxiv:2402.16835](https://arxiv.org/abs/2402.16835)) directly
          tested the released checkpoint and found that
          higher-than-baseline knowledge could be extracted, the unlearned
          model performed on par with the original on HP Q&A, and latent
          representations of the unlearned content persisted. Liu et al.
          (EMNLP 2024,
          [arxiv:2407.16997](https://arxiv.org/abs/2407.16997)) recast WHP
          as a special case of a broader causal-intervention framework for
          targeted unlearning. Treat the headline result as compelling first
          step, not solved problem.
        - **The field has moved on.** For general LLM unlearning, Negative
          Preference Optimization (Zhang et al. 2024,
          [arxiv:2404.05868](https://arxiv.org/abs/2404.05868)) and SimNPO
          (Fan et al., NeurIPS 2025,
          [arxiv:2410.07163](https://arxiv.org/abs/2410.07163)) have
          replaced reinforced-bootstrapping as the canonical method. For
          hazardous-knowledge unlearning specifically, WMDP and the
          associated RMU method (Li et al. 2024,
          [arxiv:2403.03218](https://arxiv.org/abs/2403.03218)) are the
          current reference points. WHP remains the cleanest pedagogical
          entry into the problem, which is why this walkthrough sits on top
          of it.

        ---
        ## 9 · About this notebook

        Built as a teaching artifact: a self-contained, reactive walk
        through one specific 2023 paper, using marimo's WebAssembly
        export so the whole thing runs in a browser without a server.
        Numbers are taken straight from the paper and the released model
        card; the interactive elements are wired to those values rather
        than to a live model.

        **Jacob Bowie**, researcher at the University of Connecticut.
        Physiological data analysis by day; interactive technical
        explainers as a side practice.

        - **Source:** [github.com/JacobBowie/marimo-unlearning](https://github.com/JacobBowie/marimo-unlearning)
        - **About me:** [jacobbowie.com](https://jacobbowie.com)
        - **Get in touch:** [jacob.bowie2@gmail.com](mailto:jacob.bowie2@gmail.com)

        ### Read the source paper

        - [Who's Harry Potter? Approximate Unlearning in LLMs](https://arxiv.org/abs/2310.02238).
          Eldan & Russinovich, Microsoft Research (2023).
        - [microsoft/Llama2-7b-WhoIsHarryPotter](https://huggingface.co/microsoft/Llama2-7b-WhoIsHarryPotter):
          the released unlearned checkpoint, under the Microsoft Research
          License Agreement.

        ### Built with

        [marimo](https://marimo.io) reactive notebooks · [Altair](https://altair-viz.github.io/) charts ·
        [networkx](https://networkx.org) graph layout · everything runs in your browser via
        [Pyodide](https://pyodide.org).

        *A 2026 [marimo](https://marimo.io) demonstration, explaining Eldan &
        Russinovich (2023) and the unlearning work it set off.*
        """
    )
    return


if __name__ == "__main__":
    app.run()

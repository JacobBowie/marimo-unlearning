"""
Skeleton for the "Giphy upgrade" path: a real d3-force network embedded
in marimo via mo.Html. Gives smooth tweening between checkpoints and
node-dragging that the Altair-based versions can't match.

Status: scaffolding only — the JS works in principle (d3.js v7 force
simulation is mature) but I haven't actually verified it renders inside
marimo's Html sandbox. Spend a half-day if v1 lands well and we want
to upgrade.

The pattern:
  1. Build node + edge dataframes in Python at every checkpoint
  2. Serialize as JSON
  3. Render an HTML page with d3.js loaded via CDN that:
       - Reads the JSON
       - Runs a force simulation (with current checkpoint's edge weights)
       - On slider change (or autoplay), interpolates between checkpoints
         smoothly via d3.transition()
  4. Embed via mo.Html(html_string)
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium", app_title="d3-force skeleton")


@app.cell
def _():
    import marimo as mo
    import json
    return json, mo


@app.cell
def _():
    nodes = [
        ("Harry",       "hp"),
        ("Hogwarts",    "hp"),
        ("Ron",         "hp"),
        ("Hermione",    "hp"),
        ("magic",       "bridge"),
        ("wand",        "bridge"),
        ("wizard",      "bridge"),
        ("British",     "general"),
        ("actor",       "general"),
        ("boy",         "general"),
    ]
    edges = [
        ("Harry", "Hogwarts", 0.95, 0.05),
        ("Harry", "Ron",      0.90, 0.05),
        ("Harry", "Hermione", 0.88, 0.05),
        ("Harry", "magic",    0.85, 0.06),
        ("Hogwarts", "magic", 0.90, 0.10),
        ("Ron", "Hermione",   0.85, 0.05),
        ("magic", "wand",     0.85, 0.85),
        ("magic", "wizard",   0.90, 0.90),
        ("Harry", "British",  0.05, 0.65),
        ("Harry", "actor",    0.02, 0.70),
        ("Harry", "boy",      0.20, 0.50),
    ]
    return edges, nodes


@app.cell
def _(json, mo, edges, nodes):
    zone_color = {"hp": "#E8523A", "bridge": "#F4A742", "general": "#5B8FF9"}

    nodes_json = json.dumps([
        {"id": label, "zone": zone, "color": zone_color[zone]}
        for label, zone in nodes
    ])
    # For the skeleton, ship just two snapshots (step 0 and step 120). The JS
    # interpolates linearly. Real version would ship all 7 checkpoints.
    edges_json = json.dumps([
        {"source": s, "target": t, "w0": w0, "w120": w120}
        for s, t, w0, w120 in edges
    ])

    html = f"""
    <div style="font-family: system-ui, sans-serif;">
      <input type="range" id="step" min="0" max="120" value="0"
             style="width: 100%; margin-bottom: 8px;" />
      <div id="step-readout" style="text-align: center; margin-bottom: 8px;">step 0</div>
      <svg id="d3-graph" width="600" height="500"
           style="background: #fafbfc; border-radius: 6px; display: block; margin: 0 auto;"></svg>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script>
    (function() {{
      const nodes = {nodes_json};
      const edges = {edges_json};
      const W = 600, H = 500;
      const svg = d3.select("#d3-graph");
      const stepInput = document.getElementById("step");
      const readout = document.getElementById("step-readout");

      const linkSel = svg.append("g")
        .selectAll("line")
        .data(edges)
        .join("line")
        .attr("stroke", d => d.w120 < d.w0 - 0.05 ? "#E8523A"
                            : d.w120 > d.w0 + 0.05 ? "#5AD8A6" : "#9DA8B8");

      const nodeSel = svg.append("g")
        .selectAll("circle")
        .data(nodes)
        .join("circle")
        .attr("r", 14)
        .attr("fill", d => d.color)
        .attr("stroke", "white")
        .attr("stroke-width", 1.5)
        .call(d3.drag()
          .on("start", (event, d) => {{ if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
          .on("drag",  (event, d) => {{ d.fx = event.x; d.fy = event.y; }})
          .on("end",   (event, d) => {{ if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

      const labelSel = svg.append("g")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .text(d => d.id)
        .attr("dy", -18)
        .attr("text-anchor", "middle")
        .attr("font-size", 11)
        .attr("font-weight", "bold");

      function weightAtStep(d, step) {{
        const t = step / 120;
        return d.w0 + (d.w120 - d.w0) * t;
      }}

      const sim = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(edges).id(d => d.id)
          .distance(d => 60 + 90 * (1 - Math.max(0.05, d.w0))))
        .force("charge", d3.forceManyBody().strength(-280))
        .force("center", d3.forceCenter(W / 2, H / 2));

      sim.on("tick", () => {{
        linkSel
          .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        nodeSel.attr("cx", d => d.x).attr("cy", d => d.y);
        labelSel.attr("x", d => d.x).attr("y", d => d.y);
      }});

      function applyStep(step) {{
        readout.textContent = "step " + step;
        edges.forEach(d => {{
          const w = weightAtStep(d, step);
          d.weight = w;
        }});
        linkSel
          .transition().duration(400)
          .attr("stroke-width", d => 0.5 + 4.5 * d.weight)
          .attr("stroke-opacity", d => 0.15 + 0.75 * d.weight);
        sim.force("link").distance(d => 60 + 90 * (1 - Math.max(0.05, d.weight)));
        sim.alpha(0.5).restart();
      }}

      applyStep(0);
      stepInput.addEventListener("input", e => applyStep(+e.target.value));
    }})();
    </script>
    """
    mo.Html(html)
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        **What this would buy us if it works:**
        - Smooth force-directed transitions between checkpoints
        - Node-dragging (grab and reposition; force re-settles)
        - Continuous slider (not just 7 discrete checkpoints)
        - Genuine "Giphy" feel

        **Risks / unknowns:**
        - marimo's `mo.Html` may sandbox script execution — needs verification
        - molab's WASM environment may block external CDN loads (would need to
          inline d3.js as a string, ~250 KB)
        - Mobile responsiveness needs hand-tuning
        - Doesn't get us reactive Python ↔ JS bridge (slider value lives in
          JS only, can't drive other Python cells)

        **Verdict:** test it; if it renders, build out the full version.
        If it doesn't, the Altair force-directed version is good enough for v1.
        """
    )
    return


if __name__ == "__main__":
    app.run()

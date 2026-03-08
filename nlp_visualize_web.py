from pyvis.network import Network
import webbrowser

# Colour coding for relationship types
_EDGE_COLORS = {
    "friendly": "#27ae60",   # green
    "hostile":  "#e74c3c",   # red
    "neutral":  "#95a5a6",   # grey
}

def create_interactive_graph(G, cooccurrences, output_file="graph.html"):
    """
    Create an interactive HTML graph using PyVis.

    Edges are coloured by their ``edge_type`` GraphML attribute when present:
    - **green**  → friendly
    - **red**    → hostile
    - **grey**   → neutral (default)

    Args:
        G (nx.Graph): NetworkX graph (may contain ``edge_type`` edge attributes)
        cooccurrences (Counter): Co-occurrence counts
        output_file (str): Output HTML filename
    """
    net = Network(height="750px", width="100%", 
                  notebook=False, directed=False)

    # Add nodes
    for node in G.nodes():
        count = G.nodes[node].get('count', 1)
        net.add_node(
            node,
            label=node,
            size=10 + count * 0.5,
            title=f"{node}: {count} mentions"
        )

    # Add edges — pick up edge_type from G if available
    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            edge_data  = G.get_edge_data(char1, char2, default={})
            edge_type  = edge_data.get("edge_type", "neutral")
            color      = _EDGE_COLORS.get(edge_type, _EDGE_COLORS["neutral"])
            net.add_edge(
                char1, char2,
                value=weight,
                title=f"{weight} co-occurrences | {edge_type}",
                color=color,
            )
    
    # Physics options
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": {
          "iterations": 200
        }
      }
    }
    """)
    
    net.write_html(output_file)
    print(f"✓ Interactive graph saved to {output_file}")
    webbrowser.open(output_file)


# ---------------------------------------------------------------------------
# Internal helper — shared by both single-file and combined-file paths
# ---------------------------------------------------------------------------

_PHYSICS_OPTIONS = """
{
  "physics": {
    "enabled": true,
    "stabilization": { "iterations": 200 }
  }
}
"""

def _build_network_html(G, cooccurrences):
    """
    Build a PyVis network from *G* and *cooccurrences* and return the full
    HTML page as a string (without writing to disk or opening a browser).

    Edges are coloured by ``edge_type`` if present (same palette as
    ``create_interactive_graph``).

    Args:
        G (nx.Graph): NetworkX graph
        cooccurrences (Counter): Co-occurrence counts

    Returns:
        str: Self-contained HTML page as a string.
    """
    net = Network(height="100vh", width="100%", notebook=False, directed=False)

    for node in G.nodes():
        count = G.nodes[node].get("count", 1)
        net.add_node(
            node,
            label=node,
            size=10 + count * 0.5,
            title=f"{node}: {count} mentions",
        )

    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            edge_data = G.get_edge_data(char1, char2, default={})
            edge_type = edge_data.get("edge_type", "neutral")
            color     = _EDGE_COLORS.get(edge_type, _EDGE_COLORS["neutral"])
            net.add_edge(
                char1, char2,
                value=weight,
                title=f"{weight} co-occurrences | {edge_type}",
                color=color,
            )

    net.set_options(_PHYSICS_OPTIONS)
    return net.generate_html()


# ---------------------------------------------------------------------------
# Public API — create one HTML file for many chapters
# ---------------------------------------------------------------------------

_COMBINED_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ display: flex; height: 100vh; font-family: "Segoe UI", Arial, sans-serif; background: #f0f2f5; }}

    /* ── Sidebar ───────────────────────────────────────────── */
    #sidebar {{
      width: 200px; min-width: 160px;
      background: #1e2a38; color: #ecf0f1;
      display: flex; flex-direction: column;
      overflow-y: auto;
    }}
    #sidebar-title {{
      padding: 14px 12px 10px;
      font-size: 14px; font-weight: 700;
      background: #141e28; border-bottom: 1px solid #2c3e50;
      line-height: 1.3;
    }}
    .book-label {{
      padding: 10px 12px 4px;
      font-size: 10px; color: #7f8c8d;
      text-transform: uppercase; letter-spacing: .08em;
    }}
    .tab-btn {{
      display: block; width: 100%;
      padding: 7px 16px;
      text-align: left; border: none;
      background: none; color: #bdc3c7;
      cursor: pointer; font-size: 13px;
      transition: background .15s, color .15s;
    }}
    .tab-btn:hover  {{ background: #2c3e50; color: #ecf0f1; }}
    .tab-btn.active {{ background: #2980b9; color: #fff; font-weight: 600; }}

    /* ── Main area ─────────────────────────────────────────── */
    #main {{
      flex: 1; display: flex; flex-direction: column; overflow: hidden; min-height: 0;
    }}
    #topbar {{
      display: flex; align-items: center; gap: 20px;
      padding: 7px 18px;
      background: #fff; border-bottom: 1px solid #dee2e6;
      font-size: 13px;
    }}
    #chapter-title {{
      font-weight: 600; font-size: 15px; color: #2c3e50;
    }}
    #stats {{ color: #7f8c8d; font-size: 12px; }}
    .legend-item {{ display: flex; align-items: center; gap: 5px; }}
    .dot {{
      width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0;
    }}

    /* ── Frames ────────────────────────────────────────────── */
    .frame-wrap {{
      display: none; flex: 1; min-height: 0;
    }}
    .frame-wrap.active {{ display: flex; }}
    iframe {{
      flex: 1; border: none; width: 100%; min-height: 0;
    }}
  </style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-title">{title}</div>
  {sidebar_html}
</div>

<div id="main">
  <div id="topbar">
    <span id="chapter-title">—</span>
    <span id="stats"></span>
    <span style="margin-left:auto; display:flex; gap:14px;">
      <span class="legend-item"><span class="dot" style="background:#27ae60"></span>Friendly</span>
      <span class="legend-item"><span class="dot" style="background:#e74c3c"></span>Hostile</span>
      <span class="legend-item"><span class="dot" style="background:#95a5a6"></span>Neutral</span>
    </span>
  </div>
  {frames_html}
</div>

<script>
  var META = {meta_json};

  function showTab(id) {{
    document.querySelectorAll('.frame-wrap').forEach(f => f.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    var fw  = document.getElementById('frame-' + id);
    var btn = document.getElementById('btn-' + id);
    if (!fw || !btn) return;
    // Lazy-load: set srcdoc only on first visit so vis.js inits when visible
    var iframe = fw.querySelector('iframe');
    if (iframe && !iframe.hasAttribute('srcdoc') && iframe.dataset.srcdoc) {{
      iframe.srcdoc = iframe.dataset.srcdoc;
    }}
    fw.classList.add('active');
    btn.classList.add('active');
    var m = META[id] || {{}};
    document.getElementById('chapter-title').textContent = id;
    document.getElementById('stats').textContent =
      m.nodes + ' nodes \u00b7 ' + m.edges + ' edges'
      + (m.friendly !== undefined
         ? '   |   friendly: ' + m.friendly + '  hostile: ' + m.hostile + '  neutral: ' + m.neutral
         : '');
  }}
  // activate first chapter on load
  var first = document.querySelector('.tab-btn');
  if (first) showTab(first.dataset.id);
</script>
</body>
</html>
"""


def create_combined_html(chapters_data, output_file="all_networks.html",
                         title="Character Networks"):
    """
    Render every chapter's character network into **one** HTML file.

    The page has a sidebar listing chapters grouped by book (identified by the
    prefix before the first digit in the chapter id, e.g. ``"paf"`` / ``"lca"``).
    Clicking a chapter shows its network graph in the main area.
    Edges are colour-coded by relationship type (green/red/grey).

    This function does **not** affect ``create_interactive_graph()`` and is safe
    to add without breaking existing callers.

    Args:
        chapters_data (list): Sequence of ``(chapter_id, G, cooccurrences)``
                              tuples, where *G* is a ``nx.Graph`` that may
                              carry ``edge_type`` edge attributes and
                              *cooccurrences* is a ``Counter``.  An optional
                              fourth element (a ``Counter`` of label→count) may
                              be provided as label stats.
        output_file (str):    Path of the output ``.html`` file.
        title (str):          Page/sidebar heading shown in the browser.

    Returns:
        str: Absolute path to the written file.
    """
    import json, re, html as _html

    # ── group chapters by book prefix ────────────────────────────────────────
    books: dict = {}
    meta: dict  = {}

    sidebar_parts: list[str] = []
    frames_parts:  list[str] = []

    for entry in chapters_data:
        if len(entry) == 4:
            chapter_id, G, cooccurrences, label_counts = entry
        else:
            chapter_id, G, cooccurrences = entry
            label_counts = None

        # derive book key from id prefix (everything before first digit)
        m = re.match(r"([a-zA-Z_]+)", chapter_id)
        book_key = m.group(1) if m else "other"
        books.setdefault(book_key, []).append(chapter_id)

        # build metadata for the JS topbar
        mc: dict = {"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
        if label_counts is not None:
            mc["friendly"] = label_counts.get("friendly", 0)
            mc["hostile"]  = label_counts.get("hostile",  0)
            mc["neutral"]  = label_counts.get("neutral",  0)
        meta[chapter_id] = mc

        # build per-chapter iframe — use data-srcdoc for lazy loading
        # (vis.js can only initialise when the container is visible)
        inner_html = _build_network_html(G, cooccurrences)
        escaped    = inner_html.replace("&", "&amp;").replace('"', "&quot;")
        frames_parts.append(
            f'<div class="frame-wrap" id="frame-{chapter_id}">'
            f'<iframe data-srcdoc="{escaped}"></iframe>'
            f'</div>'
        )

    # ── sidebar: one section per book ────────────────────────────────────────
    for book_key, chapter_ids in books.items():
        sidebar_parts.append(
            f'<div class="book-label">{book_key.upper()}</div>'
        )
        for cid in chapter_ids:
            sidebar_parts.append(
                f'<button class="tab-btn" id="btn-{cid}" '
                f'data-id="{cid}" onclick="showTab(\'{cid}\')">'
                f'{cid}</button>'
            )

    combined = _COMBINED_HTML_TEMPLATE.format(
        title        = _html.escape(title),
        sidebar_html = "\n  ".join(sidebar_parts),
        frames_html  = "\n  ".join(frames_parts),
        meta_json    = json.dumps(meta),
    )

    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(combined)

    import os
    print(f"✓ Combined network saved → {output_file}")
    return os.path.abspath(output_file)
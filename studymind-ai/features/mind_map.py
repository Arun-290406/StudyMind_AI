# features/mind_map.py
"""
Mind map / knowledge graph builder.
Generates concept nodes and relationships from indexed notes.
Renders using pyvis for interactive visualization.
"""

import os
import json
import tempfile
from typing import List, Dict, Optional

import networkx as nx
from core.llm import simple_chat
from core.retriever import retrieve, build_context_string
from utils.formatters import parse_mind_map


# ── Prompts ───────────────────────────────────────────────────────────────────

MIND_MAP_SYSTEM = """You are an expert knowledge graph builder.
Extract concepts and their relationships from study material.
Create a connected graph that shows how ideas relate to each other.
"""

MIND_MAP_PROMPT = """Extract a knowledge graph from the following study notes.

Notes:
{context}

Output ONLY a valid JSON object. No extra text. Format:
{{
  "nodes": [
    {{"id": "n1", "label": "Main Concept", "group": "core"}},
    {{"id": "n2", "label": "Sub Concept", "group": "detail"}},
    ...
  ],
  "edges": [
    {{"from": "n1", "to": "n2", "label": "contains"}},
    {{"from": "n2", "to": "n3", "label": "leads to"}},
    ...
  ]
}}

Groups: "core" (main topics), "detail" (sub-concepts), "example" (examples/applications)
Keep to 8-15 nodes and 10-20 edges maximum for clarity.

JSON:"""


# ── Generation ────────────────────────────────────────────────────────────────

def generate_mind_map(
    vector_store,
    topic: str = "",
    max_nodes: int = 15,
) -> Dict:
    """
    Generate a mind map data dict from indexed notes.
    Returns {nodes, edges, graph_metrics}.
    """
    query   = topic if topic else "main concepts relationships overview"
    docs    = retrieve(vector_store, query, k=8)
    context = build_context_string(docs, max_chars=4000)

    prompt  = MIND_MAP_PROMPT.format(context=context)
    raw     = simple_chat(prompt, system=MIND_MAP_SYSTEM, temperature=0.5)
    data    = parse_mind_map(raw)

    # Trim to max_nodes
    if len(data["nodes"]) > max_nodes:
        keep_ids = {n["id"] for n in data["nodes"][:max_nodes]}
        data["nodes"] = data["nodes"][:max_nodes]
        data["edges"] = [
            e for e in data["edges"]
            if e["from"] in keep_ids and e["to"] in keep_ids
        ]

    data["topic"]   = topic or "All Notes"
    data["metrics"] = _graph_metrics(data)
    return data


# ── NetworkX graph ────────────────────────────────────────────────────────────

def to_networkx(mind_map_data: Dict) -> nx.Graph:
    """Convert mind map dict to a NetworkX graph for analysis."""
    G = nx.Graph()
    for node in mind_map_data.get("nodes", []):
        G.add_node(node["id"], label=node.get("label", ""), group=node.get("group", ""))
    for edge in mind_map_data.get("edges", []):
        G.add_edge(edge["from"], edge["to"], label=edge.get("label", ""))
    return G


def _graph_metrics(data: Dict) -> Dict:
    """Compute basic graph metrics."""
    G = to_networkx(data)
    if G.number_of_nodes() == 0:
        return {}
    try:
        return {
            "num_nodes":   G.number_of_nodes(),
            "num_edges":   G.number_of_edges(),
            "density":     round(nx.density(G), 3),
            "is_connected": nx.is_connected(G),
            "central_node": max(nx.degree_centrality(G), key=nx.degree_centrality(G).get),
        }
    except Exception:
        return {"num_nodes": G.number_of_nodes(), "num_edges": G.number_of_edges()}


# ── Pyvis HTML rendering ──────────────────────────────────────────────────────

def render_mind_map_html(mind_map_data: Dict, height: str = "500px") -> str:
    """
    Render the mind map as an interactive pyvis HTML string.
    Returns the HTML string to embed in Streamlit via components.html().
    """
    try:
        from pyvis.network import Network
    except ImportError:
        return "<p>Install pyvis: <code>pip install pyvis</code></p>"

    net = Network(
        height=height,
        width="100%",
        bgcolor="#1e2d40",
        font_color="#e6edf3",
        directed=False,
    )
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120)

    COLOR_MAP = {
        "core":    "#58a6ff",
        "detail":  "#10b981",
        "example": "#f59e0b",
    }

    for node in mind_map_data.get("nodes", []):
        group = node.get("group", "detail")
        color = COLOR_MAP.get(group, "#8b949e")
        size  = 30 if group == "core" else 20
        net.add_node(
            node["id"],
            label=node.get("label", node["id"]),
            color=color,
            size=size,
            font={"size": 14, "color": "#e6edf3"},
        )

    for edge in mind_map_data.get("edges", []):
        net.add_edge(
            edge["from"],
            edge["to"],
            label=edge.get("label", ""),
            color="#4a5568",
            width=1.5,
        )

    # Render to temp file and read back
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        net.save_graph(f.name)
        tmp_path = f.name

    with open(tmp_path, "r") as f:
        html = f.read()

    os.unlink(tmp_path)
    return html
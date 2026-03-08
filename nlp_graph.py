import networkx as nx
import matplotlib.pyplot as plt

def generate_graph(cooccurrences, character_counts, alias_map=None, edge_labels=None):
    """
    Generate a NetworkX graph from co-occurrences.

    Args:
        cooccurrences (Counter): Character pair co-occurrences
        character_counts (Counter): Character mention counts
        alias_map (dict): Optional {surface: canonical} mapping used to
                          populate the required `names` node attribute.
                          When provided every surface form that maps to a
                          canonical node is listed in that node's `names`.
        edge_labels (dict): Optional {(charA, charB): edge_type_str} from
                            nlp_relation.label_relationships().  When provided,
                            each edge gains an `edge_type` GraphML attribute
                            ("friendly" | "hostile" | "neutral").

    Returns:
        nx.Graph: Network graph where every node has a `names` attribute
                  (semicolon-separated list of character name variants).
                  Edges have a `weight` attribute and, if edge_labels is
                  provided, an `edge_type` attribute.
    """
    G = nx.Graph()

    # Build reverse map: canonical -> sorted list of all surface forms
    canonical_to_surfaces: dict[str, list[str]] = {}
    if alias_map:
        for surface, canonical in alias_map.items():
            canonical_to_surfaces.setdefault(canonical, []).append(surface)

    # Add nodes with count + names attribute
    for character, count in character_counts.items():
        G.add_node(character, count=count)
        surfaces = canonical_to_surfaces.get(character, [])
        # Always include the canonical name itself, deduplicate, keep order
        all_names = [character] + [s for s in surfaces if s != character]
        G.nodes[character]["names"] = ";".join(all_names)

    # Add edges with weight based on co-occurrence; optionally tag with edge_type
    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            G.add_edge(char1, char2, weight=weight)
            if edge_labels:
                etype = (
                    edge_labels.get((char1, char2))
                    or edge_labels.get((char2, char1))
                    or "neutral"
                )
                G[char1][char2]["edge_type"] = etype

    return G


def remove_isolated_nodes(G):
    """
    Remove nodes with no edges (degree == 0) from the graph in-place.
    These are characters detected by NER that never co-appear with anyone
    in the co-occurrence window, so they contribute no useful information
    to the character network.

    Args:
        G (nx.Graph): Network graph (modified in-place)

    Returns:
        nx.Graph: Same graph with isolated nodes removed
    """
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    return G


def save_graphml(G, filename):
    """Save graph in GraphML format."""
    nx.write_graphml(G, filename)
    print(f"✓ Graph saved to {filename}")

def visualize_graph(G, title="Character Network", top_n=30):
    """
    Visualize the graph using matplotlib.
    
    Args:
        G (nx.Graph): Network graph
        title (str): Plot title
        top_n (int): Only show top N connected characters
    """
    # Filter to top connected nodes
    degrees = dict(G.degree())
    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:top_n]
    G_sub = G.subgraph(top_nodes)
    
    plt.figure(figsize=(16, 12))
    
    # Layout
    pos = nx.spring_layout(G_sub, k=0.5, iterations=50)
    
    # Node sizes based on degree
    node_sizes = [300 + 50 * degrees[node] for node in G_sub.nodes()]
    
    # Edge widths based on weight
    edge_widths = [0.5 + G_sub[u][v]['weight'] * 0.2 
                   for u, v in G_sub.edges()]
    
    # Draw
    nx.draw_networkx_nodes(G_sub, pos, node_size=node_sizes, 
                          node_color='lightblue', alpha=0.9)
    nx.draw_networkx_edges(G_sub, pos, width=edge_widths, 
                          alpha=0.5, edge_color='gray')
    nx.draw_networkx_labels(G_sub, pos, font_size=9, 
                           font_weight='bold')
    
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
import networkx as nx
import matplotlib.pyplot as plt

def generate_graph(cooccurrences, character_counts):
    """
    Generate a NetworkX graph from co-occurrences.
    
    Args:
        cooccurrences (Counter): Character pair co-occurrences
        character_counts (Counter): Character mention counts
    
    Returns:
        nx.Graph: Network graph
    """
    G = nx.Graph()
    
    # Add nodes with size based on mention count
    for character, count in character_counts.items():
        G.add_node(character, count=count)
    
    # Add edges with weight based on co-occurrence
    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            G.add_edge(char1, char2, weight=weight)
    
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
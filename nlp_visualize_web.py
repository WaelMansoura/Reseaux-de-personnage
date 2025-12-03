from pyvis.network import Network
import webbrowser

def create_interactive_graph(G, cooccurrences, output_file="graph.html"):
    """
    Create an interactive HTML graph using PyVis.
    
    Args:
        G (nx.Graph): NetworkX graph
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
    
    # Add edges
    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            net.add_edge(
                char1, char2,
                value=weight,
                title=f"{weight} co-occurrences"
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
# %%
import os
import networkx as nx
import pandas as pd
import importlib


# Reload all your modules
importlib.reload(importlib.import_module("nlp_extract_characters"))
importlib.reload(importlib.import_module("nlp_utils"))
importlib.reload(importlib.import_module("nlp_aliases"))
importlib.reload(importlib.import_module("nlp_cooccurrence"))
importlib.reload(importlib.import_module("nlp_graph"))
importlib.reload(importlib.import_module("nlp_multi_ner"))

from nlp_extract_characters import extract_entities, count_entities, filter_persons, filter_locations
from nlp_utils import read_file, load_anti_dict
from nlp_aliases import group_aliases, alias_dictionary, merge_alias_counts
from nlp_cooccurrence import detect_cooccurrences
from nlp_graph import generate_graph
from nlp_multi_ner import ensemble_entities

# %%
def process_chapter(chapter_file, anti_dict, distance_max=25):
    """
    Process a single chapter and return a NetworkX graph with 'names' attributes.
    
    Args:
        chapter_file (str): Path to chapter file
        anti_dict (set): Anti-dictionary for filtering
        distance_max (int): Co-occurrence distance threshold
    
    Returns:
        nx.Graph: Graph with nodes having 'names' attribute
    """
    # Read text
    text = read_file(chapter_file)
    
    # 1. Extract entities
    # raw_entities = extract_entities(text)
    raw_entities = ensemble_entities(text, method="vote")
    
    # 2. Count entities
    L = count_entities(raw_entities)
    
    # 3.1. Filter persons
    LP = filter_persons(L, anti_dict=anti_dict)

    # 3.2. Filter locations (not used further here, but could be)
    LL = filter_locations(L)

    # 3.3 Store L,LP, LL in files
    base_filename = os.path.splitext(os.path.basename(chapter_file))[0]
    with open(f"{base_filename}_L.txt", "w", encoding="utf8") as f:
        for (text, label), count in L.most_common():
            f.write(f"{text:30}  {label:5}  {count}\n")
    with open(f"{base_filename}_LP.txt", "w", encoding="utf8") as f:
        for text, count in LP.most_common():
            f.write(f"{text:30}  {count}\n")
    with open(f"{base_filename}_LL.txt", "w", encoding="utf8") as f:
        for text, count in LL.most_common():
            f.write(f"{text:30}  {count}\n")
    
    # 4. Group aliases
    groups = group_aliases(LP)
    alias_map = alias_dictionary(groups)
    LP_merged = merge_alias_counts(LP, alias_map)
    
    # 5. Detect co-occurrences
    cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
    
    # 6. Generate graph
    G = generate_graph(cooccurrences, LP_merged)
    
    # 7. Add 'names' attribute to each node
    # This is CRITICAL for Kaggle submission
    for group in groups:
        canonical = group[0]  # First name is canonical
        if canonical in G.nodes:
            # Join all aliases with semicolon as required
            G.nodes[canonical]["names"] = ";".join(group)
    
    # Handle nodes that might not be in groups (single occurrence names)
    for node in G.nodes:
        if "names" not in G.nodes[node]:
            G.nodes[node]["names"] = node
    
    return G

# %%
def generate_submission(
    books_config,
    anti_dict_file,
    output_csv="submission.csv",
    distance_max=25
):
    """
    Generate submission CSV for Kaggle leaderboard.
    
    Args:
        books_config (list): List of (chapter_numbers, book_code, folder_path) tuples
        anti_dict_file (str): Path to anti-dictionary
        output_csv (str): Output CSV filename
        distance_max (int): Co-occurrence distance threshold
    
    Returns:
        pd.DataFrame: Submission dataframe
    """
    # Load anti-dictionary once
    print(f"📚 Loading anti-dictionary from: {anti_dict_file}")
    anti_dict = load_anti_dict(anti_dict_file)
    print(f"   ✓ Loaded {len(anti_dict)} entries")
    
    df_dict = {"ID": [], "graphml": []}
    
    total_chapters = sum(len(chapters) for chapters, _, _ in books_config)
    processed = 0
    
    for chapters, book_code, folder_path in books_config:
        print(f"\n📖 Processing book: {book_code} ({len(chapters)} chapters)")
        
        for chapter_num in chapters:
            chapter_id = f"{book_code}{chapter_num}"
            
            # Construct chapter file path
            chapter_file = os.path.join(
                folder_path, 
                f"chapter_{chapter_num + 1}.txt.preprocessed"  # Assuming files start at 1
            )
            
            # Check if file exists
            if not os.path.isfile(chapter_file):
                print(f"   ⚠️  {chapter_id}: File not found: {chapter_file}")
                continue
            
            try:
                print(f"   📄 Processing {chapter_id}...", end=" ")
                
                # Process chapter
                G = process_chapter(chapter_file, anti_dict, distance_max)
                
                # Convert to GraphML string
                graphml = "".join(nx.generate_graphml(G))
                
                # Add to submission
                df_dict["ID"].append(chapter_id)
                df_dict["graphml"].append(graphml)
                
                processed += 1
                print(f"✓ (Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()})")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    # Create DataFrame
    df = pd.DataFrame(df_dict)
    df.set_index("ID", inplace=True)
    
    # Save to CSV
    df.to_csv(output_csv, encoding="utf-8")
    
    print(f"\n{'='*60}")
    print(f"✅ SUBMISSION COMPLETE")
    print(f"{'='*60}")
    print(f"Output file: {output_csv}")
    print(f"Chapters processed: {processed}/{total_chapters}")
    print(f"Missing: {total_chapters - processed}")
    
    return df
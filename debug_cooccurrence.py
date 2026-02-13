"""Debug script for co-occurrence detection"""

from collections import Counter
from nlp_cooccurrence import detect_cooccurrences
from nlp_extract_characters import extract_entities, count_entities, filter_persons
from nlp_utils import read_file, load_anti_dict
from nlp_aliases import group_aliases, alias_dictionary, merge_alias_counts
from nlp_multi_ner import ensemble_entities

# Read a sample chapter
text = read_file("data/prelude_a_fondation/chapter_1.txt.preprocessed")

print("=" * 60)
print("STEP 1: Extract entities")
print("=" * 60)
raw_entities = ensemble_entities(text, method="vote")
print(f"Found {len(raw_entities)} raw entities")

print("\n" + "=" * 60)
print("STEP 2: Count entities")
print("=" * 60)
L = count_entities(raw_entities)
print(f"Unique entities: {len(L)}")

print("\n" + "=" * 60)
print("STEP 3: Filter persons")
print("=" * 60)
anti_dict = load_anti_dict("antidict.txt")
LP = filter_persons(L, anti_dict=anti_dict)
print(f"Person entities: {len(LP)}")
print("\nTop 10 persons:")
for name, count in LP.most_common(10):
    print(f"  {name:30} {count}")

print("\n" + "=" * 60)
print("STEP 4: Group aliases")
print("=" * 60)
groups = group_aliases(LP)
alias_map = alias_dictionary(groups)
LP_merged = merge_alias_counts(LP, alias_map)
print(f"After merging: {len(LP_merged)} unique characters")
print("\nTop 10 merged characters:")
for name, count in LP_merged.most_common(10):
    print(f"  {name:30} {count}")

print("\n" + "=" * 60)
print("STEP 5: Detect co-occurrences")
print("=" * 60)
print(f"Input to detect_cooccurrences:")
print(f"  - Text length: {len(text)} characters")
print(f"  - Character counts: {len(LP_merged)} characters")
print(f"  - Character names: {list(LP_merged.keys())[:5]}...")

cooccurrences = detect_cooccurrences(text, LP_merged, distance_max=25)

print(f"\nCo-occurrences found: {len(cooccurrences)}")
if cooccurrences:
    print("\nTop 10 co-occurrences:")
    for (a, b), count in cooccurrences.most_common(10):
        print(f"  ({a}, {b}): {count}")
    
    print("\n" + "=" * 60)
    print("STEP 6: Test graph generation")
    print("=" * 60)
    from nlp_graph import generate_graph
    
    G = generate_graph(cooccurrences, LP_merged)
    print(f"Graph nodes: {G.number_of_nodes()}")
    print(f"Graph edges: {G.number_of_edges()}")
    
    if G.number_of_edges() > 0:
        print("\n✅ SUCCESS: Graph has edges! Co-occurrences are working correctly.")
        print("\nSample edges:")
        for u, v, data in list(G.edges(data=True))[:5]:
            print(f"  {u} <-> {v} (weight: {data['weight']})")
    else:
        print("\n⚠️  WARNING: Graph has NO edges!")
        print("This means co-occurrences are detected but not being added to graph.")
else:
    print("\n⚠️  WARNING: No co-occurrences detected!")
    print("\nDEBUGGING INFO:")
    # Let's manually check
    import re
    tokens = re.findall(r"\w+", text.lower())
    print(f"  Total tokens in text: {len(tokens)}")
    print(f"  First 30 tokens: {tokens[:30]}")
    
    # Check if any character names appear in the text
    print("\n  Checking if character names appear in text:")
    for name in list(LP_merged.keys())[:5]:
        name_lower = name.lower()
        name_tokens = name_lower.split()
        print(f"    '{name}' -> tokens: {name_tokens}")
        # Simple check if the name appears
        text_lower = text.lower()
        if name_lower in text_lower:
            print(f"      ✓ Found in text (simple match)")
        else:
            print(f"      ✗ NOT found in text (simple match)")

# %%
# =============================================================================
# CONFIGURATION - ADJUST THESE PATHS
# =============================================================================

books_folder = "/content/drive/MyDrive/M1/AMS Projet 1/FinalProject/data"
books_config = [
    # (chapter_range, book_code, folder_path)
    (list(range(0, 19)), "paf", f"{books_folder}/prelude_a_fondation"),      # paf0 to paf18
    (list(range(0, 18)), "lca", f"{books_folder}/les_cavernes_d_acier"),     # lca0 to lca17
]

anti_dict_file = "antidict.txt"
output_csv = "submission.csv"
distance_max = 50  # Co-occurrence window size

# %%
# =============================================================================
# RUN SUBMISSION GENERATION
# =============================================================================

print("🚀 Starting submission generation...")
print(f"Distance threshold: {distance_max} words")

df_submission = generate_submission(
    books_config=books_config,
    anti_dict_file=anti_dict_file,
    output_csv=output_csv,
    distance_max=distance_max
)

# %%
# =============================================================================
# VERIFY SUBMISSION
# =============================================================================

print("\n" + "="*60)
print("SUBMISSION VERIFICATION")
print("="*60)

print("\n📊 Submission Overview:")
print(df_submission.head(10))

print("\n📈 Statistics:")
print(f"Total entries: {len(df_submission)}")
print(f"Expected: 37 chapters (19 paf + 18 lca)")

# Check for missing chapters
expected_ids = [f"paf{i}" for i in range(19)] + [f"lca{i}" for i in range(18)]
actual_ids = set(df_submission.index)
missing_ids = [id for id in expected_ids if id not in actual_ids]

if missing_ids:
    print(f"\n⚠️  Missing chapters: {', '.join(missing_ids)}")
else:
    print("\n✅ All expected chapters present!")

# %%
# =============================================================================
# INSPECT SAMPLE GRAPHS
# =============================================================================

print("\n" + "="*60)
print("SAMPLE GRAPH INSPECTION")
print("="*60)

sample_ids = ["paf0", "lca0"]

for sample_id in sample_ids:
    if sample_id in df_submission.index:
        print(f"\n📖 Sample: {sample_id}")

        # Parse GraphML back to NetworkX
        import io
        graphml_str = df_submission.loc[sample_id, "graphml"]
        G_sample = nx.read_graphml(io.StringIO(graphml_str))

        print(f"   Nodes: {G_sample.number_of_nodes()}")
        print(f"   Edges: {G_sample.number_of_edges()}")

        print("\n   Sample nodes with 'names' attribute:")
        for i, (node, data) in enumerate(G_sample.nodes(data=True)):
            if i < 5:
                names = data.get('names', '⚠️ MISSING')
                print(f"      • {node}: {names}")
            if i == 5:
                print(f"      ... and {G_sample.number_of_nodes() - 5} more")
                break
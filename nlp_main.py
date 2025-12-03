from nlp_aliases import group_aliases, alias_dictionary, merge_alias_counts
from nlp_utils import read_file, load_anti_dict
from nlp_extract_characters import extract_entities, count_entities, filter_persons, filter_locations
    
def main():
    texte = read_file("output.txt")

    # 1. Extract ALL entities (raw)
    raw_entities = extract_entities(texte)

    # 2. Count all entities → L
    L = count_entities(raw_entities)

    # 3. Extract person entities → LP
    anti_dict = load_anti_dict("antidict.txt")
    LP = filter_persons(L, anti_dict=anti_dict)

    # 4. Extract location entities → LL
    LL = filter_locations(L)

    # Write L
    with open("L.txt", "w", encoding="utf8") as f:
        for (text, label), count in L.most_common():
            f.write(f"{text:30}  {label:5}  {count}\n")

    # Write LP (persons)
    with open("LP.txt", "w", encoding="utf8") as f:
        for text, count in LP.most_common():
            f.write(f"{text:30}  {count}\n")

    # Write LL (locations)
    with open("LL.txt", "w", encoding="utf8") as f:
        for text, count in LL.most_common():
            f.write(f"{text:30}  {count}\n")

    # 5. Group aliases in LP
    groups = group_aliases(LP)
    alias_map = alias_dictionary(groups)
    LP_merged = merge_alias_counts(LP, alias_map)

    print("\n=== ALIAS GROUPS ===")

    for grp in groups:
        print(grp)

    print("\n=== ALIAS MAP ===")
    for alias, canonical in alias_map.items():
        print(f"{alias:20} -> {canonical}")

    print("\n=== LP MERGED ===")
    for name, count in LP_merged.most_common():
        print(f"{name:30} {count}")

if __name__ == "__main__":
    main()
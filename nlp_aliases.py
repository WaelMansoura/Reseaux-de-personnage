# alias_utils.py
import re
from collections import defaultdict, Counter

try:
    from rapidfuzz.fuzz import ratio as fuzz_ratio
    _FUZZY_AVAILABLE = True
except ImportError:
    from difflib import SequenceMatcher
    def fuzz_ratio(a, b):
        return SequenceMatcher(None, a, b).ratio() * 100
    _FUZZY_AVAILABLE = False

TITLES = [
    "mr", "mme", "mrs", "ms", "dr", "prof", "sir",
    "m", "mlle", "lord", "maître", "colonel", "commissaire",
    "inspecteur", "capitaine", "général", "docteur"
]

# Minimum fuzzy ratio to consider two normalized names similar enough to merge.
# Conservative to avoid false positives on French names.
FUZZY_THRESHOLD = 88


def normalize_name(name: str) -> str:
    """
    Normalize a person name for alias matching:
    - lowercase and strip
    - remove civil/noble titles
    - remove punctuation (keep accented chars and hyphens)
    - collapse extra spaces
    """
    n = name.lower().strip()
    for t in TITLES:
        n = re.sub(rf"\b{t}\b\.?", "", n)
    n = re.sub(r"[^\w\sàâäéèêëîïôöùûüç-]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def name_keywords(name: str) -> set:
    """Return the set of normalized words (keywords) in a name."""
    return set(normalize_name(name).split())


# ---------------------------------------------------------------------------
# Union-Find (Disjoint Set Union) used internally by group_aliases
# ---------------------------------------------------------------------------

class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[ry] = rx

    def groups(self):
        clusters = defaultdict(list)
        for x in self.parent:
            clusters[self.find(x)].append(x)
        return list(clusters.values())


def _should_merge(name1: str, name2: str) -> bool:
    """
    Decide whether two surface names refer to the same character.

    Rules:
    1. Both multi-word → only merge if one's keyword-set is a proper subset
       of the other (one is a shorter form of the other, e.g. "Hari Seldon"
       and "Seldon Hari"-style overlap is blocked; only pure abbreviations
       like {"seldon"} ⊆ {"hari","seldon"} pass).
    2. One single-word, one multi-word → merge if the single word is a
       meaningful (len > 1) keyword of the multi-word name.
    3. Both single-word → require fuzzy similarity above FUZZY_THRESHOLD
       to avoid merging distinct short names (e.g. "Hari" vs "Harinder").
    4. No keyword overlap → fuzzy fallback only when at least one is
       multi-word and ratio >= FUZZY_THRESHOLD.
    """
    kw1 = name_keywords(name1)
    kw2 = name_keywords(name2)

    if not kw1 or not kw2:
        return False

    shared = kw1 & kw2
    multi1 = len(kw1) > 1
    multi2 = len(kw2) > 1

    if shared:
        # Ignore purely single-character shared tokens (robot "R." prefix, etc.)
        meaningful_shared = {k for k in shared if len(k) > 1}
        if not meaningful_shared:
            return False

        if not multi1 and not multi2:
            # Both single-word: require fuzzy similarity
            return fuzz_ratio(normalize_name(name1), normalize_name(name2)) >= FUZZY_THRESHOLD

        if multi1 and multi2:
            # Both multi-word: only merge if one keyword-set is a subset of
            # the other (pure abbreviation relationship).
            return kw1.issubset(kw2) or kw2.issubset(kw1)

        # Exactly one is single-word: merge if meaningful keyword IS in the
        # multi-word name's set.
        return bool(meaningful_shared)

    # No shared keywords: fuzzy fallback (multi-word involved only)
    if multi1 or multi2:
        return fuzz_ratio(normalize_name(name1), normalize_name(name2)) >= FUZZY_THRESHOLD

    return False


def group_aliases(LP: Counter) -> list:
    """
    Group surface names in LP (a Counter {name: count}) into alias clusters.

    Improvements over the original greedy approach:
    - Uses Union-Find for correct transitivity (order-independent).
    - Canonical name = most-frequent surface form in each cluster.
    - Ambiguity guard: a single-token name that appears in multiple distinct
      multi-word names (shared last/first name like "Darell") is pre-assigned
      to the most-frequent multi-word name only.
    - Fuzzy matching fallback for names with no keyword overlap.
    - Multi-word ↔ multi-word merging requires a proper keyword-set subset
      relationship, not just any overlap (prevents "Bayta Darell" merging
      with "Arcadia Darell" because they share the surname "Darell").

    Returns:
        list[list[str]]  where group[0] is the canonical (most-frequent) name.
    """
    names = [name for name, _ in LP.most_common()]
    uf = _UnionFind(names)
    kw_cache = {n: name_keywords(n) for n in names}

    # --- Pre-pass: resolve ambiguous single-token names ---
    # For each single-token name S, collect all multi-word names whose keyword
    # set contains S's single keyword.  If more than one multi-word name
    # matches, S is "ambiguous" and must only link to the most-frequent one.
    single_token_assignment: dict[str, str | None] = {}  # single_token → assigned multiword (or None if unambiguous)

    for name in names:
        kw = kw_cache[name]
        if len(kw) != 1:
            continue  # only care about single-token names
        (token,) = kw
        if len(token) <= 1:
            continue  # skip single-character tokens (robot "R." prefix, etc.)

        multiword_matches = [
            n for n in names
            if len(kw_cache[n]) > 1 and token in kw_cache[n]
        ]
        if len(multiword_matches) > 1:
            # Ambiguous: assign to most-frequent multi-word name
            best = max(multiword_matches, key=lambda n: LP.get(n, 0))
            single_token_assignment[name] = best
        elif len(multiword_matches) == 1:
            single_token_assignment[name] = multiword_matches[0]
        # else: no multi-word match, fuzzy will handle it later

    # --- Main merge pass ---
    for i, name in enumerate(names):
        kw1 = kw_cache[name]

        for j in range(i + 1, len(names)):
            other = names[j]
            if uf.find(name) == uf.find(other):
                continue  # already same group

            # Ambiguity guard for single-token names:
            # If `name` is a single-token with a pre-assigned multiword target,
            # only allow merging with that specific multiword name.
            if len(kw1) == 1 and name in single_token_assignment:
                if single_token_assignment[name] != other:
                    continue

            # Vice-versa: if `other` is a single-token with a pre-assigned
            # target, only allow the merge if `name` is that target.
            kw2 = kw_cache[other]
            if len(kw2) == 1 and other in single_token_assignment:
                if single_token_assignment[other] != name:
                    continue

            if _should_merge(name, other):
                uf.union(name, other)

    raw_groups = uf.groups()

    # Within each group, sort by frequency descending → group[0] is canonical
    result = []
    for group in raw_groups:
        sorted_group = sorted(group, key=lambda n: LP.get(n, 0), reverse=True)
        result.append(sorted_group)

    return result


def alias_dictionary(groups: list) -> dict:
    """
    Convert groups into {alias: canonical} mapping.
    group[0] (most-frequent surface form) is the canonical name.

    Returns:
        dict: { any_surface_form: canonical_name }
    """
    alias_map = {}
    for group in groups:
        canonical = group[0]
        for g in group:
            alias_map[g] = canonical
    return alias_map


def apply_gazetteer_aliases(alias_map: dict,
                             gazetteer_characters: dict,
                             lp: Counter | None = None) -> dict:
    """
    Force gazetteer groupings onto the alias map produced by alias_dictionary().

    For each {canonical: [alias, ...]} group in gazetteer_characters, all
    observed aliases are remapped to the same winning canonical.

    Canonical selection: the current alias-map canonical that "owns" the most
    LP weight (sum of raw counts for all surface forms pointing to it).  This
    means "Cléon" beats "Cleon I" when the French text never uses the English
    spelling, and "Elijah Baley" beats "Lije" because "Baley" and "Elijah"
    are already merged into it with a high combined count.

    Call order:
        alias_dictionary() → apply_gazetteer_aliases() → apply_manual_aliases()

    Args:
        alias_map:             {surface: auto_canonical} from alias_dictionary()
        gazetteer_characters:  {canonical: [alias, ...]} e.g. ASIMOV_CHARACTERS
        lp:                    raw Counter {surface: count} used to break ties

    Returns:
        dict: patched alias map
    """
    patched = dict(alias_map)

    for gaz_canonical, gaz_aliases in gazetteer_characters.items():
        all_forms = [gaz_canonical] + list(gaz_aliases)

        # Collect distinct current canonicals and their total LP weight
        current_canonicals: dict[str, int] = {}
        for form in all_forms:
            if form in patched:
                canon = patched[form]
                if canon not in current_canonicals:
                    weight = (
                        sum(lp.get(f, 0) for f, c in patched.items() if c == canon)
                        if lp is not None else 0
                    )
                    current_canonicals[canon] = weight

        if len(current_canonicals) <= 1:
            continue  # already consistent or nothing observed in this chapter

        best = max(current_canonicals, key=lambda c: current_canonicals[c])
        displaced = {c for c in current_canonicals if c != best}

        # Remap everything that pointed to a displaced canonical
        for k in list(patched):
            if patched[k] in displaced:
                patched[k] = best
        # Also directly remap any form that is listed in the gazetteer group
        for form in all_forms:
            if form in patched:
                patched[form] = best

    return patched


def apply_manual_aliases(alias_map: dict, manual_overrides: dict) -> dict:
    """
    Overlay a small set of hand-crafted aliases on top of an auto-generated
    alias_map.  Manual overrides always win.

    For every (surface, canonical) in manual_overrides:
    - surface is remapped to canonical.
    - Any entry in alias_map that previously pointed to surface is also
      redirected to canonical (transitive fix).

    Args:
        alias_map:        {surface: auto_canonical} from alias_dictionary()
        manual_overrides: {surface: desired_canonical}

    Returns:
        dict: patched alias map
    """
    patched = dict(alias_map)
    for surface, manual_canonical in manual_overrides.items():
        old_canonical = patched.get(surface, surface)
        patched[surface] = manual_canonical
        if old_canonical != manual_canonical:
            for k in list(patched):
                if patched[k] == old_canonical:
                    patched[k] = manual_canonical
    return patched


def merge_alias_counts(LP: Counter, alias_map: dict) -> Counter:
    """
    Merge counts of all alias forms into their canonical name.

    Args:
        LP: original Counter {surface_name: count}
        alias_map: {surface_name: canonical_name}

    Returns:
        Counter: {canonical_name: total_count}
    """
    merged = Counter()
    for name, count in LP.items():
        canonical = alias_map.get(name, name)
        merged[canonical] += count
    return merged


def filter_by_frequency(character_counts, min_occurrences=2):
    """
    Remove characters that appear fewer than min_occurrences times.
    Apply this AFTER merge_alias_counts so aliases are counted together.

    Args:
        character_counts (Counter): Merged character counts
        min_occurrences (int): Minimum number of mentions to keep a character

    Returns:
        Counter: Filtered character counts
    """
    return Counter({
        name: count
        for name, count in character_counts.items()
        if count >= min_occurrences
    })


# ---------------------------------------------------------------------------
# Smoke tests — run with: python3 nlp_aliases.py
# ---------------------------------------------------------------------------

def _test_alias_grouping():
    print(f"fuzzy backend: {'rapidfuzz' if _FUZZY_AVAILABLE else 'difflib'}")

    LP = Counter({
        "Hari Seldon": 50,
        "Seldon": 30,
        "Hari": 20,
        "Gaal Dornick": 15,
        "Dornick": 8,
        "Bayta Darell": 12,
        "Arcadia Darell": 10,
        "Darell": 6,
        "Elijah Baley": 40,
        "Baley": 25,
        "R. Daneel Olivaw": 35,
        "Daneel": 18,
        "R. Giskard": 10,
        "Giskard": 7,
        "Harinder": 3,   # should NOT merge with "Hari"
    })

    groups = group_aliases(LP)
    alias_map = alias_dictionary(groups)

    def same_group(a, b):
        return alias_map.get(a, a) == alias_map.get(b, b)

    tests = [
        # (name1, name2, expected_same, description)
        ("Hari Seldon", "Seldon", True,  "Seldon → Hari Seldon"),
        ("Hari Seldon", "Hari",   True,  "Hari → Hari Seldon"),
        ("Elijah Baley", "Baley", True,  "Baley → Elijah Baley"),
        ("R. Daneel Olivaw", "Daneel", True, "Daneel → R. Daneel Olivaw"),
        ("Gaal Dornick", "Dornick", True, "Dornick → Gaal Dornick"),
        # Ambiguity guard: "Darell" merges only with the most-frequent multi-word name
        ("Bayta Darell", "Arcadia Darell", False, "Bayta Darell ≠ Arcadia Darell (different chars)"),
        # Single-token false-positive guard
        ("Hari", "Harinder", False, "Hari ≠ Harinder (different people)"),
    ]

    passed = 0
    for a, b, expected, desc in tests:
        result = same_group(a, b)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        print(f"  [{status}] {desc}")

    print(f"\n{passed}/{len(tests)} tests passed.")

    # Show canonical names
    print("\nCanonical names (most-frequent surface form):")
    seen = set()
    for name, _ in LP.most_common():
        canonical = alias_map.get(name, name)
        if canonical not in seen:
            seen.add(canonical)
            group_members = [k for k, v in alias_map.items() if v == canonical]
            print(f"  {canonical!r:30s} ← {group_members}")


if __name__ == "__main__":
    _test_alias_grouping()
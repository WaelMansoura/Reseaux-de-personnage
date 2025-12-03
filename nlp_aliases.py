# alias_utils.py
import re
from collections import defaultdict, Counter
TITLES = [
    "mr", "mme", "mrs", "ms", "dr", "prof", "sir",
    "m", "mlle", "lord", "maître", "colonel"
]

def normalize_name(name: str):
    """
    Normalize person name for alias matching.
    - lowercase
    - remove titles
    - remove punctuation
    - trim spaces
    """

    n = name.lower().strip()

    # remove titles
    for t in TITLES:
        n = re.sub(rf"\b{t}\b", "", n)

    # remove punctuation
    n = re.sub(r"[^\w\sàâäéèêëîïôöùûüç-]", "", n)

    # remove extra spaces
    n = re.sub(r"\s+", " ", n).strip()

    return n


def name_keywords(name: str):
    """Return the set of words (keywords) in normalized name."""
    return set(normalize_name(name).split())


def group_aliases(LP):
    """
    LP is a Counter: { surface_name: count }
    Returns:
        groups: list of lists, e.g. [["Hari Seldon", "Seldon"], ["Gaal Dornick", "Dornick"]]
    """

    names = list(LP.keys())
    groups = []
    visited = set()

    for i, name in enumerate(names):
        if name in visited:
            continue

        kw1 = name_keywords(name)
        group = [name]
        visited.add(name)

        for j in range(i + 1, len(names)):
            other = names[j]
            if other in visited:
                continue

            kw2 = name_keywords(other)

            # simple rule: share at least one keyword
            if kw1 & kw2:
                group.append(other)
                visited.add(other)

        groups.append(group)

    return groups


def alias_dictionary(groups):
    """
    Convert groups into alias → canonical
    First name in each group becomes the canonical one.
    Returns:
        dict: { alias: canonical }
    """

    alias_map = {}

    for group in groups:
        canonical = group[0]
        for g in group:
            alias_map[g] = canonical

    return alias_map

def merge_alias_counts(LP, alias_map):
    """
    Create final LP where aliases are merged into canonical names.
    LP is original Counter.
    alias_map: alias → canonical_name
    """

    merged = Counter()

    for name, count in LP.items():
        canonical = alias_map.get(name, name)
        merged[canonical] += count

    return merged
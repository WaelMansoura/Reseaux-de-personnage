"""
nlp_relation.py
---------------
Relationship type labeling for character co-occurrence edges.

Primary approach : zero-shot NLI (MoritzLaurer/mDeBERTa-v3-base-mnli-xnli)
Fallback         : returns "neutral" on any error
Cache            : caller passes a dict keyed on (chapter_id, charA, charB)

Typical usage:
    edge_labels = label_relationships(
        text, cooccurrences, alias_map,
        distance_max=distance_max,
        chapter_id=chapter_id,
        cache=relation_cache,
    )
    G = generate_graph(cooccurrences, LP_merged, alias_map=alias_map, edge_labels=edge_labels)
"""

import re
import functools
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration — adjust these without changing any other code
# ---------------------------------------------------------------------------

NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

# French label hypotheses fed to the NLI model.
# Wording matters — keep these as simple declarative statements.
LABELS_FR = [
    "ces deux personnages ont une relation amicale",
    "ces deux personnages ont une relation hostile",
    "ces deux personnages ont une relation neutre",
]

# Map NLI French hypothesis → output edge_type string
LABEL_MAP = {
    "ces deux personnages ont une relation amicale": "friendly",
    "ces deux personnages ont une relation hostile": "hostile",
    "ces deux personnages ont une relation neutre":  "neutral",
}

# Minimum average NLI confidence to commit to a non-neutral label.
# If the winning label's average confidence is below this threshold, fall back to "neutral".
# Raise to 0.65 if you see too many false friendly/hostile labels.
CONFIDENCE_THRESHOLD = 0.55

# Maximum snippets classified per pair (caps batch size; takes earliest co-occurrences)
MAX_CONTEXTS_PER_PAIR = 5

# Characters sent to the NLI model per snippet (long windows are truncated)
MAX_SNIPPET_CHARS = 400


# ---------------------------------------------------------------------------
# Model loading — lazy singleton, loaded once per process
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _get_classifier():
    """Load the NLI classifier once and reuse across all calls."""
    from transformers import pipeline as hf_pipeline
    print(f"[nlp_relation] Loading NLI model: {NLI_MODEL}  (first call only — ~350 MB download)")
    clf = hf_pipeline(
        "zero-shot-classification",
        model=NLI_MODEL,
        device=-1,          # CPU; set to 0 for GPU if available
        multi_label=False,
    )
    print("[nlp_relation] Model ready.")
    return clf


# ---------------------------------------------------------------------------
# Context extraction
# ---------------------------------------------------------------------------

def extract_cooccurrence_contexts(
    text: str,
    charA: str,
    charB: str,
    alias_map: Dict[str, str],
    distance_max: int = 100,
    max_contexts: int = MAX_CONTEXTS_PER_PAIR,
) -> List[str]:
    """
    Return up to `max_contexts` raw prose snippets in which charA and charB
    co-appear within `distance_max` word tokens of each other.

    Parameters
    ----------
    text         : raw chapter text
    charA / charB: canonical character names
    alias_map    : {surface_form: canonical_name}
    distance_max : same window size used for co-occurrence detection
    max_contexts : cap on returned snippets (takes earliest occurrences)

    Returns
    -------
    List of raw text substrings; may be empty if the pair never co-appears.
    """
    # Build full alias sets for each character (including the canonical name itself)
    aliases_A = {sf for sf, canon in alias_map.items() if canon == charA} | {charA}
    aliases_B = {sf for sf, canon in alias_map.items() if canon == charB} | {charB}

    # Tokenize preserving character offsets (re.finditer keeps start/end positions)
    token_matches = list(re.finditer(r"\S+", text))
    token_texts_lower = [m.group().lower() for m in token_matches]
    n = len(token_matches)

    def find_positions(aliases: set) -> List[int]:
        """Return all token indices where any alias surface form begins."""
        positions = []
        for alias in aliases:
            alias_tokens = alias.lower().split()
            alen = len(alias_tokens)
            for i in range(n - alen + 1):
                if token_texts_lower[i : i + alen] == alias_tokens:
                    positions.append(i)
        return sorted(set(positions))

    pos_A = find_positions(aliases_A)
    pos_B = find_positions(aliases_B)

    contexts: List[str] = []
    used_windows: set = set()

    for a in pos_A:
        for b in pos_B:
            if abs(a - b) <= distance_max:
                win_start = min(a, b)
                win_end   = max(a, b) + 1
                window_key = (win_start, win_end)
                if window_key in used_windows:
                    continue
                used_windows.add(window_key)

                # Recover the raw text span via character offsets
                char_start = token_matches[win_start].start()
                char_end   = token_matches[min(win_end, n - 1)].end()
                snippet = text[char_start:char_end].strip()
                contexts.append(snippet)

                if len(contexts) >= max_contexts:
                    return contexts

    return contexts


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _aggregate_votes(votes: List[Tuple[str, float]]) -> str:
    """
    Confidence-weighted majority vote over per-snippet NLI results.

    Sums raw confidence scores per French hypothesis label across all snippets,
    normalises to a per-snippet average, and returns the LABEL_MAP-translated
    winner.  Falls back to "neutral" if the normalised winning score is below
    CONFIDENCE_THRESHOLD (avoids committing on weak/ambiguous signal).
    """
    if not votes:
        return "neutral"

    scores: Dict[str, float] = defaultdict(float)
    for label_fr, confidence in votes:
        scores[label_fr] += confidence

    winner_fr    = max(scores, key=scores.get)
    winner_score = scores[winner_fr] / len(votes)   # per-snippet average

    if winner_score < CONFIDENCE_THRESHOLD:
        return "neutral"

    return LABEL_MAP.get(winner_fr, "neutral")


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_relationship(
    context_snippets: List[str],
    charA: str,
    charB: str,
) -> str:
    """
    Classify the relationship type between charA and charB from text snippets.

    Returns
    -------
    "friendly" | "hostile" | "neutral"
    """
    if not context_snippets:
        return "neutral"

    clf = _get_classifier()

    # Prepend character names so the NLI model knows which pair to judge
    enriched = [
        f"[{charA}] et [{charB}] : {snippet[:MAX_SNIPPET_CHARS]}"
        for snippet in context_snippets
    ]

    per_snippet_votes: List[Tuple[str, float]] = []

    try:
        results = clf(enriched, LABELS_FR, batch_size=4)
        if not isinstance(results, list):
            results = [results]

        for result in results:
            top_label = result["labels"][0]
            top_score = result["scores"][0]
            per_snippet_votes.append((top_label, top_score))

    except Exception as exc:
        print(f"[classify_relationship] Error classifying {charA} ↔ {charB}: {exc}")
        return "neutral"

    return _aggregate_votes(per_snippet_votes)


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def label_relationships(
    text: str,
    cooccurrences: Counter,
    alias_map: Dict[str, str],
    distance_max: int = 100,
    chapter_id: str = "",
    cache: Optional[Dict] = None,
) -> Dict[tuple, str]:
    """
    Label every co-occurring character pair in a chapter.

    Parameters
    ----------
    text          : raw chapter text
    cooccurrences : Counter{(charA, charB): count}  — from detect_cooccurrences()
    alias_map     : {surface_form: canonical_name}
    distance_max  : window size used for context extraction
    chapter_id    : e.g. "paf0" — part of the cache key
    cache         : shared dict mutated in-place; keys are (chapter_id, canonA, canonB)

    Returns
    -------
    dict{(charA, charB): edge_type_string}

    Cache key: (chapter_id, canonA, canonB) where canonA < canonB (sorted).

    NOTE: Changing `distance_max` does NOT bust the cache — the relationship
    label for a pair is stable across small window changes. Only invalidate
    the cache when you change NLI_MODEL or CONFIDENCE_THRESHOLD.
    """
    edge_labels: Dict[tuple, str] = {}
    new_pairs = 0

    for (charA, charB) in cooccurrences:
        canon_pair = tuple(sorted([charA, charB]))
        cache_key  = (chapter_id,) + canon_pair

        # Cache hit — skip inference entirely
        if cache is not None and cache_key in cache:
            edge_labels[(charA, charB)] = cache[cache_key]
            continue

        snippets = extract_cooccurrence_contexts(
            text, charA, charB, alias_map, distance_max
        )
        label = classify_relationship(snippets, charA, charB)
        edge_labels[(charA, charB)] = label
        new_pairs += 1

        if cache is not None:
            cache[cache_key] = label

    if new_pairs > 0:
        print(f"   🏷️  Labeled {new_pairs} new pairs", end="  ")

    return edge_labels


# ---------------------------------------------------------------------------
# Validation utility
# ---------------------------------------------------------------------------

def print_validation_report(
    text: str,
    edge_labels: Dict[tuple, str],
    alias_map: Dict[str, str],
    distance_max: int,
    chapter_id: str = "",
    n: int = 5,
) -> None:
    """
    Print the top-n hostile and top-n friendly edges with a driving snippet each.
    Run this after the first full pass to spot-check label quality.

    If labels look wrong, try raising CONFIDENCE_THRESHOLD in this module
    or switching NLI_MODEL to "cmarkea/distilcamembert-base-nli".
    """
    hostile  = [(pair, lbl) for pair, lbl in edge_labels.items() if lbl == "hostile"][:n]
    friendly = [(pair, lbl) for pair, lbl in edge_labels.items() if lbl == "friendly"][:n]
    neutral  = [(pair, lbl) for pair, lbl in edge_labels.items() if lbl == "neutral"][:n]

    counts = {
        "friendly": sum(1 for l in edge_labels.values() if l == "friendly"),
        "hostile":  sum(1 for l in edge_labels.values() if l == "hostile"),
        "neutral":  sum(1 for l in edge_labels.values() if l == "neutral"),
    }

    print(f"\n{'='*60}")
    print(f"  VALIDATION REPORT — chapter {chapter_id}")
    print(f"  Total edges: {len(edge_labels)}  |  "
          f"friendly: {counts['friendly']}  hostile: {counts['hostile']}  neutral: {counts['neutral']}")
    print(f"{'='*60}")

    for group_name, group in [("HOSTILE", hostile), ("FRIENDLY", friendly)]:
        if not group:
            continue
        print(f"\n── {group_name} ──")
        for (charA, charB), label in group:
            snippets = extract_cooccurrence_contexts(
                text, charA, charB, alias_map, distance_max, max_contexts=1
            )
            preview = snippets[0][:200].replace("\n", " ") if snippets else "(no snippet found)"
            print(f"  {charA} ↔ {charB}")
            print(f"  « {preview}… »\n")

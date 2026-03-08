# Relationship Labeling — Final Implementation Plan

**Synthesis of research from ChatGPT extended thinking + Claude extended thinking,
reviewed and finalized.**

---

## Decision Summary

**Use zero-shot NLI classification (`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`) as the
primary engine, with a JSON/pickle cache keyed on `(chapter_id, charA, charB)`.
If manual spot-checking reveals poor quality, escalate to one batch of Mistral API calls
at `temperature=0` and store the results permanently in the same cache.**

Rationale:

| Criterion        | Why NLI wins                                               |
| ---------------- | ---------------------------------------------------------- |
| No labeled data  | Zero-shot — no annotation needed                           |
| French support   | mDeBERTa trained on multilingual XNLI, strong on French    |
| CPU feasible     | ~1–3 s/snippet on Colab free tier; batchable               |
| Deterministic    | Greedy inference; cache makes it fully reproducible        |
| Student-friendly | 5 lines via HuggingFace `pipeline()`                       |
| Quality ceiling  | Good for 3-class; escalation path exists (LLM API, cached) |

Approaches **rejected**:

- **Sentiment alone**: sentiment ≠ relationship. In Asimov's heavily expository prose, two
  allied characters will often appear in passages with zero affective vocabulary, giving a
  false "neutral."
- **Dependency rules**: high precision but near-zero recall on literary text. Useful only
  as a hard-override for a small lexicon of obvious patterns (see §5).
- **Fine-tuned transformer**: requires labeled data we don't have.
- **Local GGUF LLM**: too slow for interactive development on Colab CPU. Reserve as
  the quality-escalation step (see §7).

---

## Taxonomy

Start with **3 classes** for semester 2. Expand to 5 only if the 3-class system is working
and time allows (see §8).

| Label      | Meaning                                                     |
| ---------- | ----------------------------------------------------------- |
| `friendly` | Alliance, cooperation, trust, warmth, mentorship            |
| `hostile`  | Conflict, opposition, distrust, antagonism                  |
| `neutral`  | Functional / transactional co-presence; insufficient signal |

> **Asimov-specific note**: His chapters are often expository or philosophical — long
> passages where characters debate mathematics, politics, or sociology without emotive
> language. Expect a high proportion of `neutral` labels even for pairs with an
> established relationship. This is not a bug. Consider it a signal that the _chapter_
> does not contain interaction evidence, even if the characters are allies elsewhere.

---

## Architecture Overview

The new step inserts between `detect_cooccurrences` and `generate_graph`:

```
detect_cooccurrences(text, LP_merged, distance_max)
    → Counter{(charA, charB): count}
            │
            ▼   NEW: nlp_relation.py
label_relationships(text, cooccurrences, alias_map, distance_max, cache)
    → dict{(charA, charB): "friendly" | "hostile" | "neutral"}
            │
            ▼
generate_graph(cooccurrences, LP_merged, alias_map, edge_labels)
    → nx.Graph  [edges now have 'edge_type' attribute]
```

New file: **`nlp_relation.py`**
Modified files: `nlp_graph.py`, `nlp_create_submission.py`, `new.ipynb` (Section 4)

---

## `nlp_relation.py` — Full Implementation

```python
"""
nlp_relation.py
---------------
Relationship type labeling for character co-occurrence edges.

Primary approach : zero-shot NLI (mDeBERTa-v3-base-mnli-xnli)
Fallback         : returns "neutral" on any error
Cache            : caller passes a dict keyed on (chapter_id, charA, charB)
"""

import re
import functools
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

# French label hypotheses fed to the NLI model.
# Wording matters — keep these as simple declarative statements.
LABELS_FR = [
    "ces deux personnages ont une relation amicale",
    "ces deux personnages ont une relation hostile",
    "ces deux personnages ont une relation neutre",
]

# Map NLI hypothesis → output edge_type string
LABEL_MAP = {
    "ces deux personnages ont une relation amicale": "friendly",
    "ces deux personnages ont une relation hostile": "hostile",
    "ces deux personnages ont une relation neutre":  "neutral",
}

# Minimum NLI confidence to commit to a non-neutral label.
# If the top score is below this threshold, default to "neutral".
# Tune upward (e.g. 0.65) if you see too many false friendly/hostile labels.
CONFIDENCE_THRESHOLD = 0.55

# Maximum snippets to classify per pair (avoids batching 50 near-identical windows)
MAX_CONTEXTS_PER_PAIR = 5

# Max token length sent to the NLI model (truncate long windows)
MAX_SNIPPET_CHARS = 400


# ---------------------------------------------------------------------------
# Model loading (lazy singleton)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _get_classifier():
    """Load the NLI classifier once; reuse across all calls."""
    from transformers import pipeline as hf_pipeline
    print(f"[nlp_relation] Loading NLI model: {NLI_MODEL} (first call only)…")
    return hf_pipeline(
        "zero-shot-classification",
        model=NLI_MODEL,
        device=-1,          # CPU
        multi_label=False,
    )


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
    text        : raw chapter text
    charA/charB : canonical character names
    alias_map   : {surface_form: canonical_name}
    distance_max: same window size used for co-occurrence detection
    max_contexts: cap on number of returned snippets (take earliest occurrences)

    Returns
    -------
    List of text substrings (may be empty if the pair never co-appears).
    """
    # Build alias sets for each canonical character
    aliases_A = {sf for sf, canon in alias_map.items() if canon == charA} | {charA}
    aliases_B = {sf for sf, canon in alias_map.items() if canon == charB} | {charB}

    # Tokenize, preserving character offsets
    token_matches = list(re.finditer(r"\S+", text))
    token_texts_lower = [m.group().lower() for m in token_matches]
    n = len(token_matches)

    def find_positions(aliases: set) -> List[int]:
        """Token indices where any alias surface form starts."""
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

    contexts = []
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

                # Extract raw text from the start of the first token to end of last
                char_start = token_matches[win_start].start()
                char_end   = token_matches[min(win_end, n - 1)].end()
                snippet = text[char_start:char_end].strip()
                contexts.append(snippet)

                if len(contexts) >= max_contexts:
                    return contexts

    return contexts


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _aggregate_votes(votes: List[Tuple[str, float]]) -> str:
    """
    Confidence-weighted majority vote over per-snippet NLI results.

    Sums confidence scores per label (French hypothesis strings) across all
    snippets; returns the LABEL_MAP-translated label with the highest total.
    Falls back to "neutral" if no confident vote exceeds CONFIDENCE_THRESHOLD.
    """
    if not votes:
        return "neutral"

    scores: Dict[str, float] = defaultdict(float)
    for label_fr, confidence in votes:
        scores[label_fr] += confidence

    winner_fr    = max(scores, key=scores.get)
    winner_score = scores[winner_fr] / len(votes)   # normalise to per-snippet avg

    # If the average confidence of the winning label is below threshold, be
    # conservative and return neutral — avoids committing to a label on weak signal.
    if winner_score < CONFIDENCE_THRESHOLD:
        return "neutral"

    return LABEL_MAP.get(winner_fr, "neutral")


def classify_relationship(
    context_snippets: List[str],
    charA: str,
    charB: str,
) -> str:
    """
    Classify the relationship type between charA and charB given a list of
    co-occurrence text snippets.

    Returns: "friendly" | "hostile" | "neutral"
    """
    if not context_snippets:
        return "neutral"

    clf = _get_classifier()

    # Prepend character names so the NLI model knows whose relationship to judge.
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
        print(f"[classify_relationship] Error classifying {charA}↔{charB}: {exc}")
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
    Label every co-occurring character pair in the chapter.

    Parameters
    ----------
    text          : raw chapter text
    cooccurrences : Counter{(charA, charB): count}  from detect_cooccurrences()
    alias_map     : {surface_form: canonical_name}
    distance_max  : window size (used for context extraction)
    chapter_id    : e.g. "paf0" — used as part of cache key
    cache         : shared dict; mutated in-place with new results

    Returns
    -------
    dict{(charA, charB): edge_type_string}

    Cache key format: (chapter_id, canonA, canonB) where canonA < canonB (sorted).
    Changing `distance_max` does NOT bust the cache — the relationship label for a
    pair rarely changes when the window is slightly wider. Only invalidate the cache
    when you change the labeling model or confidence threshold.
    """
    edge_labels: Dict[tuple, str] = {}

    for (charA, charB) in cooccurrences:
        canon_pair = tuple(sorted([charA, charB]))
        cache_key  = (chapter_id,) + canon_pair

        # Cache hit
        if cache is not None and cache_key in cache:
            edge_labels[(charA, charB)] = cache[cache_key]
            continue

        snippets = extract_cooccurrence_contexts(
            text, charA, charB, alias_map, distance_max
        )
        label = classify_relationship(snippets, charA, charB)
        edge_labels[(charA, charB)] = label

        if cache is not None:
            cache[cache_key] = label

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
    """
    hostile  = [(p, l) for p, l in edge_labels.items() if l == "hostile"][:n]
    friendly = [(p, l) for p, l in edge_labels.items() if l == "friendly"][:n]

    for group_name, group in [("HOSTILE", hostile), ("FRIENDLY", friendly)]:
        print(f"\n{'='*60}")
        print(f"  {group_name} edges — chapter {chapter_id}")
        print(f"{'='*60}")
        for (charA, charB), label in group:
            snippets = extract_cooccurrence_contexts(
                text, charA, charB, alias_map, distance_max, max_contexts=1
            )
            snippet_preview = snippets[0][:200] if snippets else "(no snippet found)"
            print(f"\n  {charA} ↔ {charB}")
            print(f"  Snippet: …{snippet_preview}…")
```

---

## Changes to `nlp_graph.py`

Add `edge_labels` parameter to `generate_graph()`:

```python
def generate_graph(
    cooccurrences,
    character_counts,
    alias_map=None,
    edge_labels=None,       # NEW: dict{(charA, charB): str} | None
) -> nx.Graph:
    G = nx.Graph()
    # ... existing node creation logic (unchanged) ...

    for (charA, charB), weight in cooccurrences.items():
        G.add_edge(charA, charB, weight=weight)
        if edge_labels:
            pair  = (charA, charB)
            rpair = (charB, charA)
            etype = edge_labels.get(pair) or edge_labels.get(rpair, "neutral")
            G[charA][charB]["edge_type"] = etype

    return G
```

The `edge_type` attribute becomes a standard GraphML `<data>` field and will appear
automatically in `nx.generate_graphml(G)` output.

---

## Changes to the Notebook (Section 4)

### New cell: load/initialize relation cache (add before the main loop)

```python
import pickle, os

RELATION_CACHE_FILE = "relation_cache.pkl"
relation_cache = {}

if os.path.exists(RELATION_CACHE_FILE):
    with open(RELATION_CACHE_FILE, "rb") as f:
        relation_cache = pickle.load(f)
    print(f"✅ Loaded {len(relation_cache)} cached relation labels.")
else:
    print("ℹ️  No relation cache found — will classify from scratch.")
```

### Modified main loop (Section 4, inside the chapter loop)

Replace:

```python
cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
G = generate_graph(cooccurrences, LP_merged, alias_map=alias_map)
```

With:

```python
from nlp_relation import label_relationships

cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)

edge_labels = label_relationships(
    text,
    cooccurrences,
    alias_map,
    distance_max=distance_max,
    chapter_id=chapter_id,
    cache=relation_cache,
)

G = generate_graph(
    cooccurrences,
    LP_merged,
    alias_map=alias_map,
    edge_labels=edge_labels,
)
```

### New cell: save cache after loop

```python
with open(RELATION_CACHE_FILE, "wb") as f:
    pickle.dump(relation_cache, f)
print(f"💾 Relation cache saved ({len(relation_cache)} entries).")
```

### Optional: spot-check cell

```python
from nlp_relation import print_validation_report

# Inspect a specific chapter — change chapter_id as needed
inspect_id = "paf0"
if inspect_id in ner_cache:
    print_validation_report(
        text         = ner_cache[inspect_id]["text"],
        edge_labels  = edge_labels_per_chapter[inspect_id],  # store per chapter if needed
        alias_map    = alias_map_per_chapter[inspect_id],
        distance_max = distance_max,
        chapter_id   = inspect_id,
        n            = 5,
    )
```

---

## Installation

Add to the pip install cell at the top of the notebook:

```python
!pip install transformers torch
# spacy/stanza/flair already installed in step 1
```

The NLI model (~350 MB) will auto-download on first call and be cached by HuggingFace
in `~/.cache/huggingface/`.

---

## Caching Strategy

| Cache key    | `(chapter_id, canonA, canonB)` where `canonA < canonB` (sorted)                                                                                                                  |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cache file   | `relation_cache.pkl` (pickle) in the project directory                                                                                                                           |
| Invalidation | **Only** when you change the NLI model or `CONFIDENCE_THRESHOLD`. Changing `distance_max` does NOT invalidate — the relationship label for a pair is stable across window sizes. |
| Persistence  | Save after every full run so kernel restarts don't re-classify.                                                                                                                  |

---

## Quality Escalation Path

If manual spot-checking (or grader feedback) shows the NLI labels are too noisy:

1. **Raise `CONFIDENCE_THRESHOLD`** from 0.55 → 0.65. This will label more pairs
   "neutral" but improve precision on the labels that do fire.

2. **Try `cmarkea/distilcamembert-base-nli`** as an alternative model — it is
   French-specific and may handle literary prose better than the multilingual mDeBERTa.
   Swap `NLI_MODEL` at the top of `nlp_relation.py`.

3. **Use Mistral API (one-time batch)**: Call `mistral-medium` or `mistral-large`
   at `temperature=0` for each pair+snippet, save results to the relation cache, and never
   re-call. This produces near-human quality labels at the cost of an API call (~37 chapters
   × ~15 pairs = ~555 calls, well within free-tier rate limits).

   Prompt template:

   ```
   Texte extrait d'un roman de science-fiction en français :
   « {snippet} »

   Question : Dans ce passage, la relation entre {charA} et {charB} est-elle
   plutôt amicale, hostile, ou neutre ?
   Réponds uniquement par un seul mot : amicale, hostile, ou neutre.
   ```

4. **Add hard-override rules** (dependency heuristics) for a small lexicon of obvious
   patterns — these override the NLI result for clear-cut cases only:

   ```python
   HOSTILE_VERBS  = {"tuer", "attaquer", "haïr", "détester", "arrêter", "poursuivre"}
   FRIENDLY_VERBS = {"aider", "protéger", "sauver", "remercier", "sourire", "confier"}

   def dependency_override(text_snippet, charA, charB) -> Optional[str]:
       # parse with spaCy; if a HOSTILE_VERB connects the two characters: return "hostile"
       # if a FRIENDLY_VERB connects them: return "friendly"
       # otherwise: return None  (no override, let NLI decide)
   ```

   Apply this before calling the NLI model; if `dependency_override` returns a label,
   skip the NLI call for that snippet entirely.

---

## Taxonomy Expansion (Semester 3 / Optional)

The 3-class system can be expanded to 5 classes once it is stable:

| Label      | Meaning                                    | Additional signals needed                                  |
| ---------- | ------------------------------------------ | ---------------------------------------------------------- |
| `ally`     | Active cooperation toward a shared goal    | Cooperative action verbs, shared plans                     |
| `mentor`   | Asymmetric knowledge/guidance relationship | "expliquer à", "enseigner", "guider", titles like "maître" |
| `hostile`  | Conflict, opposition                       | (same as 3-class)                                          |
| `romantic` | Affective/intimate                         | Terms of endearment, "aimer", "embrasser", proximity cues  |
| `neutral`  | No clear signal                            | (same as 3-class)                                          |

**Practical limits**:

- 3-class (friendly/hostile/neutral): reliable with mDeBERTa zero-shot ✅
- 5-class (ally/mentor/hostile/romantic/neutral): workable with Mistral API, one-time batch ⚠️
- 7+ classes: not reliable without ≥50 labeled examples per class ❌

For multi-label edges (e.g. a character who is simultaneously a mentor and an ally):
keep `edge_type` as the single best label, and optionally add `edge_type_secondary` as
a separate GraphML attribute — do not encode semicolon-separated lists in the primary
field, as this breaks any downstream tool that expects a scalar.

---

## Summary of Files to Create / Modify

| File                       | Action     | What changes                                                                                                |
| -------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| `nlp_relation.py`          | **Create** | New module: context extraction, NLI classification, aggregation, cache orchestration, validation report     |
| `nlp_graph.py`             | **Modify** | `generate_graph()` gains `edge_labels` parameter; writes `edge_type` attribute on edges                     |
| `nlp_create_submission.py` | **Modify** | `process_chapter()` gains `relation_cache` parameter; calls `label_relationships()`                         |
| `new.ipynb` Section 1      | **Modify** | Add `transformers` and `torch` to the pip install cell                                                      |
| `new.ipynb` Section 4      | **Modify** | Add cache load cell, insert `label_relationships()` call, add cache save cell, add optional spot-check cell |

# Part 1 — Research Report: NLP Techniques for Relationship Classification

## 1. Zero-Shot Classification with a Multilingual NLI Model

**How it works**: A cross-encoder NLI model (trained on natural-language inference) is repurposed as a zero-shot classifier. You feed it a text snippet plus a hypothesis like "Ces deux personnages ont une relation amicale" and it outputs an entailment probability. The `transformers` pipeline `zero-shot-classification` automates this.

**Best model for French**: `joeddav/xlm-roberta-large-xnli` or `facebook/bart-large-mnli` won't work well on French; use instead `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` (solid multilingual NLI, well-maintained, ~350 MB, CPU-feasible). Candidate labels: `["relation amicale", "relation hostile", "relation neutre"]`.

**Suitability**: ★★★★☆. No labeled data needed, deterministic (greedy decoding), French supported, runs on CPU in ~1–3 seconds per snippet. Main failure modes: NLI models tend to anchor on surface-level sentiment in the label string rather than actually reading the narrative context — labels that sound positive/negative will bias the output even if the snippet is ambiguous. Also struggles with indirect/complex literary phrasing.

---

## 2. Sentiment / Tone Analysis on the Context Window

**How it works**: Extract the co-occurrence window and assign a sentiment polarity. Map positive → friendly, negative → hostile, near-zero → neutral.

**Best models**:

- `cmarkea/distilcamembert-base-sentiment` (CamemBERT-based, 3-class: positive/negative/neutral, ~260 MB, CPU-fast)
- `lxyuan/distilbert-base-multilingual-cased-sentiments-student` (multilingual, faster)
- Lexicon: French SentiWordNet / FEEL lexicon if you want zero-download fallback

**Suitability**: ★★★☆☆. Fast, simple, deterministic. But sentiment ≠ relationship type. "Baley poussa Daneel contre le mur" (hostile action) might read as neutral sentiment. Conversations can be warm even between adversaries. Usable as a signal but not as a sole classifier — works best combined with another approach.

---

## 3. Prompted LLM Classification (Zero-Shot / Few-Shot)

**How it works**: Feed the snippet to an LLM with a structured prompt asking for a classification. Two sub-options:

- **API-based** (Mistral API, OpenAI): Excellent quality, non-deterministic unless `temperature=0`, requires an account/key, not reproducible offline, introduces network dependency. Good for generating a cached result once and saving it.
- **Local quantized model**: Mistral-7B-Instruct or Llama-3.1-8B in GGUF format via `llama-cpp-python`. Runs on CPU but is slow (~10–60 sec/snippet depending on hardware). On Colab free tier this is borderline feasible if you limit yourself to ~200 snippets total.

**Suitability**: ★★★★★ for quality, ★★☆☆☆ for speed/simplicity. If you call the API once, cache all results to disk, and never re-call unless the pair/window changes — this is actually very practical and produces by far the best labels. The caching constraint in the project spec makes this viable.

**Recommended model for local**: `mistral-7b-instruct-v0.3.Q4_K_M.gguf` — ~4 GB, runs on Colab CPU with `llama-cpp-python`.

---

## 4. Dependency-Based Heuristic Rules

**How it works**: Parse the snippet with spaCy's `fr_core_news_lg` dependency parser. Look for:

- Subject–verb–object triples where charA and charB are the subject/object: verb lemma mapped to a sentiment lexicon (e.g. "aider" → friendly, "attaquer" → hostile)
- Adjectives modifying character names (e.g. "son ami Daneel" → friendly)
- Co-reference cues ("il lui sourit" near both names)

**Suitability**: ★★☆☆☆. Fully deterministic, zero-download, very fast. But: French literary prose is complex; dependency errors compound; coverage is low (many co-occurrences won't have a clear subject-verb-object triple spanning both characters in the window). Works well as a high-precision/low-recall fallback signal.

---

## 5. Fine-Tuned Transformer

**How it works**: Take a pre-trained French/multilingual model (CamemBERT, XLM-R) and fine-tune on relation-classification examples. For few-shot fine-tuning, you'd need at minimum ~50–200 labeled examples per class, obtainable by manually annotating ~150 snippets from your own corpus.

**Suitability**: ★★☆☆☆ right now. Without labeled data and with only 37 chapters, this is not feasible in semester 2. PEFT/LoRA reduces compute cost but doesn't solve the labeling data problem. Worth noting for a potential semester 3 extension.

---

## 6. Aggregation Strategy

Each character pair can have many co-occurrence windows. Strategies:

- **Majority vote**: Assign the most frequent label across all windows. Simple, robust.
- **Confidence-weighted vote**: If your classifier outputs probabilities, weight each window's vote by its max confidence score. Better than raw majority.
- **Recency-weighted**: Weight windows later in the chapter more (relationships evolve). Complex to implement.
- **First-and-last**: Take the label from the highest-weight window (most co-occurring) only.

**Recommendation**: confidence-weighted majority vote with a fallback to `"neutral"` on ties.

---

## ✅ Recommendation

**Use zero-shot NLI classification (`mDeBERTa-v3-base-mnli-xnli`) as your primary approach, with sentiment analysis as a secondary signal, and cache everything.**

Rationale:

- No API key needed, runs on Colab CPU in reasonable time (~1–2 sec/snippet)
- French language well-supported
- Simple to integrate (5–10 lines of code using `pipeline()`)
- Deterministic at inference time (use `torch.no_grad()` + fixed seeds)
- Student-friendly: HuggingFace `pipeline` is well-documented

If quality is insufficient after manual spot-checking, escalate to a one-time API call (Mistral/OpenAI, `temperature=0`) with results saved to a JSON cache file.

---

# Part 2 — Implementation Plan

## 1. Context Extraction

**Algorithm**: For each co-occurrence pair `(charA, charB)`, find every window position where both appear together. For each such window, return the raw text slice (not tokenized).

```python
# nlp_relation.py

import re
from typing import Dict, List, Tuple

def extract_cooccurrence_contexts(
    text: str,
    charA: str,
    charB: str,
    alias_map: Dict[str, str],   # surface_form -> canonical
    distance_max: int = 100,
    max_contexts: int = 5,        # cap to avoid huge batches
) -> List[str]:
    """
    Returns up to max_contexts text snippets (raw prose) in which
    charA and charB co-appear within distance_max tokens.
    """
    # Build alias sets for each canonical character
    aliases_A = {sf for sf, canon in alias_map.items() if canon == charA}
    aliases_A.add(charA)
    aliases_B = {sf for sf, canon in alias_map.items() if canon == charB}
    aliases_B.add(charB)

    # Tokenize to find positions (token index -> char offset)
    tokens = list(re.finditer(r"\S+", text))  # preserves char offsets
    token_texts_lower = [t.group().lower() for t in tokens]

    def find_token_positions(aliases: set) -> List[int]:
        positions = []
        for alias in aliases:
            alias_tokens = alias.lower().split()
            n = len(alias_tokens)
            for i in range(len(token_texts_lower) - n + 1):
                if token_texts_lower[i:i+n] == alias_tokens:
                    positions.append(i)
        return sorted(set(positions))

    pos_A = find_token_positions(aliases_A)
    pos_B = find_token_positions(aliases_B)

    contexts = []
    used_windows = set()

    for a in pos_A:
        for b in pos_B:
            if abs(a - b) <= distance_max:
                window_start = min(a, b)
                window_end   = max(a, b) + 1
                key = (window_start, window_end)
                if key in used_windows:
                    continue
                used_windows.add(key)

                # Extract raw text from the surrounding token span
                char_start = tokens[window_start].start()
                char_end   = tokens[min(window_end + 5, len(tokens) - 1)].end()
                contexts.append(text[char_start:char_end])

                if len(contexts) >= max_contexts:
                    return contexts

    return contexts
```

**Design choices explained**:

- We use `re.finditer(r"\S+")` to keep character offsets while still doing token-distance math.
- We cap at `max_contexts=5` to avoid sending 50 nearly-identical snippets to the classifier.
- If a pair co-occurs many times, we take the first 5 windows (earliest in the chapter). You could instead sample the 5 highest-weight windows if you pre-rank them.

---

## 2. Labeling Function

```python
# nlp_relation.py (continued)

from transformers import pipeline as hf_pipeline
import functools

LABELS_FR = ["relation amicale", "relation hostile", "relation neutre"]
LABEL_MAP  = {
    "relation amicale":  "friendly",
    "relation hostile":  "hostile",
    "relation neutre":   "neutral",
}

@functools.lru_cache(maxsize=1)
def _get_classifier():
    """Lazy singleton — loaded once, reused across all calls."""
    return hf_pipeline(
        "zero-shot-classification",
        model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device=-1,          # CPU
        multi_label=False,
    )

def classify_relationship(
    context_snippets: List[str],
    charA: str,
    charB: str,
) -> str:
    """
    Classifies the relationship type between charA and charB
    given a list of co-occurrence context snippets.
    Returns: "friendly" | "hostile" | "neutral"
    """
    if not context_snippets:
        return "neutral"

    clf = _get_classifier()

    # Prepend character names to help the model focus on their interaction
    enriched = [
        f"[{charA}] et [{charB}] : {snippet[:400]}"   # truncate long snippets
        for snippet in context_snippets
    ]

    per_window_votes: List[Tuple[str, float]] = []

    try:
        results = clf(enriched, LABELS_FR, batch_size=4)
        if not isinstance(results, list):
            results = [results]

        for result in results:
            top_label  = result["labels"][0]
            top_score  = result["scores"][0]
            per_window_votes.append((top_label, top_score))
    except Exception as e:
        print(f"[classify_relationship] Error: {e}")
        return "neutral"

    return _aggregate_votes(per_window_votes)


def _aggregate_votes(votes: List[Tuple[str, float]]) -> str:
    """Confidence-weighted majority vote."""
    from collections import defaultdict
    scores: Dict[str, float] = defaultdict(float)
    for label, confidence in votes:
        scores[label] += confidence
    winner = max(scores, key=scores.get)
    return LABEL_MAP.get(winner, "neutral")
```

---

## 3. Aggregation

The aggregation is already embedded in `_aggregate_votes` above — it sums confidence scores per label across all windows and picks the label with the highest total. This naturally handles ties (extremely rare in practice) by preferring whichever label had slightly higher summed confidence.

```
votes = [("relation amicale", 0.81), ("relation amicale", 0.73), ("relation hostile", 0.61)]
scores → {"relation amicale": 1.54, "relation hostile": 0.61}
winner → "relation amicale" → "friendly"
```

---

## 4. Module Integration

**New file**: `nlp_relation.py` — contains `extract_cooccurrence_contexts`, `classify_relationship`, `_aggregate_votes`, `_get_classifier`, and a top-level `label_relationships()` orchestrator:

```python
# nlp_relation.py — top-level orchestrator

from collections import Counter
from typing import Dict

def label_relationships(
    text: str,
    cooccurrences: Counter,              # {(charA, charB): count}
    alias_map: Dict[str, str],
    distance_max: int = 100,
    cache: Dict = None,                   # pass existing cache to skip re-classification
) -> Dict[tuple, str]:
    """
    Returns {(charA, charB): edge_type_string} for every pair in cooccurrences.
    """
    edge_labels = {}

    for (charA, charB) in cooccurrences:
        pair_key = tuple(sorted([charA, charB]))

        # Cache hit
        if cache is not None and pair_key in cache:
            edge_labels[(charA, charB)] = cache[pair_key]
            continue

        snippets = extract_cooccurrence_contexts(
            text, charA, charB, alias_map, distance_max
        )
        label = classify_relationship(snippets, charA, charB)
        edge_labels[(charA, charB)] = label

        if cache is not None:
            cache[pair_key] = label

    return edge_labels
```

**Change to `nlp_graph.py :: generate_graph()`**:

```python
def generate_graph(
    cooccurrences,
    character_counts,
    alias_map=None,
    edge_labels=None,          # NEW: dict{(charA,charB): str} | None
) -> nx.Graph:
    G = nx.Graph()
    # ... existing node/edge creation code ...

    for (charA, charB), weight in cooccurrences.items():
        G.add_edge(charA, charB, weight=weight)
        if edge_labels:
            pair = (charA, charB)
            alt  = (charB, charA)
            etype = edge_labels.get(pair) or edge_labels.get(alt, "neutral")
            G[charA][charB]["edge_type"] = etype

    return G
```

**Change to `nlp_create_submission.py :: process_chapter()`**:

```python
# Add to imports
from nlp_relation import label_relationships

def process_chapter(chapter_file, anti_dict, distance_max, chapter_id,
                    relation_cache=None):     # NEW param
    text      = read_file(chapter_file)
    # ... existing NER / alias / cooccurrence logic ...

    cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)

    # NEW: label relationships
    edge_labels = label_relationships(
        text, cooccurrences, alias_map,
        distance_max=distance_max,
        cache=relation_cache,
    )

    G = generate_graph(
        cooccurrences, LP_merged,
        alias_map=alias_map,
        edge_labels=edge_labels,    # NEW
    )
    # ... rest unchanged ...
```

**Notebook (Section 4)**: Add two cells — one to load/initialize the relation cache, one to pass it into the submission generator:

```python
# Cell: load relation cache
import pickle, os
RELATION_CACHE_FILE = "relation_cache.pkl"
relation_cache = {}
if os.path.exists(RELATION_CACHE_FILE):
    with open(RELATION_CACHE_FILE, "rb") as f:
        relation_cache = pickle.load(f)
print(f"Loaded {len(relation_cache)} cached relation labels.")
```

```python
# Cell: run submission (Section 4 — modified)
# ... run process_chapter for each chapter, passing relation_cache ...

# After loop: save updated cache
with open(RELATION_CACHE_FILE, "wb") as f:
    pickle.dump(relation_cache, f)
print("Relation cache saved.")
```

---

## 5. Caching / Performance

**Store labels per canonical pair, per chapter** using a two-level key:

```python
cache_key = (chapter_id, charA_canonical, charB_canonical)
# or equivalently:
cache_key = (chapter_id, *sorted([charA, charB]))
```

Why per-chapter? Because the same pair may have a different relationship in different chapters (e.g. they are neutral in ch. 1 and allied by ch. 10). Per-pair-global caching would be wrong.

Changing `distance_max` changes _which_ snippets are extracted but rarely reverses a relationship label (if Baley and Daneel are friendly in a 100-word window, they'll still be friendly in a 150-word window). So: cache at the pair+chapter level and only invalidate when the labeling model changes, not when `distance_max` changes. Document this assumption in a comment.

---

## 6. Validation (No Ground-Truth Labels)

**Spot-check procedure** — add this utility to `nlp_relation.py`:

```python
def print_validation_report(
    text: str,
    edge_labels: Dict[tuple, str],
    alias_map: Dict[str, str],
    distance_max: int,
    n: int = 5,
):
    """Print the n most 'hostile' and n most 'friendly' edges with their driving snippet."""
    hostile = [(p, l) for p, l in edge_labels.items() if l == "hostile"][:n]
    friendly = [(p, l) for p, l in edge_labels.items() if l == "friendly"][:n]

    for label_group in [hostile, friendly]:
        for (charA, charB), label in label_group:
            snippets = extract_cooccurrence_contexts(
                text, charA, charB, alias_map, distance_max, max_contexts=1
            )
            print(f"\n[{label.upper()}] {charA} ↔ {charB}")
            print(f"  Snippet: {snippets[0][:200] if snippets else '(none)'}…")
```

Run this for each chapter after the first full pass. Manually read ~20 pairs and check if the label matches your intuition. If "hostile" fires on scenes where characters are simply having a tense conversation but are allies, tighten your confidence threshold (e.g. only label "hostile" if the top NLI score ≥ 0.75, otherwise fall back to "neutral").

---

# Part 3 — Taxonomy Expansion Discussion

## 1. Richer Taxonomies in Literary Research

The NLP/DH literature on character networks uses several taxonomies:

- **BookNLP** (Bamman et al.) uses: agent, patient, possession, and predicative relations — structural roles, not social relations.
- **Social network analysis of fiction** often uses: ally, enemy, neutral, romantic, familial, hierarchical/authority.
- **PropBank / FrameNet** frames encode things like: Communication, Judgment_direct_address, Assistance, Attack — more granular than social types but hard to map cleanly.
- **SemEval-2010 Task 8** defines 9 directed relation types (Cause-Effect, Component-Whole, etc.) — too abstract for character-social use.

The most practical taxonomy for your use case, informed by the Asimov novels specifically, would be:

```
ally         — cooperating toward a shared goal (e.g. Baley + Daneel)
mentor/mentee — asymmetric knowledge transfer (e.g. Hummin guiding Seldon)
authority    — power relationship, command/obedience
romantic     — affective/intimate relationship
rival        — competing but not actively hostile
hostile      — active conflict or opposition
neutral      — minimal meaningful relationship in this chapter
```

## 2. Signals Needed for Fine-Grained Labels

| Distinction           | Signal needed                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------------- |
| mentor vs. ally       | Asymmetric verbs: "expliquer à", "enseigner", "guider", "apprendre à" + the learner as object                  |
| romantic vs. friendly | Physical proximity cues, terms of endearment, verbs like "embrasser", "aimer", "désirer"                       |
| rival vs. hostile     | Hostile = physical conflict verbs; rival = competition/comparison without violence, e.g. "défier", "surpasser" |
| authority vs. ally    | Command verbs: "ordonner à", "exiger de", titles like "commissaire", "chef" in apposition                      |

Most of these require either dependency parsing or a model with world knowledge about the characters (which an LLM has for Asimov, since it's in training data).

## 3. Practical Limit for Zero-Shot / Few-Shot in French Literary Text

The reliable limit for zero-shot NLI on French literary text is roughly **3–4 classes**. Beyond that, label overlap confuses the model:

- 3-class (friendly/hostile/neutral): ✅ reliable with mDeBERTa
- 5-class (ally/hostile/romantic/neutral/authority): ⚠️ workable with careful French hypotheses and a strong model (Mistral-7B)
- 7-class (the full taxonomy above): ❌ without labeled data or few-shot examples, precision drops below usefulness (~40–50% accuracy estimated on literary French)

The practical recommendation is to implement 3-class first, then optionally expand to 5-class using a one-time LLM API call (Mistral/OpenAI, `temperature=0`, cached to disk). Do not go beyond 5-class without at least 50 manually-labeled examples per class.

## 4. Multiple Labels per Edge

It is technically meaningful — Hummin is simultaneously a **mentor** and **ally** to Seldon. However:

- GraphML edge attributes are typed scalars. Multi-label requires either a semicolon-encoded string (`"ally;mentor"`) or separate boolean attributes (`is_ally`, `is_mentor`, `is_hostile`…).
- Kaggle evaluation would need to define how multi-label edges are scored.
- Multi-label zero-shot NLI is possible (set `multi_label=True` in the HuggingFace pipeline and apply a per-class threshold, e.g. 0.5) but requires careful threshold tuning.

**Recommendation**: Keep `edge_type` as a single best-label string for semester 2. If you expand later, use a secondary attribute `edge_type_secondary` rather than modifying the primary one — this keeps backward compatibility with the existing Kaggle schema.

---

## Summary Table

| Approach                 | French support | No labels needed | CPU feasible | Complexity | Quality    |
| ------------------------ | -------------- | ---------------- | ------------ | ---------- | ---------- |
| Zero-shot NLI (mDeBERTa) | ✅             | ✅               | ✅           | Low        | Good       |
| Sentiment (CamemBERT)    | ✅             | ✅               | ✅           | Very low   | Moderate   |
| LLM API (cached)         | ✅             | ✅               | ✅ (cached)  | Medium     | Excellent  |
| Local GGUF LLM           | ✅             | ✅               | ⚠️ slow      | Medium     | Very good  |
| Dependency rules         | ✅             | ✅               | ✅           | High       | Low recall |
| Fine-tuned transformer   | ✅             | ❌               | ✅           | Very high  | N/A        |

**Final recommendation**: Start with the `mDeBERTa` zero-shot NLI approach backed by a JSON/pickle pair-level cache keyed on `(chapter_id, charA, charB)`. If manual spot-checking reveals poor quality on your specific chapter set, upgrade by running one batch of Mistral API calls (`temperature=0`) and saving the results permanently. Never re-call the API for a pair that's already in the cache.

import re
import functools
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax

import numpy as np

# Load once (like your NLI model)
_tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-xlm-roberta-base-sentiment")
_model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-xlm-roberta-base-sentiment")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Much faster than zero-shot NLI
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Short semantic prototypes for each relationship type.
# These are used as label anchors in embedding space.
LABEL_PROMPTS = {
    "friendly": [
        "Two characters are friends.",
        "They trust and support each other.",
        "They are kind to one another.",
    ],
    "hostile": [
        "Two characters are enemies.",
        "They hate or oppose each other.",
        "They are in conflict or hostile.",
    ],
    "neutral": [
        "Two characters have no clear relationship.",
        "They simply appear together without strong feelings.",
        "Their interaction is ordinary or ambiguous.",
    ],
}

CONFIDENCE_THRESHOLD = 0.45
MAX_CONTEXTS_PER_PAIR = 5
MAX_SNIPPET_CHARS = 400


# ---------------------------------------------------------------------------
# Embedding model loading
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _get_embedder():
    """
    Load the sentence embedding model once and reuse it.
    """
    from sentence_transformers import SentenceTransformer
    print(f"[nlp_relation] Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("[nlp_relation] Embedding model ready.")
    return model


@functools.lru_cache(maxsize=1)
def _get_label_embeddings() -> Tuple[np.ndarray, List[str]]:
    """
    Precompute embeddings for the relationship labels.
    Returns:
        (label_matrix, label_names)
    """
    model = _get_embedder()

    label_names = ["friendly", "hostile", "neutral"]
    prompts = []
    prompt_owner = []

    for label in label_names:
        for prompt in LABEL_PROMPTS[label]:
            prompts.append(prompt)
            prompt_owner.append(label)

    emb = model.encode(prompts, convert_to_numpy=True, normalize_embeddings=True)

    # Average prompt embeddings per label
    label_vectors = []
    for label in label_names:
        idxs = [i for i, owner in enumerate(prompt_owner) if owner == label]
        vec = emb[idxs].mean(axis=0)
        vec = vec / (np.linalg.norm(vec) + 1e-12)
        label_vectors.append(vec)

    label_matrix = np.vstack(label_vectors)  # shape: (3, dim)
    return label_matrix, label_names


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
    aliases_A = {sf for sf, canon in alias_map.items() if canon == charA} | {charA}
    aliases_B = {sf for sf, canon in alias_map.items() if canon == charB} | {charB}

    token_matches = list(re.finditer(r"\S+", text))
    token_texts_lower = [m.group().lower() for m in token_matches]
    n = len(token_matches)

    def find_positions(aliases: set) -> List[int]:
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
                win_end = max(a, b) + 1
                window_key = (win_start, win_end)
                if window_key in used_windows:
                    continue
                used_windows.add(window_key)

                char_start = token_matches[win_start].start()
                char_end = token_matches[min(win_end, n - 1)].end()
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
    Confidence-weighted majority vote over per-snippet similarity results.
    """
    if not votes:
        return "neutral"

    scores: Dict[str, float] = defaultdict(float)
    for label, confidence in votes:
        scores[label] += confidence

    winner = max(scores, key=scores.get)
    winner_score = scores[winner] / len(votes)

    if winner_score < CONFIDENCE_THRESHOLD:
        return "neutral"

    return winner


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_relationship(context_snippets: list, charA: str, charB: str) -> str:
    """
    Fast sentiment-based relationship classifier.
    Returns "friendly", "hostile", or "neutral".
    """
    if not context_snippets:
        return "neutral"

    votes = []

    for snippet in context_snippets:
        text = f"{charA} et {charB}: {snippet[:400]}"
        tokens = _tokenizer(text, return_tensors="pt", truncation=True)
        output = _model(**tokens)
        scores = softmax(output.logits.detach().numpy()[0])
        # Map sentiment to relation
        sentiment_score = scores[2] - scores[0]  # positive - negative
        if sentiment_score > 0.1:
            votes.append(("friendly", abs(sentiment_score)))
        elif sentiment_score < -0.1:
            votes.append(("hostile", abs(sentiment_score)))
        else:
            votes.append(("neutral", abs(sentiment_score)))

    # Aggregate votes like in original nlp_relation
    if not votes:
        return "neutral"
    # Weighted majority vote
    totals = {"friendly": 0, "hostile": 0, "neutral": 0}
    for label, weight in votes:
        totals[label] += weight
    winner = max(totals, key=totals.get)
    return winner


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
    edge_labels: Dict[tuple, str] = {}
    new_pairs = 0

    for (charA, charB) in cooccurrences:
        canon_pair = tuple(sorted([charA, charB]))
        cache_key = (chapter_id,) + canon_pair

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

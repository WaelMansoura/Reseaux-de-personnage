Character Relationship Labeling: Research and Implementation Plan
Part 1 — Research Report

We consider six approaches for classifying a French literary character pair’s relationship (“friendly” / “hostile” / “neutral”):

1. Zero-shot classification with multilingual NLI

How it works: We use an off-the-shelf Natural Language Inference model (trained on XNLI or similar) to perform zero-shot text classification. In practice, we present the snippet as a “premise” and candidate relationship statements (e.g. “Cette relation est amicale”, “est hostile”, “est neutre”) as “hypotheses.” The NLI model then scores entailment/contradiction for each hypothesis, effectively ranking the labels. HuggingFace’s pipeline("zero-shot-classification") automates this. For example, MoritzLaurer’s mDeBERTa-v3 (fine-tuned on XNLI) supports French and 100+ languages. Similarly, French-specific NLI models exist (e.g. DistilCamemBERT-NLI). We would feed each snippet and the label set {“friendly”, “hostile”, “neutral”} (or French equivalents) to the pipeline.

    Suitability: Good for no-label zero-shot classification and French text. These models can run on CPU (though inference is slower, it can be batched). They require no training data, giving a deterministic mapping (given fixed seeds or cached scores). Downside: performance on literary text is uncertain, and running a 300M+ parameter model on ~hundreds of snippets may be slow without GPU. We must batch calls and cache outputs to be efficient and reproducible.

    Tools/Models: HuggingFace Transformers (pipeline("zero-shot-classification")). Recommended models: MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7, cmarkea/distilcamembert-base-nli, or joeddav/xlm-roberta-large-xnli. These all support French.

    Failure modes: NLI models may misinterpret context or pick up spurious cues. For example, if the text contains negative words (“meurtre”, “haïr”), it may label “hostile” even if the relationship is friendly in context. Ambiguous or subtle interactions may be hard to classify. Also, these models assume the snippet indeed expresses a relationship assertion; neutral/shared context could get misclassified. They are also sensitive to label wording (e.g. “amicale” vs “amicaux”), so label choice matters.

2. Sentiment / Tone Analysis on the context window

How it works: We compute the sentiment of the snippet around the two characters and map polarity to relationship: positive sentiment ⇒ friendly, negative ⇒ hostile, near-zero ⇒ neutral. For example, use a French sentiment model (like DistilCamemBERT-Sentiment) or a lexicon (FEEL or LIWC). One could simply run pipeline("sentiment-analysis") on the snippet and interpret “POS” vs “NEG”.

    Suitability: Very simple and CPU-efficient. Works without labels. Some multilingual sentiment models (e.g. nlptown/bert-base-multilingual-uncased-sentiment) can run on CPU; there are French-specific ones like cmarkea/distilcamembert-base-sentiment. However, literary passages may not align sentiment and relationship polarity well.

    Tools/Models: HuggingFace Transformers with cmarkea/distilcamembert-base-sentiment or tblard/tf-allocine. Lexicon-based approaches (e.g. sentiment lexicon applied to in-between words) could also be tried if models are too heavy.

    Failure modes: Sentiment ≠ relationship. Two characters could speak harshly about a third party (negative sentiment) but still be friendly to each other. Conversely, a neutral description (no sentiment words) doesn’t imply a neutral relationship. Polite hostility (sarcasm) or complex dialogue can fool sentiment. In short, sentiment is a noisy proxy: it may label all negative-content windows as “hostile” even if the characters’ dynamic is more complex.

3. Prompted LLM classification (zero/few-shot)

How it works: We ask a large language model to read the snippet and answer: “Given the excerpt, are X and Y friendly, hostile, or neutral?” This can be done with an API (GPT-4, GPT-3.5, Mistral-7B) or a local model via llama.cpp (e.g. Llama 2 / Mistral-7B instruction-tuned). The prompt includes the snippet and possibly a few examples (few-shot). The model then generates the label. E.g.:

Prompt: "Texte: [snippet]\nQuestion: Quel est le type de relation entre Alice et Bob? Réponses possibles: amicale, hostile, neutre. Réponse:"

    Suitability: Potentially high accuracy with rich understanding, especially with GPT-4-level models. Many open LLMs (Mistral-7B, Llama-2/3) can handle French if prompted properly. However, CPU inference of a 7B+ model is slow, and results are non-deterministic unless using fixed seed or deterministic decoding. Running dozens of queries in a notebook (on Colab CPU) might be very slow or require quantization (4-bit). Cached responses are needed for reproducibility.

    Tools/Models: OpenAI API (GPT-3.5/4) – not offline but yields good quality (but not reproducible without caching). Local: Mistral 7B (via Hugging Face’s mistralAI/mistral-7b), Llama 2-7B (Meta’s HF checkpoint), or any French-tuned model (e.g. OpenLLM-France’s Claire-Mistral-7B). These require transformers+torch (with 4/8-bit quantization) or llama.cpp.

    Failure modes: LLMs may hallucinate or give inconsistent labels if the prompt is ambiguous. They may also be overly verbose or add justification. Without careful prompt engineering, answers could vary. There’s also a risk of leaking context or bias – e.g. expecting “Bob” to be male affects “mentor” vs “authority”. Reliability without fine-tuning or supervision is uncertain, though scoring can be gleaned via log probabilities. Determinism is an issue – outputs must be cached.

4. Dependency-based heuristic rules

How it works: Parse each snippet with a French parser (spaCy or Stanza) to get grammatical relations. Then apply hand-crafted patterns: e.g. if X is subject and Y object of verb “aimer” (“X loves Y”), label friendly. If verb like “battre, haïr, tuer” connects them, label hostile. Adjectives or nouns directly modifying a character (e.g. “gardien”), or appositions (“Alice, son amie d’enfance”), can signal relations. We could also count positive/negative adjectives on each name. Essentially, we build lexicons of verbs/adjectives for friendly vs hostile and check if characters fill positive vs negative semantic roles.

    Suitability: Very interpretable and deterministic, requires only small libraries (spaCy French already in use). Runs fast on CPU. However, designing robust rules is laborious and brittle. The small Asimov corpus might lack clear verb patterns. Heuristics will cover only obvious cases (greetings, insults, explicit actions) and miss subtler cues. It also cannot easily detect neutral stance if nothing matches. It’s low-cost and deterministic, which is good for reproducibility.

    Tools/Models: spaCy’s fr_core_news_lg (already in our stack) or Stanza’s French model for dependency parsing. Optionally, FrameNet or semantic role tools (but likely overkill). Simple keyword lists can be built for French verbs of aggression vs affection.

    Failure modes: Extremely incomplete coverage. Many relationships are not explicitly verbalized (e.g. characters are friends implied by context, not direct dialogue). Also French syntax is flexible; subject-object patterns can be scrambled. Negation and idioms complicate rule matching. Risk of gross mislabeling if a pattern is too general (e.g. any occurrence of “respecter” might indicate positive but could be neutral context).

5. Fine-tuned transformer

How it works: We would fine-tune a pre-trained French (CamemBERT) or multilingual model (XLM-R) on labeled examples of snippet→relationship. This could be done with a few-shot approach (PEFT/LoRA) if we had even a small annotated set. In theory, unsupervised techniques (like this paper’s dynamic latent model) could also cluster relationship types beyond sentiment.

    Suitability: Not feasible without labeled data. We have zero ground truth for Asimov characters. Crafting even 50-100 labeled windows by hand is time-consuming. Without GPU, fine-tuning is slow and risky. Few-shot or transfer learning is unlikely to work well on 3-way classification with no clear training set. It also conflicts with “must be reproducible” since randomness in training can change results.

    Tools/Models: If attempted, one might use AutoModelForSequenceClassification (CamemBERT or XLM-R) and Hugging Face Trainer. For low-resource fine-tuning, adapters or LoRA (via 🤗PEFT) could reduce train time. Still, labeling data is the main blocker.

    Failure modes: Overfitting on tiny hand-labeled set; inability to generalize. Also unbalanced classes (we might have many neutral contexts and few hostile examples). If no labels, this approach is moot.

6. Aggregation strategy (window → edge-level)

How it works: Each character pair often co-occurs in multiple overlapping windows. We need to combine those snippet-level labels into one final edge_type. Simple options: majority vote of labels; choose label with highest confidence aggregate; or weighted vote (e.g. weight recent mentions more). Another idea: if any snippet is strongly hostile, label the edge hostile (to catch conflict even if most context is neutral). Or average an underlying sentiment score across snippets.

    Suitability: This is not so much a standalone approach as a needed step for any snippet-based method. It’s straightforward to implement (few CPU cost). We must be careful: if we always take “first occurrence” or “most frequent label,” we risk biases (e.g. early chapters might set tone). Simple majority vote is reproducible and easy. More complex schemes (score thresholds) could be explored but might overfit.

    Tools/Models: No special models needed, just Python logic (e.g. collections.Counter or NumPy). Possibly use snippet confidence scores from classifiers (NLI or sentiment) to break ties.

    Failure modes: If snippets give mixed signals, majority vote might flatten nuance (a relationship that is mostly friendly but briefly hostile would be labeled “friendly”). Also, if a pair only co-occurs once, aggregation does nothing. Weighted schemes introduce hyperparameters.

Recommendation: Given our constraints (French text, no labels, small data, CPU-only), the strongest yet practical approach is Zero-shot NLI (Approach 1), possibly supplemented by simple heuristics (Approach 4) to catch obvious cases. Multilingual NLI models (MoritzLaurer, DistilCamemBERT-NLI) provide a ready way to classify each snippet by embedding-based reasoning. They require no training data and have good French support. We should pair this with a clear aggregation rule (majority vote). If time allows, a basic sentiment check (Approach 2) could serve as a secondary signal (e.g. to break ties), and we can write a few dependency-based rules for glaring patterns (like X aime Y). Prompted LLMs are promising but impractical on CPU and costly to iterate. Fine-tuning is ruled out without data. Thus: Use a zero-shot transformer (multilingual NLI or French NLI) as the core, ensuring caching of results. This balances performance (entailment models have shown strong zero-shot capabilities) and feasibility. We will implement this first.
Part 2 — Implementation Plan

Based on the above, we recommend building new functions around a zero-shot NLI classifier. Here is a step-by-step plan:

1. Context Extraction

For each co-occurrence pair, extract the text snippets containing both names. For example, take the minimal token span around each co-occurrence (up to distance_max tokens). Pseudocode:

```python
def extract_cooccurrence_contexts(text, charA, charB, alias_map, distance_max):
    # Tokenize the text (e.g. simple whitespace or spaCy tokens).
    tokens = text.split()
    # Identify all positions where each character (or its alias) occurs.
    positions_A = [i for i, tok in enumerate(tokens) if alias_map.get(tok.lower(), tok) == charA]
    positions_B = [i for i, tok in enumerate(tokens) if alias_map.get(tok.lower(), tok) == charB]
    contexts = []
    for posA in positions_A:
        for posB in positions_B:
            if abs(posA - posB) <= distance_max:
                # Define snippet boundaries (e.g. include 20 tokens around the pair).
                start = max(0, min(posA, posB) - 20)
                end = min(len(tokens), max(posA, posB) + 20)
                snippet = " ".join(tokens[start:end])
                contexts.append(snippet)
    # Deduplicate identical snippets
    return list(set(contexts))
```

This returns a list of snippet strings for all windows where A and B appear within distance_max. We might shorten very long snippets or join multiple occurrences, but the above covers the basic logic.

2. Labeling Function

Load a zero-shot classifier once (lazy singleton) and apply it to each snippet, then aggregate. Pseudocode using HuggingFace pipeline:

```python
from transformers import pipeline

nlp_classifier = None
def get_nli_classifier():
    global nlp_classifier
    if nlp_classifier is None:
        # Load a French/multilingual NLI model
        nlp_classifier = pipeline(
            task='zero-shot-classification',
            model='MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7',
            device=-1  # CPU
        )
    return nlp_classifier

def classify_relationship(context_snippets: list[str], charA: str, charB: str) -> str:
    if not context_snippets:
        return "neutral"
    classifier = get_nli_classifier()
    candidate_labels = ["relation amicale", "relation hostile", "relation neutre"]
    snippet_labels = []
    for snippet in context_snippets:
        result = classifier(snippet, candidate_labels, multi_label=False)
        # result: {'labels': [...], 'scores': [...]} with labels ranked
        top_label = result['labels'][0]  # best hypothesis
        # Map French labels to English output labels
        if "amicale" in top_label:
            snippet_labels.append("friendly")
        elif "hostile" in top_label:
            snippet_labels.append("hostile")
        else:
            snippet_labels.append("neutral")
    # Aggregate snippet labels to one edge label
    final = aggregate_labels(snippet_labels)
    return final
```

Key points:

    We use the HuggingFace zero-shot-classification pipeline with a suitable model. (Alternatively, a French NLI model could be used.)

    We feed the snippet and French label phrases so the model works in the correct language.

    We then map the chosen label to our canonical English label.

    Error handling: if the pipeline call fails (e.g. OOM), catch and default to “neutral”.

3. Aggregation Strategy

A simple majority-vote aggregator (ties broken arbitrarily or by preferring hostile if any strong evidence). For example:

from collections import Counter

```python
from collections import Counter

def aggregate_labels(labels: list[str]) -> str:
    if not labels:
        return "neutral"
    counts = Counter(labels)
    # If 'hostile' appears at least once, we could bias toward it (optional)
    # For simplicity, use majority:
    return counts.most_common(1)[0][0]
```

This returns the most frequent label among snippets. In case of ties (e.g. ["friendly","hostile"]), it picks one arbitrarily (the one encountered first). We could refine by checking confidence scores or using a fixed priority (e.g. hostile > friendly > neutral if ambiguous). 4. Code Integration

    New Module: Create nlp_relation.py to hold the above functions (extract_cooccurrence_contexts, classify_relationship, aggregate_labels, plus any model-loading code). This keeps relationship logic separate.

    In nlp_cooccurrence.py or similar: After detecting cooccurrences, call a function label_relationships(text, cooccurrences, alias_map) which loops over each pair (charA, charB):

    ```python
    edge_labels = {}
    for (charA, charB), count in cooccurrences.items():
        contexts = extract_cooccurrence_contexts(text, charA, charB, alias_map, distance_max)
        label = classify_relationship(contexts, charA, charB)
        edge_labels[(charA, charB)] = label
    ```

    Modify nlp_graph.py::generate_graph(): Add a new parameter edge_labels (default None). When adding edges, if edge_labels[(u,v)] exists, set G[u][v]['edge_type'] = edge_labels[(u,v)]. For example:

    ```python
    def generate_graph(cooccurrences, LP_merged, alias_map, edge_labels=None):
    G = nx.Graph()
    # ... existing node logic ...
    for (charA, charB), weight in cooccurrences.items():
        G.add_edge(charA, charB, weight=weight)
        if edge_labels:
            label = edge_labels.get((charA,charB)) or edge_labels.get((charB,charA))
            if label:
                G[charA][charB]['edge_type'] = label
    return G
    ```

    Update calls in nlp_create_submission.py: originally G = generate_graph(cooccurrences, LP_merged, alias_map), change to include edge_labels.

    Notebook changes: In Section 4 of new.ipynb, before building the graph, insert the labeling step. For example:

    ```python
    cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
    edge_labels = label_relationships(text, cooccurrences, alias_map)
    G = generate_graph(cooccurrences, LP_merged, alias_map=alias_map, edge_labels=edge_labels)
    ```

    Ensure the edge_type attribute is written into GraphML. The Kaggle submission generator will automatically include it in the <graphml> output since generate_graph now added it.

5. Caching / Performance

To avoid re-running expensive inference:

    Cache per-snippet or per-pair: After computing labels for a chapter, save edge_labels (the dict of pair→label) to disk (e.g. JSON or pickle keyed by chapter ID). Next run, if the cache exists and distance_max hasn’t changed, we can reuse it.

    Granularity: Store at chapter level: e.g. { "paf0": {("Elijah Baley","Daneel Olivaw"): "friendly", ...}, ... }. Since we rely on full text and window size, if distance_max changes, some co-occurrences may change. We could key the cache by (chapter_id, distance_max), or simply invalidate the cache if the window param changes and recompute.

    Batching: When classifying snippets with pipeline, do them in batches if possible to speed up, but here we classify one by one. Alternatively, use classifier(snippets, candidate_labels) to batch multiple windows at once (though the HF pipeline supports list inputs).

    Reproducibility: Use deterministic pipeline parameters (use_auth_token fixed, no randomness) and save all outputs. Also, set any seeds if needed (though pipeline is usually deterministic for inference).

6. Manual Validation

Without ground truth, we do spot checks:

    For each chapter, print out (say) the top 5 edges labeled hostile with their most indicative snippet. The “most indicative” could be the snippet where the model was most confident (highest score) or the first occurrence. Manually reading these can catch obvious errors (e.g. if two friends were labeled hostile due to a misunderstood word).

    Compare with intuition: e.g. we know Hari Seldon and Dors Venabili are allies, so if labeled “hostile”, that’s a red flag.

    Create a small manual test list of snippets (10–20) with known relationships (friendship, antagonism, neutrality) and run the classifier. This helps calibrate threshold/tuning.

    Log counts of labels per chapter and inspect outliers (e.g. too many hostiles in a peaceable scene).

    In code, we might produce a debug output (on demand) that shows (charA, charB): label along with one snippet (or all snippets) that decided it, to eyeball reasonableness.

Part 3 — Taxonomy Expansion Discussion
Richer Relationship Taxonomies

Literature often defines many more relationship types than just friendly/hostile/neutral. In literary NLP, common categories include friend, lover/romantic partner, family (parent/child, siblings), mentor/mentee, rival, enemy, colleague, leader/subordinate, ally, protector/protected, member_of (group), etc. For example, an annotated fiction relations ontology lists labels like friend_of, lover_of, rival_of, enemy_of, mentor_of, teacher_of, protector_of, etc.. Another study notes that real relationships in narratives involve facets like family or romance, not just positive/negative sentiment. Standard ontologies (e.g. SEMNLP schemas) often mix familial ties (parent, spouse) and social roles (leader, member) alongside affective categories (friend, enemy). There is no single universal taxonomy, but these examples show how a graph’s edges could eventually carry more precise labels.
Signals for Finer Distinctions

Distinguishing mentor vs ally or romantic vs friendly requires deeper cues. For mentor/ally, look for words of guidance or hierarchy: verbs like “enseigner”, “conseiller”, “élève”, or explicit titles (“professeur”, “élève”, “conseiller”) often signal a mentor-mentee role. Allies/friends usually co-occur in cooperative actions or share goals without a power imbalance, and lack hierarchical terms. For romantic vs platonic, look for affectionate language: terms of endearment, affection verbs (“aimer”, “embrasser”), or context about marriage/love. Narration may mention a fiancé, époux, or describe physical closeness, jealousy, or longing. Words like “chérie”, “amour”, or descriptions of the characters looking at each other tenderly can hint romance. In contrast, friendly relationships lack such emotional intensity. French pronouns and adjectives may shift (“notre ami” vs “mon amour”). Semantic frames (love, marriage vs friendship, family) or sentiment intensifiers can help. Without explicit markers, however, these nuances are extremely hard to infer automatically.
Limits of Fine-Grained Taxonomies

Beyond a handful of broad classes, classification becomes unreliable without data. Each additional class (e.g. splitting “friendly” into ally, colleague, family, etc.) requires more specific cues. Zero-shot or few-shot models can handle maybe a handful of distinct labels, but as the number of classes grows (say >5–6), the entropy of label hypotheses makes predictions unstable. Literary text is especially tricky due to implied context. At some point (roughly beyond 5–7 categories), even a human without annotations would struggle to consistently differentiate subtle relations on a single snippet. Therefore, any fine-grained taxonomy in French likely needs either a larger annotated corpus or hierarchical classification (coarse first, then refine). In practice, starting with ~3–5 high-level types (as above) is safer. Excessive granularity (e.g. separate “ally” vs “companion” vs “colleague”) is likely too fine without training examples.
Multi-label Relationships

Characters can have multiple relationship facets (e.g. one might be both leader_of and ally of another). Supporting multi-label edges is possible but complicates output. If we allow multiple labels, the GraphML edge could store a list (e.g. "ally;leader"). However, GraphML typically expects atomic values; we could encode this as a semicolon-separated string or use multiple <data> fields (not standard). In practice, it may be simpler to choose the most defining label or adopt a hierarchy (e.g. always include "mentor_of" even if also "ally"). If multi-label is used, our pipeline must output all applicable labels. This might involve running separate classifiers or spotting multiple patterns. GraphML output would then have to store either an array or concatenated string. One pragmatic approach: allow one primary label (edge_type) and, if needed, introduce secondary attributes (e.g. edge_role="ally"; edge_role2="leader") or multiple edges (NetworkX MultiGraph) – but that breaks the submission format. Given the Kaggle format, it’s safer to stick to one label per edge for now, or encode multiple roles in one string. A future version could output something like "friendly (mentor)" or a combined category.

Sources: Prior work on fictional relationship extraction describes rich label sets (e.g. friend_of, lover_of, mentor_of, protector_of, etc.) and notes that real relationships have many facets (romance, family, etc.) beyond simple sentiment. Our plan will initially target the 3-class schema, with an eye toward expanding categories once we have a working system and possibly some manual labels to calibrate finer distinctions.

```

```

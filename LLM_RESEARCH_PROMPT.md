# LLM Research Prompt: Relationship Type Labeling for Character Networks

This file contains a ready-to-use prompt for advanced reasoning LLMs (o3, DeepSeek R1,
Gemini 2.5, Claude 3.7, etc.). Copy everything inside the fenced block below and paste it
directly into the model's chat interface.

Optional: also attach [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and
[TECHNICAL_PIPELINE.md](TECHNICAL_PIPELINE.md) as additional context files if the model
supports file uploads.

---

```
═══════════════════════════════════════════════════════════════════════════════
CONTEXT — PROJECT SUMMARY (read carefully before answering)
═══════════════════════════════════════════════════════════════════════════════

We are M1 students working on an NLP academic project / Kaggle competition.
In Semester 1 we built a character co-occurrence network extractor for two French
science-fiction novels by Isaac Asimov:
  • "Prélude à Fondation" (19 chapters, code: paf)
  • "Les Cavernes d'Acier" (18 chapters, code: lca)

THE COMPLETE PIPELINE (already implemented, written in Python):
  1. Multi-model NER ensemble (spaCy fr_core_news_lg + Stanza French + Flair fr-ner,
     majority vote) extracts character names from each chapter.
  2. False positives are filtered using an anti-dictionary of ~868 French stopwords.
  3. Surface-form aliases are grouped into canonical names using Union-Find +
     keyword-subset logic + fuzzy matching (rapidfuzz, threshold 88).
  4. A SLIDING WORD-DISTANCE WINDOW detects co-occurrences: for every window of
     `distance_max` consecutive tokens, if two character names both appear in the
     window, the pair's counter is incremented. Default window: 25–150 words.
  5. A NetworkX undirected graph is built: nodes = canonical characters (attrs:
     `count`, `names`="Canonical;Alias1;Alias2"), edges = co-occurring pairs
     (attr: `weight` = window overlap count).
  6. The graph is exported as a GraphML string and stored in a Kaggle submission CSV.

CURRENT EDGE ATTRIBUTES:
  weight (int) — number of windows where the two characters co-appeared

NEW EDGE ATTRIBUTE TO ADD (Semester 2 goal):
  edge_type (string) — the NATURE of the relationship between the two characters

DATA CONSTRAINTS:
  • All text is in French.
  • 37 chapters total — small corpus, no ground-truth relationship labels exist.
  • Must run on Google Colab free tier or a local CPU machine.
  • No large GPU models unless they support offline CPU inference.
  • Output must be deterministic or cached (same text → same label on re-run).
  • The `edge_type` value must be a plain string serializable as a GraphML attribute.

WHAT WE KNOW ABOUT THE CO-OCCURRENCE CONTEXT:
  For each detected co-occurrence, we know:
  (a) The two canonical character names (e.g. "Elijah Baley", "R. Daneel Olivaw").
  (b) The full chapter text (raw French prose, ~3,000–8,000 words per chapter).
  (c) All token positions where each character name (any alias) appears in the text.
  (d) The word-distance window that triggered the co-occurrence.
  We can therefore extract the actual text snippet(s) surrounding each co-occurrence
  instance (e.g. the 150-word window where both names appear).

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK — TWO-PART RESEARCH AND IMPLEMENTATION ASSIGNMENT
═══════════════════════════════════════════════════════════════════════════════

We need you to research how to add relationship-type labeling to this pipeline.
Please produce BOTH parts described below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 1 — RESEARCH REPORT: NLP Techniques for Relationship Classification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Survey and evaluate the following approaches for classifying the *nature* of a
named-character relationship given a short French text snippet around each
co-occurrence. For each approach:
  • Describe how it works in this context.
  • Rate its suitability given our constraints (French, no labels, small corpus,
    CPU-only, must be reproducible).
  • List the best available open-source libraries or models.
  • Note known failure modes or risks.

Approaches to cover:

1. ZERO-SHOT CLASSIFICATION WITH A MULTILINGUAL NLI MODEL
   (e.g. mDeBERTa, XNLI-trained models via HuggingFace `pipeline("zero-shot-classification")`)
   — Classify each text snippet against candidate labels like
     ["relation amicale", "relation hostile", "relation neutre"].

2. SENTIMENT / TONE ANALYSIS ON THE CONTEXT WINDOW
   (e.g. CamemBERT-sentiment, XLM-R-sentiment, or lexicon-based approaches)
   — Assign a sentiment score to the text window between/around the two character
     mentions, then map sentiment to relationship type.

3. PROMPTED LLM CLASSIFICATION (zero-shot or few-shot via API or local model)
   (e.g. Mistral-7B, Llama-3, or a quantized GGUF model via llama.cpp)
   — Use a structured prompt asking the model to classify the relationship in the
     given snippet. Consider both API calls (OpenAI/Mistral) and local inference.

4. DEPENDENCY-BASED HEURISTIC RULES
   — Use spaCy or Stanza dependency parses to identify syntactic patterns
     (e.g. subject-verb-object where both characters are arguments, or
     adjectives governing character mentions) and map these to relationship types.

5. FINE-TUNED TRANSFORMER (if a suitable pre-trained base exists)
   — Can any French or multilingual model be adapted with minimal examples
     (few-shot fine-tuning, PEFT/LoRA) to classify these snippets?
     What would we need, and is it feasible without labeled data?

6. AGGREGATION STRATEGY
   — Each character pair may have multiple co-occurrence windows in a chapter.
     How should per-window labels be aggregated into one edge-level `edge_type`?
     (e.g. majority vote, most-confident score, weighted by recency or count)

AT THE END OF PART 1, give a clear RECOMMENDATION: which single approach (or
combination) should we implement first, and why? Take into account that we are
students, so implementation complexity matters.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 2 — IMPLEMENTATION PLAN: Step-by-Step Integration into Our Codebase
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on your Part 1 recommendation, provide a CONCRETE, STEP-BY-STEP
implementation plan that integrates into our existing Python modules.

The plan must specify:

1. CONTEXT EXTRACTION
   How exactly do we extract the text snippet(s) for each co-occurrence pair?
   — Should we take the window of `distance_max` tokens around each co-occurrence?
   — Should we extract the full sentence(s) containing both character mentions?
   — How do we handle a pair that co-occurs many times (truncate, sample, concatenate)?
   Provide the exact algorithm or pseudocode for a function:
     `extract_cooccurrence_contexts(text, charA, charB, alias_map, distance_max)
      → list[str]`

2. LABELING FUNCTION
   Provide pseudocode (or actual Python code) for:
     `classify_relationship(context_snippets: list[str], charA: str, charB: str)
      → str`
   that returns one of: "friendly", "hostile", "neutral"
   (or a more detailed label — see Part 3).
   Include: model loading (lazy singleton), batching if beneficial, error handling.

3. AGGREGATION
   How to turn a list of per-window labels into one final `edge_type` string.
   Provide pseudocode for the aggregation step.

4. MODULE INTEGRATION
   Show exactly where the new code slots into the existing pipeline:
   — Which file should the new functions live in? (new `nlp_relation.py`?
     or extend `nlp_cooccurrence.py`?)
   — How does `nlp_graph.py :: generate_graph()` need to change to accept and
     write the `edge_type` attribute?
   — What changes are needed in `nlp_create_submission.py` and the notebook?

5. CACHING / PERFORMANCE
   — How do we cache relationship labels so re-running with different
     `distance_max` values does NOT re-classify everything?
   — Should labels be stored per co-occurrence window, per pair, or per chapter?

6. VALIDATION (no ground-truth labels)
   — How do we sanity-check that the labeling is reasonable without annotated data?
   — Suggest a simple manual spot-check procedure (e.g. print the 5 most
     confident "hostile" edges per chapter and the snippet that drove the label).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PART 3 — TAXONOMY EXPANSION DISCUSSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We want to eventually expand beyond the simple 3-class taxonomy
(friendly / hostile / neutral).

Please discuss:

1. What richer taxonomies are used in literary relationship extraction research?
   (e.g. ally, mentor/mentee, rival, romantic, authority/subordinate, neutral,
   unknown — are there standard ontologies?)

2. Which additional signals in the text would be needed to distinguish e.g.
   "mentor/mentee" from "ally", or "romantic" from "friendly"?

3. At what point does the taxonomy become too fine-grained to be reliably
   classified without labeled data? Where is the practical limit for zero-shot
   or few-shot approaches in French literary text?

4. Would it be worthwhile to assign MULTIPLE labels to one edge
   (e.g. a character can be both "authority" and "ally")?
   If so, how would that affect the GraphML edge attribute design?

═══════════════════════════════════════════════════════════════════════════════
FORMAT REQUIREMENTS FOR YOUR RESPONSE
═══════════════════════════════════════════════════════════════════════════════

• Use clear section headers (Part 1, Part 2, Part 3).
• In Part 2, include actual Python pseudocode or real code snippets where possible.
• Keep implementation suggestions compatible with: Python 3.10+, NetworkX, spaCy,
  HuggingFace Transformers, and running on CPU (Google Colab free tier).
• Be opinionated — we need a clear recommendation to act on, not just a list of options.
• Prioritize approaches that are well-maintained, well-documented, and have French
  language support.

Thank you.
```

---

## Notes on Using This Prompt

- **Which model to use**: This prompt is designed for a reasoning/research mode.
  Use o3, o1-pro, DeepSeek R1, Gemini 2.5 Pro, or Claude 3.7 (extended thinking).
  Standard chat models will give shallower answers.

- **Attaching files**: If the model supports file uploads, attach both
  [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and [TECHNICAL_PIPELINE.md](TECHNICAL_PIPELINE.md).
  The prompt is written to be self-contained if you can't attach files.

- **Follow-up questions to ask after the initial answer**:
  - _"Can you show me a complete, runnable `nlp_relation.py` module based on your recommendation?"_
  - _"What does the updated `generate_graph()` function look like with the `edge_type` parameter?"_
  - _"Write the complete updated Section 4 notebook cell that incorporates relationship labeling."_
  - _"What are 10 example French text snippets with their expected label (friendly/hostile/neutral)
    that I could use to manually validate the classifier?"_

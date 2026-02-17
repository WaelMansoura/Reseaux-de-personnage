# Enhancing NER for Literary Science-Fiction

## Pre-trained NER vs. Domain Adaptation

General French NER tools (spaCy’s news model, Stanza, etc.) struggle with unique sci-fi names. In practice, one can ensemble spaCy/Stanza **plus** a fiction-tuned model.

A very strong option is a **CamemBERT model fine-tuned on French novels**, for example:

- `compnet-renard/camembert-base-literary-NER-v2`  
  Trained specifically on literary texts, it performs much better on character and location names in novels.

Example usage with Hugging Face:

```python
from transformers import pipeline

ner = pipeline(
    "token-classification",
    model="compnet-renard/camembert-base-literary-NER-v2",
    aggregation_strategy="simple"
)

print(ner("Hari Seldon rencontre Dors Venabili sur Trantor."))
```

Another strong general-purpose option is **ModernCamemBERT**:

- `CATIE-AQ/Moderncamembert_3entities`
- Very high F1 on PER / LOC
- Works well out of the box

```python
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

model_name = "CATIE-AQ/Moderncamembert_3entities"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)

ner = pipeline(
    "token-classification",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple"
)
```

### Recommendation (low effort, high impact)

Add **one transformer-based literary NER model** as a third voter in your ensemble.
Instead of “spaCy AND Stanza must agree”, do **majority vote** or weighted vote.

This alone usually recovers:

- Fictional character names
- Invented planets
- Multi-token names like _Hari Seldon_

---

## Fine-tuning with Very Little Data

Even with limited time and data, **light fine-tuning helps**.

- Annotate ~50–100 sentences manually
- Include difficult cases:

  - Robot names (`R. Daneel Olivaw`)
  - Short mentions (`Seldon`, `Hari`)
  - Sci-fi locations (`Trantor`, `Terminus`)

- Fine-tune:

  - `fr_core_news_lg`
  - or a CamemBERT-based NER model

spaCy’s training pipeline makes this feasible in a few hours, and even small datasets produce noticeable gains in recall.

---

## Rule-Based & Gazetteer Improvements

### EntityRuler for Known Names

This is **one of the highest ROI improvements**.

```python
from spacy.pipeline import EntityRuler
import spacy

nlp = spacy.load("fr_core_news_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

patterns = [
    {"label": "PER", "pattern": [{"TEXT": "Hari"}, {"TEXT": "Seldon"}]},
    {"label": "PER", "pattern": [{"TEXT": "R."}, {"TEXT": "Daneel"}, {"TEXT": "Olivaw"}]},
    {"label": "LOC", "pattern": "Trantor"},
    {"label": "LOC", "pattern": "Terminus"},
    {"label": "LOC", "pattern": "Helicon"},
]

ruler.add_patterns(patterns)
```

You can generate these patterns automatically from:

- A Foundation wiki
- A character list extracted once manually

### Robot Naming Convention

Your intuition is correct: `"R."` is **not a title** in this universe.

Suggested rule:

- If `"R."` is followed by a capitalized token → treat as part of a PERSON name
- Do **not** strip `"R."` in `normalize_name` in that case

This avoids breaking robot names during alias merging.

---

## Alias Resolution Improvements

Your current keyword-based approach is a good baseline, but it can be improved with minimal changes.

### 1. Frequency-Based Canonical Selection

Instead of picking the _first_ name as canonical:

```python
canonical = max(group, key=lambda n: LP[n])
```

This ensures:

- `"Hari Seldon"` beats `"Hari"` or `"Seldon"`
- More stable canonical forms

---

### 2. Fuzzy String Matching (Very Low Effort)

Add a fuzzy similarity step to catch cases like:

- `Daneel` ↔ `R. Daneel Olivaw`
- Accent or punctuation variations

```python
from fuzzywuzzy import fuzz

if fuzz.partial_ratio(name1, name2) > 90:
    merge()
```

This complements your keyword logic very well.

---

### 3. Context / Embedding-Based Alias Clustering (Optional but Powerful)

Encode names (or short surrounding contexts) and cluster them.

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = {name: model.encode(name) for name in names}
```

Names that:

- Share tokens
- Have close embeddings
  are very likely aliases.

This works extremely well for fictional names with multiple surface forms.

---

## Co-occurrence Detection Improvements

Your sliding window works, but novels have richer structure.

### 1. Paragraph-Based Co-occurrence (Recommended)

Instead of word distance:

- Split by paragraphs
- Count all character pairs appearing in the same paragraph

```python
paragraphs = text.split("\n\n")

for para in paragraphs:
    present = [c for c in characters if c in para]
    for i in range(len(present)):
        for j in range(i + 1, len(present)):
            cooccurrences[(present[i], present[j])] += 1
```

This aligns better with narrative structure than token distance.

---

### 2. Sentence-Based Co-occurrence

Even simpler and often cleaner:

- Same sentence → co-occurrence

This reduces false positives where two names appear far apart but within 25 tokens.

---

### 3. Dialogue-Aware Co-occurrence (High Impact)

Most interactions happen in dialogue.

Ideas:

- Split text on quotes (« »)
- When a character speaks and another is mentioned in the same dialogue block, link them
- Look for patterns like:

  - `dit Seldon`
  - `répondit Gaal`

Even simple regex-based dialogue handling improves interaction graphs significantly.

---

### 4. Dependency-Based Interaction Weighting (Optional)

Use dependency parsing to boost strong interactions:

- `"Seldon aida Gaal"` → stronger edge
- Subject–verb–object relations imply real interaction

You can increment co-occurrence weight more for these cases.

---

## Coreference (If Time Allows)

French coreference is hard, but even **simple heuristics help**:

- Link:

  - `il`, `lui`, `elle`
  - to the most recent compatible character

- Especially useful inside dialogue

If possible, look into **BookNLP-fr**, which is designed for novels and includes:

- Character mentions
- Coreference chains

Even partial use (names only) can improve alias resolution.

---

## Quick Wins Summary (Best Effort / Impact Ratio)

1. Add **CamemBERT literary NER** to your ensemble
2. Add **EntityRuler + Gazetteer**
3. Improve alias canonical selection using frequency
4. Replace sliding window with **paragraph or sentence co-occurrence**
5. Handle `"R."` robot names explicitly

These can realistically be done in **1–3 days total**.

---

## If You Had More Time (Interesting Extensions)

- Train a **Foundation-specific NER**
- Add **coreference-aware co-occurrence**
- Label edges with interaction types (helped, opposed, talked to)
- Graph embeddings (Node2Vec) to analyze character communities
- Compare French vs English networks for translation effects

---

## Final Advice

For a Kaggle-style evaluation with limited time:

> **Recall beats elegance**

Catch every possible character mention first, then clean and merge aggressively.
Your current architecture is solid; the biggest gains will come from:

- Literary NER models
- Better alias resolution
- Narrative-aware co-occurrence

If you want, I can help you:

- Refactor your pipeline step-by-step
- Choose exact thresholds for alias merging
- Design a clean evaluation script per chapter

```

```

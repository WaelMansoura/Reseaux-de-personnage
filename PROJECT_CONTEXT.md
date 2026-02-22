# Project Context: Character Co-occurrence Networks in French Literary Text

## Overview

This is an M1 (master's year 1, semester 1) academic project / Kaggle competition built
by two students (Lotfi ABDALLAH — NER/entity pipeline; Wael MANSOURA — co-occurrence/graph).

**Goal (Semester 1 — completed)**: For each chapter of two French Asimov novels, automatically
extract named characters, resolve their aliases, detect which characters appear near each other
in the text, and output the resulting **character co-occurrence network** as a GraphML string
in a Kaggle submission CSV.

**Goal (Semester 2 — current)**: Extend each edge in the graph with a **relationship type
label** — at minimum distinguishing _friendly_, _hostile_, and _neutral_ interactions.
A richer taxonomy (ally, mentor, rival, romantic interest, neutral, etc.) should also be
explored.

---

## Data

### Books

Two Isaac Asimov novels translated into French:

| Book code | Title                                         | Chapters          |
| --------- | --------------------------------------------- | ----------------- |
| `paf`     | _Prélude à Fondation_ (Prelude to Foundation) | 19 (indices 0–18) |
| `lca`     | _Les Cavernes d'Acier_ (The Caves of Steel)   | 18 (indices 0–17) |

**Total**: 37 chapters.

### File Format

Each chapter is stored as a plain UTF-8 text file:

```
data/prelude_a_fondation/chapter_1.txt.preprocessed
data/prelude_a_fondation/chapter_2.txt.preprocessed
...
data/les_cavernes_d_acier/chapter_1.txt.preprocessed
...
```

The `.preprocessed` files are standard French prose — no markup, no annotations.
Chapter filenames are **1-indexed on disk** but **0-indexed in the submission IDs**
(e.g. `chapter_1.txt.preprocessed` → submission ID `paf0`).

### Sample Characters

- _Prélude à Fondation_: Hari Seldon, Cléon I (Emperor), Chetter Hummin, Dors Venabili,
  Demerzel, Joranum, Amaryl, Gaal Dornick …
- _Les Cavernes d'Acier_: Elijah Baley, R. Daneel Olivaw, Commissioner Enderby,
  Jessie Baley, Dr. Fastolfe …

---

## Semester 1 Pipeline (Completed)

```
Raw chapter text
      │
      ▼  Multi-model NER (spaCy + Stanza + Flair, majority vote)
Named entity spans [(surface_form, label), ...]
      │
      ▼  Filtering (PER only, anti-dictionary stopwords, validity rules)
Person counter  {name: mention_count}
      │
      ▼  Alias grouping (Union-Find + keyword overlap + fuzzy matching)
Alias clusters  → canonical name = most-frequent form
      │
      ▼  Alias map applied, counts merged
Merged person counter  {canonical_name: total_count}
      │
      ▼  Sliding-window co-occurrence detection (configurable word window)
Co-occurrence counter  {(charA, charB): window_overlap_count}
      │
      ▼  Graph construction (NetworkX undirected)
nx.Graph: nodes with (count, names) attrs; edges with weight attr
      │
      ▼  Isolated node removal → GraphML export
submission.csv row:  ID=pafN / lcaN,  graphml=<xml string>
```

---

## Submission Format

The Kaggle submission is a two-column CSV:

```
ID,graphml
paf0,"<?xml version='1.0' ...><graphml>...</graphml>"
paf1,...
lca0,...
lca17,...
```

- **ID**: `{book_code}{chapter_0_based_index}` — e.g. `paf0`, `lca17`
- **graphml**: a complete GraphML XML string produced by NetworkX

### GraphML Node Attributes

| Attribute | Type    | Meaning                                                                                |
| --------- | ------- | -------------------------------------------------------------------------------------- |
| `count`   | integer | Total mention count across the chapter (after alias merging)                           |
| `names`   | string  | Semicolon-separated list of all surface forms, e.g. `"Elijah Baley;Baley;Elijah;Lije"` |

The `names` attribute is **required** by the Kaggle evaluation — it is used to verify that
alias merging was done correctly.

### GraphML Edge Attributes (Semester 1)

| Attribute | Type    | Meaning                                                   |
| --------- | ------- | --------------------------------------------------------- |
| `weight`  | integer | Number of windows in which the two characters co-appeared |

### GraphML Edge Attributes (Semester 2 — to be added)

| Attribute   | Type    | Meaning                                                         |
| ----------- | ------- | --------------------------------------------------------------- |
| `weight`    | integer | (unchanged) Co-occurrence count                                 |
| `edge_type` | string  | Relationship label, e.g. `"friendly"`, `"hostile"`, `"neutral"` |

---

## Constraints for Semester 2

- **Language**: All text is in **French**. Any NLP model used for labeling must support French.
- **No labeled training data**: There is no annotated corpus of relationship types for these
  specific books. Any approach must work zero-shot, few-shot, or via unsupervised signals.
- **Small corpus**: Only 37 chapters; the co-occurrence graph per chapter is sparse
  (typically 5–20 nodes, 5–30 edges per chapter).
- **Existing stack**: Python 3, NetworkX, spaCy, Stanza, Flair, rapidfuzz. New libraries are
  allowed but must be justified.
- **Output must be GraphML-serializable**: The `edge_type` value must be a plain string
  (or a numeric code) storable as a GraphML edge attribute and embeddable in the submission CSV.
- **Reproducibility**: The labeling must be deterministic (same text → same label on re-run),
  or at minimum produce a cached/saved result.
- **Compute**: Runs on a Google Colab free tier or a local machine (no GPU guarantee).
  Approaches requiring large GPU models need a fallback or an offline-inference strategy.

---

## Anti-Dictionary

`antidict.txt` contains ~868 French functional words (prepositions, determiners, common pronouns,
verbal auxiliaries) used to filter NER false positives. Example entries: `quelqu`, `celui`,
`dont`, `vers`, `comme`, `après`, `entre`. These are stripped from the entity list before any
further processing.

---

## See Also

- [TECHNICAL_PIPELINE.md](TECHNICAL_PIPELINE.md) — module-by-module code reference
- [LLM_RESEARCH_PROMPT.md](LLM_RESEARCH_PROMPT.md) — ready-to-use research prompt for
  advanced reasoning LLMs

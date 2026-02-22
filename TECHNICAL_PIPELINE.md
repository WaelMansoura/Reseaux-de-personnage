# Technical Pipeline Reference

This document is a module-by-module reference for the character network extraction
codebase. See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for the domain/competition overview.

---

## Repository Structure

```
FinalProject/
├── nlp_utils.py              # I/O helpers
├── nlp_extract_characters.py # Single-model NER + filtering (baseline)
├── nlp_multi_ner.py          # Multi-model NER ensemble (production)
├── nlp_aliases.py            # Alias grouping (Union-Find + fuzzy)
├── nlp_cooccurrence.py       # Sliding-window co-occurrence detection
├── nlp_graph.py              # NetworkX graph construction + export
├── nlp_visualize_web.py      # PyVis interactive HTML export
├── nlp_main.py               # Dev/debug single-file pipeline
├── nlp_create_submission.py  # Production Kaggle submission generator
├── antidict.txt              # ~868 French functional-word stopwords
├── characters.txt            # Optional custom character name list
└── data/
    ├── prelude_a_fondation/  # 19 chapters (chapter_1 … chapter_19)
    └── les_cavernes_d_acier/ # 18 chapters (chapter_1 … chapter_18)
```

---

## End-to-End Pipeline

```
chapter_N.txt.preprocessed
        │
        ▼  nlp_multi_ner.py :: ensemble_entities(text, method="vote")
list[(surface_form, label)]     ← majority vote across spaCy + Stanza + Flair
        │
        ▼  nlp_extract_characters.py :: count_entities(entities)
Counter{(text, label): count}   ← L (all entities)
        │
        ▼  nlp_extract_characters.py :: filter_persons(L, anti_dict)
Counter{name: count}            ← LP (persons only, filtered)
        │
        ▼  nlp_aliases.py :: group_aliases(LP)
list[list[str]]                 ← alias clusters; group[0] = canonical name
        │
        ▼  nlp_aliases.py :: alias_dictionary(groups) + apply_manual_aliases(...)
dict{surface_form: canonical}   ← alias_map
        │
        ▼  nlp_aliases.py :: merge_alias_counts(LP, alias_map)
Counter{canonical_name: total}  ← LP_merged
        │
        ▼  nlp_cooccurrence.py :: detect_cooccurrences(text, LP_merged, distance_max)
Counter{(charA, charB): count}  ← co-occurrence pairs
        │
        ▼  nlp_graph.py :: generate_graph(cooccurrences, LP_merged, alias_map)
nx.Graph                        ← nodes: {count, names}; edges: {weight}
        │
        ▼  nlp_graph.py :: remove_isolated_nodes(G)
nx.Graph (pruned)
        │
        ▼  nx.generate_graphml(G) + html.unescape(...)
GraphML XML string
        │
        ▼  pandas DataFrame → submission.csv
ID,graphml
paf0,"..."
```

---

## Module Reference

---

### `nlp_utils.py`

Minimal I/O helpers, no external dependencies.

| Function         | Signature                          | Returns                | Notes                      |
| ---------------- | ---------------------------------- | ---------------------- | -------------------------- |
| `read_file`      | `(path: str) → str`                | Full file content      | UTF-8                      |
| `load_anti_dict` | `(path="antidict.txt") → set[str]` | Lowercase stopword set | Strips inline `#` comments |

---

### `nlp_extract_characters.py`

Single-model NER baseline (spaCy only). Used for prototyping; the production pipeline
uses `nlp_multi_ner.py` instead.

| Function           | Signature                            | Returns                         | Notes                                                             |
| ------------------ | ------------------------------------ | ------------------------------- | ----------------------------------------------------------------- |
| `get_spacy_model`  | `() → nlp`                           | spaCy pipeline                  | Lazy singleton, `fr_core_news_lg`                                 |
| `extract_entities` | `(text: str) → list[tuple[str,str]]` | `[(surface, label), …]`         | All spaCy NER spans                                               |
| `count_entities`   | `(entities) → Counter`               | `Counter{(text, label): count}` |                                                                   |
| `filter_persons`   | `(L, anti_dict=None) → Counter`      | `Counter{name: count}`          | Keeps `PER` labels passing `is_valid_entity` and not in anti_dict |
| `filter_locations` | `(L) → Counter`                      | `Counter{name: count}`          | Keeps `LOC` and `GPE` labels                                      |
| `is_valid_entity`  | `(text: str) → bool`                 | bool                            | Rejects: empty, single-char, ALL-CAPS, contains `-–?"`            |

**NER model**: `fr_core_news_lg` (spaCy French large, trained on news text).

---

### `nlp_multi_ner.py`

Production NER ensemble. Combines three models via majority vote.

#### Models

| Model             | Library | Notes                                                                                     |
| ----------------- | ------- | ----------------------------------------------------------------------------------------- |
| `fr_core_news_lg` | spaCy   | Augmented with an `EntityRuler` gazetteer loaded **before** the statistical NER component |
| French pipeline   | Stanza  | `tokenize,ner` processors; auto-downloads on first use                                    |
| `fr-ner`          | Flair   | BiLSTM-CRF, ~450 MB; optional — pipeline degrades gracefully if unavailable               |

#### Asimov Gazetteer

`nlp_multi_ner.py` contains hard-coded dictionaries `ASIMOV_CHARACTERS` and
`ASIMOV_LOCATIONS` covering canonical names and alias lists for both books and the
broader Foundation/Robot universe. These are injected into spaCy's `EntityRuler` with
priority over the statistical NER, ensuring key names are always recognized.

Example entry:

```python
"Elijah Baley": ["Baley", "Elijah", "Lije"]
"Hari Seldon":  ["Seldon", "Hari"]
```

#### Key Functions

| Function             | Signature                                             | Returns                                                            |
| -------------------- | ----------------------------------------------------- | ------------------------------------------------------------------ |
| `get_spacy_model`    | `() → nlp`                                            | spaCy pipeline + EntityRuler singleton                             |
| `get_stanza_model`   | `() → Pipeline`                                       | Stanza pipeline singleton                                          |
| `get_flair_model`    | `() → Classifier`                                     | Flair tagger singleton                                             |
| `setup_entity_ruler` | `(nlp, character_file, use_gazetteer)`                | Attaches EntityRuler to nlp in-place                               |
| `normalize_span`     | `(text: str) → str`                                   | Strips French quote marks (`«»""`)                                 |
| `extract_spacy`      | `(text: str) → list[tuple]`                           | `[(surface, label), …]`                                            |
| `extract_stanza`     | `(text: str) → list[tuple]`                           | `[(surface, label), …]`                                            |
| `_chunk_text`        | `(text, max_chars=900) → list[str]`                   | Splits on paragraph/sentence boundaries for Flair's sequence model |
| `extract_flair`      | `(text: str) → list[tuple]`                           | `[(surface, label), …]`                                            |
| `ensemble_entities`  | `(text, method="vote", use_flair=True) → list[tuple]` | **Main entry point**                                               |

#### Ensemble Logic

Each model votes at most once per unique entity surface form.
Vote tally: `counter[entity_text][label] += 1` per model.

| Mode                 | Behavior                                                                     |
| -------------------- | ---------------------------------------------------------------------------- |
| `"union"`            | Keep entities found by ≥ 1 model                                             |
| `"intersection"`     | Keep entities agreed on by all active models                                 |
| `"vote"` _(default)_ | Keep entities found by ≥ 2 models (majority, works for 2- or 3-model setups) |

If Flair is unavailable, falls back silently to spaCy + Stanza.

---

### `nlp_aliases.py`

Groups surface-form variants of the same character into one canonical name.

#### Key Functions

| Function               | Signature                                         | Returns                                                                                            |
| ---------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `normalize_name`       | `(name: str) → str`                               | Lowercase, stripped, civil titles removed, punctuation removed (except accented chars and hyphens) |
| `name_keywords`        | `(name: str) → set[str]`                          | Set of normalized word tokens                                                                      |
| `_should_merge`        | `(name1, name2) → bool`                           | Core merging predicate (see algorithm below)                                                       |
| `group_aliases`        | `(LP: Counter) → list[list[str]]`                 | List of alias clusters; `group[0]` = most-frequent (canonical)                                     |
| `alias_dictionary`     | `(groups) → dict`                                 | `{any_surface_form: canonical_name}`                                                               |
| `apply_manual_aliases` | `(alias_map, manual_overrides) → dict`            | Overlays hand-crafted aliases with transitive fix                                                  |
| `merge_alias_counts`   | `(LP, alias_map) → Counter`                       | Sums counts of all alias forms into canonical                                                      |
| `filter_by_frequency`  | `(character_counts, min_occurrences=2) → Counter` | Removes characters with fewer than N mentions                                                      |

#### Alias Grouping Algorithm

1. **Ambiguity guard (pre-pass)**: For each single-token name (e.g. `"Darell"`), find all
   multi-word names containing that token. If more than one multi-word name matches, the
   single token is pre-assigned exclusively to the **most-frequent** multi-word name.
   This prevents `"Darell"` from bridging `"Bayta Darell"` and `"Arcadia Darell"` into
   one group.

2. **Pair-wise merging via `_should_merge`**:
   - _Both multi-word_: merge only if one keyword-set is a **proper subset** of the other
     (pure abbreviation, e.g. `{seldon} ⊂ {hari, seldon}`).
   - _One single-word + one multi-word_: merge if the single token is a meaningful
     (length > 1) keyword of the multi-word name.
   - _Both single-word_: merge only if fuzzy ratio ≥ 88.
   - _No shared keywords + at least one multi-word_: fuzzy fallback at threshold 88.

3. **Union-Find (DSU)** ensures transitivity: if A→B and B→C, all three are in one group
   regardless of iteration order.

4. Within each group, sort descending by frequency → `group[0]` is the canonical name.

**Fuzzy backend**: `rapidfuzz` preferred; falls back to `difflib.SequenceMatcher`.

#### Manual Alias Overrides (in notebook)

```python
MANUAL_ALIASES = {
    "Empereur":   "Cléon",
    "l'Empereur": "Cléon",
    "L'Empereur": "Cléon",
    "Sire":       "Cléon",
    "Cléon Ier":  "Cléon",
}
```

---

### `nlp_cooccurrence.py`

Sliding word-distance window co-occurrence detection.

#### `detect_cooccurrences(text, character_counts, distance_max=25) → Counter`

**Input**:

- `text`: raw chapter string
- `character_counts`: `Counter{canonical_name: mention_count}` (LP_merged)
- `distance_max`: window size in word tokens (default 25; notebook uses 150)

**Output**: `Counter{(charA, charB): overlap_count}` — unordered pairs, counts summed
across all windows.

**Algorithm**:

1. Tokenize with `re.findall(r"\w+", text.lower())` → flat list of lowercase tokens.
   (Apostrophes/punctuation discarded; `d'acier` → `["d", "acier"]`.)
2. For each character name, find all token-index positions where the name's token sequence
   appears.
3. For every starting token index `i`, define a window `[i, i + distance_max)`.
   Collect all character names with at least one occurrence in the window.
4. Every unordered pair of characters in the same window increments the counter by 1.
5. Convert lowercase tokenized names back to original case via a `lowercase_to_original` map.

**Detection type**: word-distance window-based — **not** sentence-based or dependency-based.

---

### `nlp_graph.py`

Builds and exports the NetworkX character network.

#### Functions

| Function                | Signature                                                      | Notes                                                      |
| ----------------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| `generate_graph`        | `(cooccurrences, character_counts, alias_map=None) → nx.Graph` | Nodes get `count` + `names` attrs; edges get `weight` attr |
| `remove_isolated_nodes` | `(G) → nx.Graph`                                               | Removes degree-0 nodes in-place                            |
| `save_graphml`          | `(G, filename)`                                                | `nx.write_graphml(G, filename)`                            |
| `visualize_graph`       | `(G, title, top_n=30)`                                         | Matplotlib spring-layout, top-N by count                   |

#### Graph Schema

**Nodes**:

```
node_id  =  canonical_name  (string)
count    =  total mention count in chapter  (int)
names    =  "CanonName;Alias1;Alias2;…"     (string, semicolon-separated)
```

The `names` attribute is **required by Kaggle** — it encodes the alias merging result.

**Edges**:

```
(charA, charB)  →  undirected
weight          =  co-occurrence window overlap count  (int)
```

**Type**: `nx.Graph` (undirected, no self-loops).

#### Semester 2 Extension Point

The natural place to add relationship labeling is **between** `detect_cooccurrences` and
`generate_graph`. The enrichment would change the pipeline step from:

```python
cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
G = generate_graph(cooccurrences, LP_merged, alias_map=alias_map)
```

to something like:

```python
cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
edge_labels = label_relationships(text, cooccurrences, LP_merged)
G = generate_graph(cooccurrences, LP_merged, alias_map=alias_map, edge_labels=edge_labels)
```

where `edge_labels` is a `dict{(charA, charB): "friendly" | "hostile" | "neutral"}`,
and `generate_graph` writes these as the new `edge_type` GraphML attribute.

---

### `nlp_visualize_web.py`

Interactive HTML visualization using PyVis.

#### `create_interactive_graph(G, cooccurrences, output_file="graph.html")`

- Writes a self-contained HTML file using the bundled `vis.js` library (`lib/vis-9.1.2/`).
- Node size: `10 + count × 0.5`.
- Edge thickness (`value`): co-occurrence weight.
- Opens the file in the default browser after creation.

---

### `nlp_create_submission.py`

Production Kaggle submission generator.

| Function                                                                                            | Notes                                         |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `process_chapter(chapter_file, anti_dict, distance_max, chapter_id)`                                | Full per-chapter pipeline; returns `nx.Graph` |
| `generate_submission(books_config, anti_dict_file, output_csv, distance_max)`                       | Sequential processing of all chapters         |
| `generate_submission_parallel(books_config, anti_dict_file, output_csv, distance_max, n_processes)` | Parallel version via `multiprocessing.Pool`   |

#### `books_config` format

```python
[
    (chapter_numbers_list,  book_code_string,  folder_path_string),
    (list(range(19)),       "paf",             "data/prelude_a_fondation"),
    (list(range(18)),       "lca",             "data/les_cavernes_d_acier"),
]
```

Side effect: writes `{chapter_id}_L.txt`, `{chapter_id}_LP.txt`, `{chapter_id}_LL.txt`
debug files per chapter.

---

### `nlp_main.py`

Development/debug script. Runs the full pipeline on a single concatenated `output.txt`
file and writes intermediate lists (`L.txt`, `LP.txt`, `LL.txt`) to disk for inspection.
Not used in the submission workflow.

---

## Notebook (`new.ipynb`) — Optimized Workflow

The notebook implements a two-phase workflow to avoid re-running the slow NER step:

| Section                                | Speed           | Re-run when                                                  |
| -------------------------------------- | --------------- | ------------------------------------------------------------ |
| Section 3 — NER extraction             | Slow (~2–5 min) | NER/filtering logic changes                                  |
| Section 3.5 — Save/Load cache          | Instant         | After NER, before kernel restart                             |
| Section 4 — Co-occurrence + submission | Fast (~seconds) | Changing `distance_max`, `min_occurrences`, `MANUAL_ALIASES` |

### NER Cache Schema

```python
ner_cache = {
    "paf0": {
        "text": str,         # raw chapter text
        "L":   Counter,      # all entities {(text,label): count}
        "LP":  Counter,      # persons only {name: count}
        "LL":  Counter,      # locations {name: count}
    },
    "paf1": { … },
    …
    "lca17": { … },
}
```

Cache is serialized to `ner_cache.pkl` via `pickle` for persistence across sessions.

---

## Dependencies

| Package     | Version constraint               | Purpose                                  |
| ----------- | -------------------------------- | ---------------------------------------- |
| `spacy`     | `fr_core_news_lg` model required | Primary NER                              |
| `stanza`    | French model auto-downloads      | Secondary NER                            |
| `flair`     | `fr-ner` model auto-downloads    | Tertiary NER (optional)                  |
| `networkx`  | any                              | Graph construction + GraphML export      |
| `rapidfuzz` | any (fallback: `difflib`)        | Fuzzy string matching for alias grouping |
| `pyvis`     | any                              | Interactive HTML visualization           |
| `pandas`    | any                              | Submission CSV generation                |

---

## See Also

- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) — domain/competition overview and semester-2 goals
- [LLM_RESEARCH_PROMPT.md](LLM_RESEARCH_PROMPT.md) — research prompt for relationship labeling

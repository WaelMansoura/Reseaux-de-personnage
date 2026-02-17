# Character Network Extraction from Asimov's Works

## Project Overview

This is an NLP (Natural Language Processing) project focused on automatically extracting character networks from French translations of Isaac Asimov's science fiction novels. The system identifies characters, detects their interactions through co-occurrence analysis, and generates network graphs representing character relationships.

**Academic Context**: Master's Level 1 (M1), Semester 1 - AMS (Applied Mathematics & Statistics) Project

---

## 📚 Analyzed Books

The project processes two Isaac Asimov novels translated into French:

1. **Prélude à Fondation** (Prelude to Foundation) - 19 chapters
   - Files: `paf0` through `paf18`
2. **Les Cavernes d'Acier** (The Caves of Steel) - 18 chapters
   - Files: `lca0` through `lca17`

**Total**: 37 chapters analyzed

---

## 🎯 Project Objectives

1. **Entity Extraction**: Automatically identify named entities (characters, locations) from narrative text
2. **Character Recognition**: Filter and classify person entities (LP list)
3. **Alias Resolution**: Group different mentions of the same character (e.g., "Hari Seldon", "Seldon", "Hari")
4. **Co-occurrence Detection**: Find character interactions based on proximity in text
5. **Network Generation**: Build NetworkX graphs representing character relationships
6. **Submission Generation**: Create GraphML format output for Kaggle competition

---

## 🏗️ Project Architecture

### Core Modules

#### 1. **nlp_extract_characters.py**

Handles Named Entity Recognition (NER) using spaCy:

- `extract_entities()`: Extracts all named entities from text
- `count_entities()`: Counts entity occurrences
- `filter_persons()`: Filters person entities (LP list)
- `filter_locations()`: Filters location entities (LL list)
- `is_valid_entity()`: Validates entities (rejects ALL CAPS, single characters, hyphens)

**Model**: `fr_core_news_lg` (spaCy French large model)

#### 2. **nlp_multi_ner.py**

Ensemble NER approach using multiple models for improved accuracy:

- **Models Used**:
  - spaCy (`fr_core_news_lg`)
  - Stanza (French NER pipeline)
  - EntityRuler with Asimov-specific gazetteer
- **Ensemble Methods**:
  - `union`: Keep all entities from both models
  - `intersection`: Only entities found by both models
  - `vote`: Keep entities where models agree (default)

- **Asimov Gazetteer**: Built-in dictionary of 40+ character names and 10+ locations with aliases for better recognition of sci-fi proper nouns

**Key Innovation**: Uses custom EntityRuler patterns to recognize Asimov-specific characters that standard NER models might miss.

#### 3. **nlp_aliases.py**

Handles character alias resolution:

- `normalize_name()`: Normalizes names (lowercase, remove titles, punctuation)
- `name_keywords()`: Extracts keywords from names
- `group_aliases()`: Groups variants of the same character using keyword overlap
- `alias_dictionary()`: Maps aliases to canonical names
- `merge_alias_counts()`: Merges counts for aliased names

**Example**: Groups `["Hari Seldon", "Seldon", "Hari"]` → canonical: `"Hari Seldon"`

#### 4. **nlp_cooccurrence.py**

Detects character co-occurrences using sliding window approach:

- `detect_cooccurrences()`: Finds character pairs within distance threshold
- **Window Size**: Configurable (default: 25-100 words)
- **Algorithm**:
  1. Tokenize text using regex `\w+`
  2. Find positions of all character mentions
  3. Slide window across text
  4. Count pairs appearing in same window

**Critical Feature**: Handles multi-word character names and apostrophes correctly

#### 5. **nlp_graph.py**

NetworkX graph generation and visualization:

- `generate_graph()`: Creates graph from co-occurrences
- `save_graphml()`: Exports to GraphML format
- `visualize_graph()`: Creates matplotlib visualization

**Graph Properties**:

- **Nodes**: Characters with `count` (mentions) and `names` (aliases) attributes
- **Edges**: Co-occurrences with `weight` attribute

#### 6. **nlp_create_submission.py**

Main pipeline orchestrator:

- `process_chapter()`: Complete pipeline for one chapter
- `generate_submission()`: Processes all chapters and creates CSV

**Pipeline Flow**:

```
Text → Ensemble NER → Count Entities → Filter Persons →
Group Aliases → Detect Co-occurrences → Generate Graph → Export GraphML
```

#### 7. **nlp_visualize_web.py**

Interactive visualization using PyVis:

- Creates HTML interactive network graphs
- Node sizes based on mention frequency
- Edge widths based on co-occurrence strength
- Auto-opens in web browser

#### 8. **nlp_utils.py**

Utility functions:

- `read_file()`: File reading with UTF-8 encoding
- `load_anti_dict()`: Loads anti-dictionary with comment support

---

## 📊 Data Pipeline

### Input

- **Text Files**: Preprocessed chapter files (`.txt.preprocessed`)
- **Anti-dictionary**: `antidict.txt` - 868 functional words to filter out (prepositions, articles, etc.)
- **Character List**: `characters.txt` - 110 known Asimov characters for enhanced recognition

### Output

- **submission.csv**: Kaggle submission file with GraphML graphs
- **L.txt / LP.txt / LL.txt**: Entity lists (All / Persons / Locations)
- **Interactive HTML**: Network visualization

### Intermediate Files

Each chapter generates:

- `{chapter_id}_L.txt`: All entities
- `{chapter_id}_LP.txt`: Person entities
- `{chapter_id}_LL.txt`: Location entities

---

## 🔧 Configuration Parameters

### Key Hyperparameters

| Parameter         | Default | Description                        |
| ----------------- | ------- | ---------------------------------- |
| `distance_max`    | 25-100  | Co-occurrence window size (words)  |
| `ensemble_method` | "vote"  | NER ensemble strategy              |
| `use_gazetteer`   | True    | Enable Asimov character dictionary |

### Entity Validation Rules

- ❌ Reject ALL CAPS (acronyms)
- ❌ Reject single characters
- ❌ Reject names with hyphens or quotes
- ❌ Reject anti-dictionary matches
- ✅ Accept proper nouns with mixed case

---

## 🚀 Usage

### Running the Pipeline

**Jupyter Notebook** (`nlp_notebook.ipynb`):

```python
# Configure paths
books_config = [
    (list(range(0, 19)), "paf", "data/prelude_a_fondation"),
    (list(range(0, 18)), "lca", "data/les_cavernes_d_acier"),
]

# Generate submission
df_submission = generate_submission(
    books_config=books_config,
    anti_dict_file="antidict.txt",
    output_csv="submission.csv",
    distance_max=100
)
```

**Standalone Script** (`nlp_main.py`):

```bash
python nlp_main.py
```

### Dependencies

```bash
pip install spacy stanza networkx pyvis matplotlib
python -m spacy download fr_core_news_lg
```

---

## 📈 Performance & Results

### Ensemble NER Benefits

The multi-model approach significantly improves character recognition:

- spaCy alone: Misses sci-fi proper nouns
- Stanza alone: Different entity boundaries
- EntityRuler + Voting: Combines strengths, reduces false positives

### Graph Statistics (Typical Chapter)

- **Nodes**: 15-40 characters
- **Edges**: 30-150 co-occurrences
- **Processing Time**: ~10-30 seconds per chapter

### Submission Format

```csv
ID,graphml
paf0,"<?xml version='1.0' encoding='utf-8'?>..."
paf1,"<?xml version='1.0' encoding='utf-8'?>..."
...
```

---

## 🎓 Key Features & Innovations

### 1. **Multi-Model Ensemble NER**

Combines spaCy, Stanza, and custom EntityRuler for robust character extraction

### 2. **Sci-Fi Gazetteer**

Custom dictionary of 40+ Asimov characters with aliases handles genre-specific proper nouns

### 3. **Smart Alias Resolution**

Keyword-based grouping automatically merges character name variants

### 4. **Sliding Window Co-occurrence**

Efficient algorithm handles multi-word names in proximity detection

### 5. **GraphML with Metadata**

Nodes include both canonical names and all aliases in `names` attribute

---

## 🧪 Testing & Validation

### Debug Scripts

- `debug_cooccurrence.py`: Tests co-occurrence detection
- `debug_final_submission.py`: Validates submission format
- `test_entity_ruler.py`: Tests EntityRuler patterns

### Verification Steps

1. Check all 37 chapters are processed
2. Verify nodes have `names` attribute with semicolon-separated aliases
3. Validate GraphML format is parseable
4. Inspect sample graphs for correctness

---

## 📁 Project Structure

```
FinalProject/
├── nlp_*.py              # Core modules
├── main.ipynb            # Jupyter notebook interface
├── nlp_notebook.ipynb    # Google Colab notebook
├── antidict.txt          # Functional words filter (868 entries)
├── characters.txt        # Known Asimov characters (110 entries)
├── submission.csv        # Final output
├── data/                 # Chapter files
│   ├── prelude_a_fondation/
│   │   └── chapter_*.txt.preprocessed
│   └── les_cavernes_d_acier/
│       └── chapter_*.txt.preprocessed
└── docs/
    ├── cahier_des_charges.md
    ├── presentation.md
    └── CANVA_PRESENTATION_CONTEXT.md
```

---

## 🎯 Competition Context

This project is designed for a **Kaggle competition** evaluating character network extraction accuracy. Success metrics include:

- **Precision**: Correctly identifying main characters
- **Recall**: Not missing important characters
- **Graph Accuracy**: Edge weights reflecting actual interactions
- **Alias Handling**: Proper merging of character variants

---

## 🔮 Future Improvements

### Potential Enhancements

1. **Deep Learning NER**: Fine-tune transformer models on sci-fi literature
2. **Coreference Resolution**: Link pronouns to character mentions
3. **Sentiment Analysis**: Add edge attributes for interaction types (positive/negative)
4. **Temporal Networks**: Track character relationships evolution across chapters
5. **Cross-Chapter Tracking**: Maintain character identities across book sections

### Known Limitations

- Relies on proximity for interactions (may miss distant relationships)
- Keyword-based aliasing may merge distinct characters
- Fixed window size may not capture all interaction contexts
- NER models trained on news text struggle with sci-fi terminology

---

## 👥 Target Users

- **Students**: Learning NLP and network analysis
- **Researchers**: Computational literary analysis
- **Developers**: Building narrative understanding systems

---

## 📝 Documentation Files

- `cahier_des_charges.md`: Project requirements specification (French)
- `presentation.md`: Project presentation materials
- `CANVA_PRESENTATION_CONTEXT.md`: Presentation context and notes
- AI assistants logs: `_claude.md`, `_gemini.md`, `_gpt.md`

---

## 🛠️ Technologies

| Technology     | Purpose                             |
| -------------- | ----------------------------------- |
| **Python 3.x** | Core programming language           |
| **spaCy**      | French NER (fr_core_news_lg)        |
| **Stanza**     | Alternative NER model               |
| **NetworkX**   | Graph data structure and algorithms |
| **PyVis**      | Interactive network visualization   |
| **Matplotlib** | Static graph visualization          |
| **Pandas**     | Data manipulation and CSV export    |
| **Jupyter**    | Interactive development             |

---

## 📊 Success Criteria

1. ✅ Process all 37 chapters successfully
2. ✅ Generate valid GraphML output
3. ✅ Identify main characters with aliases
4. ✅ Detect meaningful co-occurrences
5. ✅ Submit to Kaggle leaderboard
6. 🎯 Achieve competitive accuracy score

---

## 🏆 Project Status

**Phase**: Submission-ready
**Completion**: Pipeline fully implemented and tested
**Output**: 37 character networks in GraphML format ready for evaluation

---

_Last Updated: February 2026_
_Course: AMS Projet 1 - M1/S1_

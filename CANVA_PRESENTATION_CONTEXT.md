# Character Network Extraction Project - Presentation Context for Canva

## Project Title

**Automatic Character Network Extraction from Literary Texts**
_NLP & Graph Analysis Project_

---

## 🎯 Project Overview (Slide 1-2)

### What is this project?

An advanced Natural Language Processing (NLP) system that automatically:

- Identifies characters in literary texts (Isaac Asimov novels in French)
- Detects their interactions through co-occurrence analysis
- Builds and visualizes character relationship networks
- Generates Kaggle-ready submissions for character network competitions

### Why does it matter?

- **For researchers**: Computational literary analysis at scale
- **For students**: Understanding narrative structures through data
- **For competitions**: Automated character network extraction for evaluation

---

## 🔍 Problem Statement (Slide 3)

### The Challenge

Manually analyzing character relationships in novels is:

- Time-consuming (hundreds of pages to read)
- Subjective (different interpretations)
- Difficult to quantify (how to measure character importance?)
- Hard to visualize (complex relationship networks)

### Our Solution

Automated pipeline using ensemble NER models and distance-based co-occurrence detection

---

## 🏗️ Technical Architecture (Slide 4-5)

### Pipeline Components (Main Implementation)

**1. Named Entity Recognition (NER) - Ensemble Approach**

- **Dual Model System**:
  - **spaCy** (`fr_core_news_lg`): Fast, general-purpose French NER
  - **Stanza** (French): Stanford's accurate linguistic analysis
- **Voting System**: Entities must be detected by at least 2 models to be accepted
- **Normalization**: Removes quotes, special characters, standardizes text

**2. Entity Classification & Filtering**

- **L** (All entities): Complete list with labels (PER, LOC, GPE, ORG)
- **LP** (Person entities): Filtered characters with validation rules
- **LL** (Location entities): Geographic and geopolitical entities
- **Anti-dictionary**: Removes common false positives

**3. Alias Resolution**

- Keyword-based matching: Groups names sharing common words
- Title removal: Strips "Dr", "Prof", "M.", etc.
- Normalization: Case-insensitive, punctuation-removed
- Canonical naming: First name in group becomes the representative

**4. Co-occurrence Detection**

- **Distance-based windowing**: Characters within 25 words = interaction
- **Token-level analysis**: Word-by-word proximity checking
- **Pair counting**: Tracks how often each character pair co-occurs
- **Sorted tuples**: Ensures (A,B) = (B,A) for consistency

**5. Graph Construction & Export**

- **Nodes**: Characters with mention counts as attributes
- **Edges**: Weighted by co-occurrence frequency
- **NetworkX**: Graph manipulation and analysis
- **GraphML export**: Standard format for graph analysis tools
- **Kaggle submission**: CSV with "names" attribute (semicolon-separated aliases)

---

## 📊 Key Features (Slide 6)

### Smart Entity Validation

- **Anti-dictionary filtering**: Custom blacklist removes common false positives
- **Rule-based validation**: Rejects ALL CAPS, single characters, hyphenated words
- **Type-based filtering**: Separates persons (PER) from locations (LOC/GPE)
- **Normalization**: Cleans punctuation, quotes, extra spaces

### Dual-Model NER Ensemble

- **spaCy** + **Stanza** working in parallel
- **Voting mechanism**: Entity accepted only if ≥2 models agree
- **Label consensus**: Takes majority vote for entity type
- **Higher precision**: Reduces false positives significantly

### Alias Resolution System

- **Keyword matching**: Groups names sharing common words
- **Title stripping**: Removes "Dr", "Prof", "M.", "Mme", etc.
- **Canonical names**: Uses first/most complete name as representative
- **Automatic grouping**: No manual intervention needed

### Flexible Processing

- **Chapter-by-chapter analysis**: Processes books in segments
- **Distance parameter**: Adjustable co-occurrence window (default: 25 words)
- **Multiple formats**: Outputs to TXT, CSV, GraphML, HTML
- **Kaggle integration**: Direct submission format generation

---

## 📚 Test Corpus (Slide 7)

### Books Analyzed

1. **"Les Cavernes d'Acier"** (The Caves of Steel)

   - 18 chapters
   - Detective story
   - Robot-human relationships

2. **"Prélude à Fondation"** (Prelude to Foundation)
   - 19 chapters
   - Epic science fiction
   - Complex political networks

### Why Asimov?

- Rich character networks
- French translations available
- Multiple interacting characters
- Complex narrative structure

---

## 🔧 Technologies Used (Slide 8)

### Programming & Core

- **Language**: Python 3.x
- **Architecture**: Modular design with separate components

### NLP Libraries

- **spaCy** (`fr_core_news_lg`): Fast French NER model
- **Stanza**: Stanford NLP for French
- **Collections**: Counter, defaultdict for efficient data structures
- **Regex**: Text normalization and pattern matching

### Graph & Visualization

- **NetworkX**: Graph creation and manipulation
- **Matplotlib**: Static visualization and plotting
- **PyVis**: Interactive HTML graph visualization
- **GraphML**: Standard graph export format

### Data Processing & Export

- **Pandas**: DataFrame operations for submissions
- **CSV**: Kaggle submission format
- **JSON/GraphML**: Network data exchange
- **Text files**: Entity lists (L.txt, LP.txt, LL.txt)

---

## 📈 Results & Performance (Slide 9)

### Extraction Accuracy

- Multi-model approach improves precision
- Alias resolution reduces duplicates
- Context-aware filtering reduces false positives

### Output Formats

1. **Text Lists**:

   - L.txt (all entities)
   - LP.txt (characters)
   - LL.txt (locations)

2. **Graph Files**:

   - character_network.graphml
   - Interactive HTML visualization

3. **Competition Format**:
   - submission.csv (Kaggle-ready)

### Use Cases

- Literary analysis research
- Character importance ranking
- Narrative structure visualization
- Comparative literature studies

---

## 🎓 Project Methodology (Slide 10)

### Development Phases

**Phase 1: Single-Model NER Implementation**

- Initial spaCy integration for French text
- Basic entity extraction and counting
- Simple filtering by entity type

**Phase 2: Ensemble NER System**

- Added Stanza for improved accuracy
- Implemented voting mechanism (minimum 2 model agreement)
- Label consensus algorithm for conflicting types

**Phase 3: Entity Filtering & Classification**

- Created validation rules (reject ALL CAPS, single chars, hyphens)
- Built anti-dictionary from common false positives
- Separated entities into L (all), LP (persons), LL (locations)

**Phase 4: Alias Resolution**

- Developed keyword-based matching algorithm
- Implemented title removal and normalization
- Created canonical name selection logic

**Phase 5: Co-occurrence Detection**

- Built distance-based windowing system (25-word threshold)
- Token-level proximity analysis
- Pair counting with sorted tuples for consistency

**Phase 6: Graph Construction & Export**

- NetworkX graph generation with weighted edges
- Node attributes (mention counts)
- Multiple export formats: GraphML, CSV, TXT, HTML

**Phase 7: Kaggle Integration**

- Chapter-by-chapter processing pipeline
- "names" attribute with semicolon-separated aliases
- Submission CSV generation for competition

---

## 🚀 Key Achievements

### Technical Innovation

✅ **Ensemble NER with voting system**: 2-model consensus for higher precision
✅ **French literary text adaptation**: Specialized for Asimov novels in French
✅ **Automated alias resolution**: Keyword-based grouping without manual curation
✅ **Distance-based co-occurrence**: 25-word proximity window for interaction detection

### Academic Value

✅ **Combines NLP + Graph Theory**: Multi-disciplinary approach
✅ **Reproducible methodology**: Clear pipeline with modular components
✅ **Competition-validated**: Kaggle-ready output format
✅ **Chapter-level analysis**: Granular processing for better accuracy

### Practical Applications

✅ **Fast text analysis**: Processes entire books in minutes
✅ **Objective metrics**: Character importance based on mention counts
✅ **Visual narrative understanding**: Interactive graph visualization
✅ **Multiple export formats**: TXT, CSV, GraphML, HTML

### Code Quality

✅ **Modular architecture**: Separate files for each component
✅ **Reusable functions**: Easy to adapt for other texts/languages
✅ **Well-documented**: Clear function docstrings and comments
✅ **Efficient data structures**: Counter, defaultdict for performance

---

## 💡 Future Improvements

- Add sentiment analysis to edge weights (positive/negative interactions)
- Implement temporal evolution tracking across chapters
- Expand to more NER models (Flair, CamemBERT) if needed
- Multi-language support for other novel translations
- Machine learning for smarter alias resolution
- Real-time web interface for text upload and analysis
- Community detection algorithms for character groups
- Named entity linking to knowledge bases

---

## 📝 Project Context

**Course**: AMS (Advanced Methods in Statistics/NLP)
**Level**: Master 1 (M1)
**Team**: Collaborative project
**Duration**: Multi-week development
**Goal**: Extract character networks for literary analysis

---

## 🎨 Visual Suggestions for Canva

### Color Scheme

- **Primary**: Deep blue (technology, trust)
- **Secondary**: Orange/amber (creativity, energy)
- **Accent**: Green (success, growth)
- **Text**: Dark gray/black on light backgrounds

### Iconography

- 🔍 Search/magnifying glass for NER
- 🤝 Connected nodes for co-occurrence
- 📊 Network diagrams for graphs
- 📚 Books for corpus
- 🤖 Robot icon for AI/NLP
- ⚙️ Gears for pipeline/processing

### Chart Types to Use

- **Network graphs**: Character relationships
- **Bar charts**: Entity counts
- **Flow diagrams**: Pipeline architecture
- **Comparison tables**: Model performance
- **Timeline**: Project phases

### Layout Tips

- Use **split-screen** for before/after comparisons
- **Icons + text** for feature lists
- **Code snippets** in monospace font (minimal, illustrative only)
- **Screenshots** of actual graph visualizations
- **Process arrows** showing pipeline flow

---

## 📊 Key Numbers to Highlight

- **2 novels** analyzed (Asimov in French)
- **37 chapters** total (18 + 19)
- **2 NER models** in ensemble (spaCy + Stanza)
- **3 entity types** extracted (L, LP, LL)
- **25-word** co-occurrence distance window
- **Voting threshold**: Minimum 2 models must agree
- **8 modular Python files**: Clean architecture
- **4 output formats**: TXT, CSV, GraphML, HTML
- **100% Python** implementation
- **GPU-accelerated**: Stanza with CUDA support

---

## 🎤 Presentation Flow (10 minutes)

1. **Introduction** (1 min): Problem & motivation
2. **Project Goals** (1 min): What we're building
3. **Technical Approach** (3 min): Pipeline components
4. **Technologies** (1.5 min): Tools & libraries
5. **Results** (2 min): Outputs & visualizations
6. **Methodology** (1 min): Development process
7. **Conclusion** (0.5 min): Achievements & future work

---

## 📌 Key Takeaways

### For the Audience

1. Character network extraction can be automated with NLP
2. Ensemble methods improve accuracy over single models
3. Graph theory reveals hidden narrative structures
4. This approach scales to any narrative text

### Project Strengths

- **Innovative**: Multi-model ensemble approach
- **Practical**: Real books, real results
- **Scalable**: Modular architecture
- **Validated**: Competition-tested methodology

---

## 📞 Additional Information

**Project Repository**: WaelMansoura/Reseaux-de-personnage on GitHub
**Documentation**: Comprehensive cahier des charges (specifications document)
**Code Structure**:

- `nlp_main.py`: Main orchestration
- `nlp_multi_ner.py`: Ensemble NER with voting
- `nlp_extract_characters.py`: Entity extraction and filtering
- `nlp_aliases.py`: Alias resolution algorithms
- `nlp_cooccurrence.py`: Distance-based co-occurrence
- `nlp_graph.py`: NetworkX graph generation
- `nlp_visualize_web.py`: PyVis interactive visualization
- `nlp_create_submission.py`: Kaggle CSV export pipeline
  **Testing**: Multiple books, chapter-by-chapter validation
  **Export Formats**: TXT (entity lists), CSV (Kaggle), GraphML (networks), HTML (interactive)
  **Anti-dictionary**: Custom blacklist for filtering false positives

---

_End of Context Document_
_This document provides all necessary information to create a professional 10-minute presentation about the Character Network Extraction project._

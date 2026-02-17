# Kaggle Score Improvement Strategies

## Character Network Extraction Project

This document outlines actionable strategies to improve your Kaggle competition score for the character network extraction task.

---

## 🎯 Quick Wins (High Impact, Low Effort)

### 1. **Optimize Co-occurrence Window Size**

**Current**: `distance_max = 100` words

**Try**:

- Test multiple window sizes: `[25, 50, 75, 100, 150, 200]`
- Use **scene-based windows** instead of fixed word counts
- Implement **adaptive windows** based on dialogue detection

```python
# Experiment with different window sizes
for distance in [25, 50, 75, 100, 150]:
    df = generate_submission(distance_max=distance,
                             output_csv=f"submission_{distance}.csv")
```

**Why**: Different books/chapters may have different narrative pacing. Dialogue-heavy sections need smaller windows, descriptive passages need larger ones.

---

### 2. **Improve Alias Grouping Algorithm**

**Current**: Simple keyword overlap matching

**Improvements**:

- **Levenshtein distance** for fuzzy matching (handles typos)
- **First/last name detection** (keep "Hari Seldon" and "Hari" but not "Hari" and "Harinder")
- **Title-based grouping** (Dr., Mr., Commissioner, etc.)
- **Frequency-based canonical selection** (most frequent variant becomes canonical)

```python
from fuzzywuzzy import fuzz

def better_alias_matching(name1, name2, threshold=85):
    # Fuzzy string matching
    if fuzz.ratio(name1, name2) > threshold:
        return True

    # Check if one is substring of other (with word boundaries)
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())

    # One name is subset of another
    if words1.issubset(words2) or words2.issubset(words1):
        return True

    return False
```

---

### 3. **Filter Low-Confidence Entities**

**Current**: All NER predictions kept if valid

**Add**:

- **Minimum occurrence threshold**: Remove characters mentioned < 2-3 times
- **Entity confidence scores**: Use spaCy's entity confidence if available
- **Context validation**: Check if entity appears in typical character contexts

```python
def filter_by_frequency(LP, min_occurrences=2):
    """Remove characters mentioned fewer than min_occurrences times"""
    return Counter({name: count for name, count in LP.items()
                    if count >= min_occurrences})
```

---

## 🔬 Advanced NER Improvements

### 4. **Fine-tune NER Model on French Literature**

**Current**: Using pre-trained `fr_core_news_lg` (trained on news)

**Improvement**:

- Fine-tune spaCy model on French sci-fi/literature corpus
- Use **CamemBERT** (French BERT) for better literary text understanding
- Train on annotated Asimov passages

**Resources**:

- [spaCy training guide](https://spacy.io/usage/training)
- CamemBERT: `camembert-base` from HuggingFace
- Annotate 500-1000 sentences manually for training data

---

### 5. **Add Coreference Resolution**

**Current**: Only detects explicit name mentions

**Add**: Resolve pronouns and references

```python
# Example: "Hari left. He was worried." → both refer to Hari
# Use: neuralcoref or fastcoref for French
import neuralcoref

nlp = spacy.load('fr_core_news_lg')
neuralcoref.add_to_pipe(nlp, language='fr')

def resolve_coreferences(text):
    doc = nlp(text)
    # Replace pronouns with their referents
    resolved = doc._.coref_resolved
    return resolved
```

**Why**: Captures interactions where characters are referred to by pronouns, significantly increasing edge detection accuracy.

---

### 6. **Improve Gazetteer with Context Patterns**

**Current**: Static entity list in EntityRuler

**Improvements**:

- Add **contextual patterns**: "Commissaire Baley", "Dr. Seldon"
- Include **robot prefixes**: R. Daneel, R. Giskard
- Add **French variations**: "d'Acier" → "Acier"

```python
patterns = [
    # Title + Name patterns
    {"label": "PER", "pattern": [{"LOWER": "commissaire"}, {"IS_TITLE": True}]},
    {"label": "PER", "pattern": [{"LOWER": "dr"}, {"TEXT": "."}, {"IS_TITLE": True}]},

    # Robot patterns
    {"label": "PER", "pattern": [{"UPPER": "R"}, {"TEXT": "."}, {"IS_TITLE": True}]},
]
```

---

## 📊 Graph Construction Improvements

### 7. **Weight Edges by Interaction Quality**

**Current**: All co-occurrences weighted equally

**Improvements**:

- **Distance decay**: Closer mentions = higher weight
- **Dialogue bonus**: Co-occurrence in same dialogue = 2x weight
- **Chapter boundaries**: Penalize cross-chapter co-occurrences

```python
def weighted_cooccurrence(text, characters, distance_max=100):
    cooccurrences = Counter()

    for i in range(len(tokens)):
        for char1, char2 in pairs_in_window(i, distance_max):
            # Distance-based weighting
            distance = get_distance(char1_pos, char2_pos)
            weight = 1.0 / (1 + distance/10)  # Decay function

            # Dialogue bonus
            if in_same_dialogue(char1_pos, char2_pos):
                weight *= 2.0

            cooccurrences[(char1, char2)] += weight

    return cooccurrences
```

---

### 8. **Prune Weak Edges**

**Current**: All edges kept regardless of strength

**Add**: Remove edges below threshold

```python
def prune_graph(G, min_weight=2, min_degree=1):
    """Remove weak edges and isolated nodes"""
    # Remove edges with weight < threshold
    edges_to_remove = [(u, v) for u, v, w in G.edges(data='weight')
                       if w < min_weight]
    G.remove_edges_from(edges_to_remove)

    # Remove isolated or weakly connected nodes
    nodes_to_remove = [n for n, d in G.degree() if d <= min_degree]
    G.remove_nodes_from(nodes_to_remove)

    return G
```

---

### 9. **Detect and Highlight Main Characters**

**Current**: All characters treated equally

**Add**: Rank characters by importance

```python
def identify_main_characters(G, top_n=10):
    """Use centrality metrics to find main characters"""
    import networkx as nx

    # Multiple centrality measures
    degree_cent = nx.degree_centrality(G)
    betweenness_cent = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G, weight='weight')

    # Combine metrics
    importance = {}
    for node in G.nodes():
        importance[node] = (
            0.4 * degree_cent.get(node, 0) +
            0.3 * betweenness_cent.get(node, 0) +
            0.3 * pagerank.get(node, 0)
        )

    # Add as node attribute
    for node, score in importance.items():
        G.nodes[node]['importance'] = score

    return G
```

---

## 🔍 Text Preprocessing Improvements

### 10. **Better Dialogue Detection**

**Current**: No dialogue-specific handling

**Add**: Detect and leverage dialogue structure

```python
import re

def detect_dialogues(text):
    """Extract dialogue sections for better character interaction detection"""
    # French dialogue markers: « », —, "
    dialogue_pattern = r'[«"](.*?)[»"]|^—\s*(.+)$'
    dialogues = re.findall(dialogue_pattern, text, re.MULTILINE)
    return dialogues

def characters_in_dialogue(dialogue, character_list):
    """Find which characters are in a dialogue segment"""
    # Higher confidence for characters mentioned in same dialogue
    pass
```

---

### 11. **Scene Segmentation**

**Current**: Treats entire chapter as continuous text

**Improvement**: Detect scene breaks

```python
def segment_by_scenes(text):
    """Split text into scenes based on indicators"""
    # Scene break indicators: "***", blank lines, time/location changes
    scene_breaks = r'\n\s*\n\s*\n|\*\*\*|_{3,}'
    scenes = re.split(scene_breaks, text)
    return [s.strip() for s in scenes if s.strip()]
```

**Why**: Characters in same scene are more likely to interact than characters across scenes.

---

## 🧪 Ensemble & Validation

### 12. **Weighted Ensemble Voting**

**Current**: Equal vote weight for spaCy and Stanza

**Improvement**:

```python
def weighted_ensemble(text, weights={'spacy': 0.6, 'stanza': 0.4}):
    """Give more weight to better-performing models"""
    entities = defaultdict(float)

    spacy_ents = extract_spacy(text)
    for ent, label in spacy_ents:
        entities[(ent, label)] += weights['spacy']

    stanza_ents = extract_stanza(text)
    for ent, label in stanza_ents:
        entities[(ent, label)] += weights['stanza']

    # Keep entities above threshold
    threshold = 0.5
    return [(ent, label) for (ent, label), score in entities.items()
            if score >= threshold]
```

---

### 13. **Cross-Validation on Chapters**

**Test improvements systematically**:

```python
# Hold out 20% of chapters for validation
validation_chapters = ["paf0", "paf5", "paf10", "lca0", "lca5"]
training_chapters = [all others]

def evaluate_pipeline(chapters, metric_func):
    """Evaluate pipeline changes before submitting"""
    scores = []
    for chapter in chapters:
        G = process_chapter(chapter)
        score = metric_func(G)
        scores.append(score)
    return np.mean(scores)
```

---

## 📈 Advanced Techniques

### 14. **Add Entity Linking / Disambiguation**

**Problem**: Multiple characters with similar names

**Solution**: Entity linking to knowledge base

```python
# Link "Seldon" → which Seldon? Hari or Raych?
# Use context: if "psychohistory" nearby → likely Hari
# Use chapter knowledge: which Seldon appears in this book?

def disambiguate_entity(entity, context_window, knowledge_base):
    """Resolve ambiguous names using context"""
    candidates = knowledge_base.get_candidates(entity)

    if len(candidates) == 1:
        return candidates[0]

    # Score each candidate by context similarity
    scores = {}
    for candidate in candidates:
        context_words = set(context_window.lower().split())
        known_associations = knowledge_base.get_associations(candidate)
        overlap = len(context_words & known_associations)
        scores[candidate] = overlap

    return max(scores, key=scores.get)
```

---

### 15. **Temporal Network Analysis**

**Add temporal dimension to graphs**:

```python
def create_temporal_graph(chapters):
    """Track how relationships evolve across chapters"""
    temporal_G = nx.DiGraph()

    for i, chapter in enumerate(chapters):
        G = process_chapter(chapter)

        # Add timestamp to edges
        for u, v, data in G.edges(data=True):
            if temporal_G.has_edge(u, v):
                temporal_G[u][v]['weights'].append(data['weight'])
                temporal_G[u][v]['chapters'].append(i)
            else:
                temporal_G.add_edge(u, v,
                                   weights=[data['weight']],
                                   chapters=[i])

    return temporal_G
```

---

### 16. **Use Book-Specific Heuristics**

**Leverage domain knowledge**:

**For Foundation series**:

- Prioritize psychohistory-related terms
- Recognize political/scientific roles
- Handle time-skips (different characters, same name patterns)

**For Caves of Steel**:

- Robotics vocabulary as strong signal
- Earth vs. Spacer context
- Detective story structure (suspects, witnesses)

```python
DOMAIN_TERMS = {
    'foundation': ['psychohistoire', 'fondation', 'trantor', 'empire'],
    'caves_of_steel': ['robot', 'spacien', 'terrien', 'commissaire']
}

def boost_domain_entities(entities, book_type):
    """Boost confidence for entities in domain contexts"""
    boosted = []
    for ent, label in entities:
        context = get_context(ent, window=50)
        if any(term in context.lower()
               for term in DOMAIN_TERMS[book_type]):
            # Keep this entity with higher confidence
            boosted.append((ent, label, 'high'))
        else:
            boosted.append((ent, label, 'normal'))
    return boosted
```

---

## 🛠️ Implementation Strategy

### Phase 1: Quick Wins (Week 1)

1. ✅ Test window sizes [25, 50, 75, 100, 150]
2. ✅ Add minimum frequency filter (>=2 mentions)
3. ✅ Improve alias matching with fuzzy logic
4. ✅ Submit and compare scores

### Phase 2: NER Improvements (Week 2)

5. ✅ Add coreference resolution
6. ✅ Enhance gazetteer patterns
7. ✅ Implement weighted ensemble
8. ✅ Submit new version

### Phase 3: Graph Refinement (Week 3)

9. ✅ Add edge weighting by distance
10. ✅ Implement graph pruning
11. ✅ Calculate character importance
12. ✅ Submit refined graphs

### Phase 4: Advanced (Week 4)

13. ✅ Scene segmentation
14. ✅ Entity disambiguation
15. ✅ Temporal analysis
16. ✅ Final submission

---

## 📊 Metrics to Track

For each experiment, track:

```python
metrics = {
    'num_nodes': G.number_of_nodes(),
    'num_edges': G.number_of_edges(),
    'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes(),
    'density': nx.density(G),
    'num_components': nx.number_connected_components(G),
    'largest_component_size': len(max(nx.connected_components(G), key=len)),
    'kaggle_score': 0.XXX  # Update after submission
}
```

**Expected improvements**:

- Baseline: Current score
- After Phase 1: +5-10% improvement
- After Phase 2: +10-20% improvement
- After Phase 3: +15-25% improvement
- After Phase 4: +20-30% improvement

---

## 🎓 Additional Resources

### Libraries to Explore

- **spaCy-transformers**: Use BERT-based models for French
- **flair**: Alternative NER with good French support
- **neuralcoref**: Coreference resolution
- **nltk.metrics**: Evaluation metrics
- **python-Levenshtein**: Fast string similarity

### Datasets for Training

- **WikiNER**: Named entities from Wikipedia (French)
- **French Treebank**: Annotated French text
- **Project Gutenberg**: French literature for domain adaptation

### Papers to Read

- "Neural Coreference Resolution" (Clark & Manning, 2016)
- "Character Network Analysis in Literature"
- "Entity Disambiguation in Literary Texts"

---

## ⚡ Final Tips

1. **Submit frequently**: Test each improvement individually
2. **Keep baselines**: Always compare against previous best
3. **Document everything**: Track what works and what doesn't
4. **Analyze errors**: Look at specific chapters where you lose points
5. **Ensemble submissions**: Combine multiple good approaches
6. **Check for overfitting**: Don't optimize only for visible test set
7. **Read discussions**: Kaggle forums often have crucial insights

---

## 🎯 Priority Actions

**Start with these 3 today**:

1. **Test window sizes** → 30 minutes
2. **Add frequency filter (min_count=2)** → 15 minutes
3. **Improve alias fuzzy matching** → 1 hour

**Expected gain**: +10-15% score improvement

Good luck! 🚀

---

_Last updated: February 2026_
_Based on current Kaggle character network extraction competition_

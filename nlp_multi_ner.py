import spacy
import stanza
from collections import Counter, defaultdict
import re
from pathlib import Path

# ---------------------------------------
# Load models once (important for speed)
# ---------------------------------------
spacy_nlp = spacy.load("fr_core_news_lg")

# ---------------------------------------
# Add EntityRuler for character extraction
# ---------------------------------------
def load_character_patterns(character_file="characters.txt"):
    """
    Load character names from file and create patterns for EntityRuler.
    Args:
        character_file: Path to character list file (one name per line)
    Returns:
        List of pattern dictionaries for EntityRuler
    """
    patterns = []
    file_path = Path(__file__).parent / character_file
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                name = line.strip()
                # Skip comments and empty lines
                if not name or name.startswith('#'):
                    continue
                # Add each character name as a pattern
                patterns.append({
                    "label": "PER",  # Person entity label
                    "pattern": name
                })
    else:
        print(f"Warning: Character file {character_file} not found")
    
    return patterns

# Create and add EntityRuler to pipeline
def setup_entity_ruler(nlp, character_file="characters.txt"):
    """
    Add EntityRuler to the spaCy pipeline with character patterns.
    Args:
        nlp: spaCy language model
        character_file: Path to character list file
    """
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    character_patterns = load_character_patterns(character_file)
    ruler.add_patterns(character_patterns)
    print(f"Loaded {len(character_patterns)} character patterns for NER enhancement")

stanza.download("fr")
stanza_nlp = stanza.Pipeline(lang="fr", processors="tokenize,ner", use_gpu=True)

setup_entity_ruler(spacy_nlp, character_file="characters.txt")

# ---------------------------------------
# Normalization function
# ---------------------------------------
def normalize_span(text):
    t = text.strip()
    t = re.sub(r"[«»""]", "", t)
    return t


# ---------------------------------------
# Run models independently
# ---------------------------------------
def extract_spacy(text):
    doc = spacy_nlp(text)
    ents = [(normalize_span(ent.text), ent.label_) for ent in doc.ents]
    return ents


def extract_stanza(text):
    doc = stanza_nlp(text)
    ents = []
    for sentence in doc.sentences:
        for ent in sentence.ents:
            ents.append((normalize_span(ent.text), ent.type))
    return ents


# ---------------------------------------
# Ensemble Logic
# ---------------------------------------
def ensemble_entities(text, method="vote"):
    """
    method:
        - union → keep all entities
        - intersection → only keep those found by both models
        - vote → keep if both models agree
    """

    spa = extract_spacy(text)
    sta = extract_stanza(text)

    all_entities = {
        "spacy": spa,
        "stanza": sta
    }

    # Map: entity_text → {labels...}
    counter = defaultdict(lambda: defaultdict(int))

    for model_name, ents in all_entities.items():
        for text, label in ents:
            counter[text][label] += 1

    final = []

    for text, label_map in counter.items():
        # Find majority label
        best_label = max(label_map, key=lambda k: label_map[k])
        votes = label_map[best_label]

        if method == "union":
            final.append((text, best_label))

        elif method == "intersection":
            if votes == 2:
                final.append((text, best_label))

        elif method == "vote":
            if votes >= 2:
                final.append((text, best_label))

    return final

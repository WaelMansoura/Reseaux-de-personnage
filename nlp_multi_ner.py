import spacy
import stanza
from collections import Counter, defaultdict
import re
from pathlib import Path

# =============================================================================
# ASIMOV FOUNDATION GAZETTEER (Enhanced character/location recognition)
# =============================================================================
# Canonical names with aliases for better entity recognition
# This significantly improves NER accuracy for sci-fi proper nouns

ASIMOV_CHARACTERS = {
    # Prelude to Foundation / Forward the Foundation
    "Hari Seldon": ["Seldon", "Hari"],
    "Eto Demerzel": ["Demerzel", "Eto"],
    "Cleon I": ["Cléon", "l'Empereur", "Empereur", "Sire"],
    "Chetter Hummin": ["Hummin", "Chetter"],
    "Dors Venabili": ["Dors", "Venabili"],
    "Yugo Amaryl": ["Amaryl", "Yugo"],
    "Raych Seldon": ["Raych"],
    "R. Daneel Olivaw": ["Daneel", "R. Daneel", "Daneel Olivaw"],
    
    # Caves of Steel / Robot series
    "Elijah Baley": ["Baley", "Elijah", "Lije"],
    "R. Giskard Reventlov": ["Giskard", "R. Giskard"],
    "Jessie Baley": ["Jessie"],
    "Bentley Baley": ["Bentley", "Ben"],
    "Julius Enderby": ["Enderby", "Julius"],
    
    # Foundation Series
    "Gaal Dornick": ["Dornick", "Gaal"],
    "Salvor Hardin": ["Hardin", "Salvor"],
    "Hober Mallow": ["Mallow", "Hober"],
    "Bel Riose": ["Riose", "Bel"],
    "Le Mulet": ["Mulet", "the Mule"],
    "Bayta Darell": ["Bayta", "Bay"],
    "Toran Darell": ["Toran"],
    "Arkady Darell": ["Arkady"],
    "Golan Trevize": ["Trevize", "Golan"],
    "Janov Pelorat": ["Pelorat", "Janov", "Pel"],
    "Bliss": ["Blissenobiarella"],
}

ASIMOV_LOCATIONS = {
    # Major planets
    "Trantor": ["Trantor"],
    "Terminus": ["Terminus"],
    "Helicon": ["Hélicon", "Helicon"],
    "Kalgan": ["Kalgan"],
    "Anacreon": ["Anacreon"],
    "Gaia": ["Gaïa", "Gaia"],
    "Aurora": ["Aurora"],
    "Solaria": ["Solaria"],
    
    # Places/Institutions
    "Streeling": ["Université de Streeling", "Streeling"],
    "Bibliothèque Galactique": ["Bibliothèque"],
    "Palais Impérial": ["Palais"],
}

# =============================================================================
# LAZY LOADING - Models initialized only when first used
# =============================================================================
# This prevents re-downloading and re-initialization on module reload

_spacy_nlp = None
_stanza_nlp = None
_models_initialized = False

def get_spacy_model():
    """
    Lazy load spaCy model with EntityRuler.
    Models are loaded only once, even if module is reloaded.
    """
    global _spacy_nlp, _models_initialized
    
    if _spacy_nlp is None:
        print("🔄 Loading spaCy model (fr_core_news_lg)...")
        _spacy_nlp = spacy.load("fr_core_news_lg")
        
        # Setup EntityRuler with gazetteer
        setup_entity_ruler(_spacy_nlp, use_gazetteer=True)
        print("✅ spaCy model loaded!")
    
    return _spacy_nlp


def get_stanza_model():
    """
    Lazy load Stanza model.
    Models are loaded only once, even if module is reloaded.
    """
    global _stanza_nlp
    
    if _stanza_nlp is None:
        print("🔄 Loading Stanza model (fr)...")
        # Only download if not already downloaded
        try:
            _stanza_nlp = stanza.Pipeline(
                lang="fr", 
                processors="tokenize,ner", 
                use_gpu=False,  # Set to True if GPU available
                download_method=stanza.DownloadMethod.REUSE_RESOURCES  # Don't re-download
            )
        except:
            # If models not found, download them first
            print("📥 Downloading Stanza models (one-time setup)...")
            stanza.download("fr")
            _stanza_nlp = stanza.Pipeline(
                lang="fr", 
                processors="tokenize,ner", 
                use_gpu=False
            )
        print("✅ Stanza model loaded!")
    
    return _stanza_nlp


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

def setup_entity_ruler(nlp, character_file="characters.txt", use_gazetteer=True):
    """
    Add EntityRuler to the spaCy pipeline with character patterns.
    Args:
        nlp: spaCy language model
        character_file: Path to character list file (used if use_gazetteer=False)
        use_gazetteer: If True, use built-in ASIMOV gazetteer; if False, load from file
    """
    # Check if entity_ruler already exists to avoid duplicate
    if "entity_ruler" in nlp.pipe_names:
        return  # Already setup, skip
    
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    
    if use_gazetteer:
        # Use the comprehensive built-in gazetteer (recommended)
        patterns = []
        
        # Add character patterns with all aliases
        for canonical, aliases in ASIMOV_CHARACTERS.items():
            patterns.append({"label": "PER", "pattern": canonical})
            for alias in aliases:
                patterns.append({"label": "PER", "pattern": alias})
        
        # Add location patterns with all aliases
        for canonical, aliases in ASIMOV_LOCATIONS.items():
            patterns.append({"label": "LOC", "pattern": canonical})
            for alias in aliases:
                patterns.append({"label": "LOC", "pattern": alias})
        
        ruler.add_patterns(patterns)
        print(f"   ✓ {len(patterns)} patterns ({len(ASIMOV_CHARACTERS)} characters, {len(ASIMOV_LOCATIONS)} locations)")
    else:
        # Fallback: load from file (for custom character lists)
        character_patterns = load_character_patterns(character_file)
        ruler.add_patterns(character_patterns)
        print(f"   ✓ {len(character_patterns)} patterns from {character_file}")


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
    """Extract entities using spaCy with lazy loading"""
    nlp = get_spacy_model()  # Lazy load model
    doc = nlp(text)
    ents = [(normalize_span(ent.text), ent.label_) for ent in doc.ents]
    return ents


def extract_stanza(text):
    """Extract entities using Stanza with lazy loading"""
    nlp = get_stanza_model()  # Lazy load model
    doc = nlp(text)
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

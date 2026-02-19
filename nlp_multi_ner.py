import spacy
import stanza
from collections import Counter, defaultdict
import re
from pathlib import Path

try:
    from flair.nn import Classifier
    from flair.data import Sentence as FlairSentence
    _FLAIR_AVAILABLE = True
except ImportError:
    _FLAIR_AVAILABLE = False
    print("⚠️  flair not installed. Run: pip install flair")

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
_flair_tagger = None
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


def get_flair_model():
    """
    Lazy load Flair French NER tagger.
    Uses 'fr-ner' (BiLSTM-CRF, French-specific, no sentencepiece dependency).
    Model auto-downloads to ~/.flair/ on first call (~450 MB, one-time).
    Labels: PER, LOC, ORG, MISC — identical to spaCy/Stanza.
    """
    global _flair_tagger

    if not _FLAIR_AVAILABLE:
        raise ImportError("flair is not installed. Run: pip install flair")

    if _flair_tagger is None:
        print("🔄 Loading Flair NER model (fr-ner)...")
        _flair_tagger = Classifier.load("fr-ner")
        print("✅ Flair model loaded!")

    return _flair_tagger


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


def _chunk_text(text, max_chars=900):
    """
    Split text into chunks safe for Flair's BiLSTM sequence model (~250 tokens).
    Splits on double-newline paragraph breaks first, then falls back to
    sentence-ending punctuation. max_chars=900 ≈ 150-200 tokens (safe margin).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > max_chars:
                # Split long paragraph by sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sub = ""
                for sent in sentences:
                    if len(sub) + len(sent) + 1 <= max_chars:
                        sub = (sub + " " + sent).strip()
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = sent
                if sub:
                    chunks.append(sub)
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks


def extract_flair(text):
    """
    Extract entities using Flair fr-ner with lazy loading.
    Handles long texts by chunking on paragraph/sentence boundaries.
    Labels: PER, LOC, ORG, MISC — same as spaCy/Stanza, no remapping needed.
    """
    tagger = get_flair_model()
    ents = []
    for chunk in _chunk_text(text):
        sentence = FlairSentence(chunk)
        tagger.predict(sentence)
        for span in sentence.get_spans("ner"):
            word = normalize_span(span.text)
            if word:
                ents.append((word, span.tag))
    return ents


# ---------------------------------------
# Ensemble Logic
# ---------------------------------------
def ensemble_entities(text, method="vote", use_flair=True):
    """
    Combine NER predictions from spaCy, Stanza, and (optionally) Flair.

    method:
        - union        → keep any entity found by ≥1 model
        - intersection → keep only entities found by ALL active models
        - vote         → keep entities found by ≥2 models (majority vote)

    use_flair:
        If True (default) and flair is installed, Flair fr-ner is used as
        a third voter. Falls back silently to 2-model ensemble if unavailable.
    """
    spa = extract_spacy(text)
    sta = extract_stanza(text)

    all_entities = {
        "spacy": spa,
        "stanza": sta,
    }

    if use_flair and _FLAIR_AVAILABLE:
        try:
            fla = extract_flair(text)
            all_entities["flair"] = fla
        except Exception as e:
            print(f"⚠️  Flair extraction failed, falling back to 2-model ensemble: {e}")

    n_models = len(all_entities)
    vote_threshold = 2  # true majority for both 2-model and 3-model setups

    # Map: entity_text → {label → vote count}
    # Deduplicate per model so one model cannot double-vote the same entity
    counter = defaultdict(lambda: defaultdict(int))
    for model_name, ents in all_entities.items():
        seen = set()
        for entity_text, label in ents:
            key = (entity_text, label)
            if key not in seen:
                counter[entity_text][label] += 1
                seen.add(key)

    final = []
    for entity_text, label_map in counter.items():
        best_label = max(label_map, key=lambda k: label_map[k])
        votes = sum(label_map.values())

        if method == "union":
            final.append((entity_text, best_label))

        elif method == "intersection":
            if votes == n_models:  # all active models agree
                final.append((entity_text, best_label))

        elif method == "vote":
            if votes >= vote_threshold:  # ≥2 models agree
                final.append((entity_text, best_label))

    return final

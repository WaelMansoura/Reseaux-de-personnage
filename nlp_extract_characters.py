import spacy
from collections import Counter
import re

# =============================================================================
# LAZY LOADING - spaCy model loaded only once
# =============================================================================

_nlp_model = None

def get_spacy_model():
    """
    Lazy load spaCy model for entity extraction.
    Model is loaded only once, even if module is reloaded.
    """
    global _nlp_model
    
    if _nlp_model is None:
        print("🔄 Loading spaCy model for entity extraction...")
        _nlp_model = spacy.load("fr_core_news_lg")
        print("✅ spaCy model loaded!")
    
    return _nlp_model


def extract_entities(text: str):
    """
    Returns raw NER counts:
        - L: all named entities
    """
    nlp = get_spacy_model()  # Lazy load
    doc = nlp(text)

    entities = []

    for ent in doc.ents:
        # ent.text = surface form
        # ent.label_ = PERSON, LOC, ORG, MISC
        entities.append((ent.text, ent.label_))

    return entities


def count_entities(entities):
    """
    Count how many times each surface form appears.
    Returns a dict: { (text, label): count }
    """
    return Counter(entities)



def filter_persons(L, anti_dict=None):
    """
    From L (raw entity counts), extract only PERSON entities.
    LP = { entity_text: count }
    """
    if anti_dict is None:
        anti_dict = set()

    persons = Counter()

    for (text, label), count in L.items():
        if label == "PER" and is_valid_entity(text):  # spaCy uses "PER"
            norm = text.strip().lower()
            if norm not in anti_dict:
                persons[text] = persons[text] + count

    return persons

def filter_locations(L):
    """
    Extract locations from L.
    spaCy uses:
        LOC = location
        GPE = geopolitical entity
    LL = { entity_text: count }
    """
    locations = Counter()

    for (text, label), count in L.items():
        if label in ("LOC", "GPE") and is_valid_entity(text):
            locations[text] = locations[text] + count

    return locations

def is_valid_entity(text: str):
    """
    Common filtering rules for PERSON and LOCATION entities.

    Rules:
    - Reject ALL CAPS (ACRONYMS)
    - Reject names with hyphens
    - Reject 1-character entities
    - Reject empty / whitespace-only
    """

    t = text.strip()

    # Reject empty
    if not t:
        return False

    # Reject single character (e.g. "A", "X", "B")
    if len(t) == 1:
        return False

    # Reject ALL CAPS (ACRONYMS: "ONU", "USA", "GNA")
    if t.isupper():
        return False
    
    # reject all caps and spaces (e.g. "HELLO WORLD")
    if re.fullmatch(r"[A-Z\s]+", t):
        return False

    # Reject names containing "-"
    if "-" in t or "–" in t or "?" in t or '"' in t:
        return False
    
    return True

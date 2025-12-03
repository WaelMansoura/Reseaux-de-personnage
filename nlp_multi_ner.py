import spacy
import stanza
from flair.data import Sentence
from flair.models import SequenceTagger

from collections import Counter, defaultdict
import re

# ---------------------------------------
# Load models once (important for speed)
# ---------------------------------------
spacy_nlp = spacy.load("fr_core_news_lg")

stanza.download("fr")
stanza_nlp = stanza.Pipeline(lang="fr", processors="tokenize,ner", use_gpu=True)

flair_tagger = SequenceTagger.load("ner-multi")   # multilingual


# ---------------------------------------
# Normalization function
# ---------------------------------------
def normalize_span(text):
    t = text.strip()
    t = re.sub(r"[«»“”]", "", t)
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


def extract_flair(text):
    sentence = Sentence(text)
    flair_tagger.predict(sentence)

    ents = []
    for entity in sentence.get_spans('ner'):
        ents.append((normalize_span(entity.text), entity.tag))
    return ents


# ---------------------------------------
# Ensemble Logic
# ---------------------------------------
def ensemble_entities(text, method="vote"):
    """
    method:
        - union → keep all entities
        - intersection → only keep those found by all models
        - vote → keep if at least 2/3 models agree
    """

    spa = extract_spacy(text)
    sta = extract_stanza(text)
    fla = extract_flair(text)

    all_entities = {
        "spacy": spa,
        "stanza": sta,
        "flair": fla
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
            if votes == 3:
                final.append((text, best_label))

        elif method == "vote":
            if votes >= 2:
                final.append((text, best_label))

    return final

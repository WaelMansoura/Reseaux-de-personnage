"""
nlp_manual_ner.py — Rule-based NER for Asimov novels (no AI models).

Three strategies combined:
  1. Gazetteer lookup (characters.txt + hard-coded Asimov names)
  2. Capitalization heuristics (unknown proper nouns mid-sentence)
  3. Regex patterns (titled names: Docteur X, R. Name, etc.)

Output format: list[tuple[str, str]]  — identical to ensemble_entities()
so all downstream code (count_entities, filter_persons, aliases, etc.)
works unchanged.
"""

import re
from collections import Counter
from pathlib import Path

# =============================================================================
# ASIMOV GAZETTEER — same data as nlp_multi_ner.py, kept here to avoid
# importing the AI-dependent module
# =============================================================================

ASIMOV_CHARACTERS = {
    # Prelude to Foundation / Forward the Foundation
    "Hari Seldon": ["Seldon", "Hari"],
    "Eto Demerzel": ["Demerzel", "Eto"],
    "Cleon I": ["Cléon", "l'Empereur", "Empereur", "Sire"],
    "Chetter Hummin": ["Hummin", "Chetter"],
    "Dors Venabili": ["Dors", "Venabili"],
    "Yugo Amaryl": ["Amaryl", "Yugo"],
    "Raych Seldon": ["Raych"],
    "R. Daneel Olivaw": ["Daneel", "R. Daneel", "Daneel Olivaw", "Olivaw"],
    "Alem": ["Alem"],

    # Caves of Steel / Robot series
    "Elijah Baley": ["Baley", "Elijah", "Lije", "Elie"],
    "R. Giskard Reventlov": ["Giskard", "R. Giskard"],
    "Jessie Baley": ["Jessie", "Jézabel", "Jessica"],
    "Bentley Baley": ["Bentley", "Ben"],
    "Julius Enderby": ["Enderby", "Julius"],

    # Prelude to Foundation — secondary characters
    "Marron": ["Marron"],
    "Grisnuage": ["Grisnuage"],
    "Endor Levanian": ["Levanian"],
    "Mycélium": ["Mycélium"],
    "Hano Lindor": ["Lindor", "Hano"],
    "Lanel Russ": ["Russ", "Lanel"],
    "Gebore Astinwald": ["Astinwald", "Gebore"],
    "Emmer Thalus": ["Thalus", "Emmer"],
    "Mannix IV": ["Mannix"],
    "Davan": ["Davan"],
    "Rachelle": ["Rachelle"],
    "Mère Rittah": ["Rittah"],
    "Casilia Tisalver": ["Casilia"],
    "Tisalver": ["Tisalver"],
    "Clowzia": ["Clowzia"],
    "Leggen": ["Leggen"],
    "Maître-du-Soleil Quatorze": ["Maître-du-Soleil Quatorze", "Quatorze"],

    # Caves of Steel — secondary characters
    "Dr Sarton": ["Sarton", "Dr Sarton"],
    "R. Sammy": ["R. Sammy"],
    "Philip Norris": ["Norris", "Philip Norris"],
    "Clousarr": ["Clousarr", "Francis Clousarr", "Francis"],
    "Gerrigel": ["Gerrigel"],
    "Vincent Barrett": ["Barrett", "Vincent Barrett", "Vince"],
    "Dr Fastolfe": ["Fastolfe", "Dr Fastolfe"],

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
    # Trantor sectors / neighborhoods
    "Mycogène": ["Mycogène"],
    "Dahl": ["Dahl"],
    "Billibotton": ["Billibotton"],
    "Kan": ["Kan"],
    "Sacratorium": ["Sacratorium"],
    "Damiano Nord": ["Damiano Nord"],
    "Cinna": ["Cinna"],
    # Earth cities / LCA locations
    "Spacetown": ["Spacetown"],
    "New York": ["New York"],
    "Los Angeles": ["Los Angeles"],
    "Londres": ["Londres"],
    "Newark": ["Newark"],
    "Trenton": ["Trenton"],
    "Williamsburg": ["Williamsburg"],
    "Berlin": ["Berlin"],
    "Brighton": ["Brighton"],
    "Norwich": ["Norwich"],
    "Coventry": ["Coventry"],
    "Canterbury": ["Canterbury"],
    "Budapest": ["Budapest"],
    "Shanghai": ["Shanghai", "Shanghaï"],
    "Tachkent": ["Tachkent"],
    "Winnipeg": ["Winnipeg"],
    "Toronto": ["Toronto"],
    "Buenos Aires": ["Buenos Aires"],
    "San Francisco": ["San Francisco"],
    "Washington": ["Washington"],
    "Philadelphie": ["Philadelphie"],
    "City Hall Building": ["City Hall Building"],
    # Other locations / planets
    "Mercure": ["Mercure"],
    "Saturne": ["Saturne"],
    "Aurore": ["Aurore"],
    "Ziggoreth": ["Ziggoreth"],
    "Terra": ["Terra"],
    "Amérique": ["Amérique"],
    "Le Caire": ["Caire"],
    # Places / Institutions
    "Streeling": ["Université de Streeling", "Streeling"],
    "Bibliothèque Galactique": ["Bibliothèque"],
    "Palais Impérial": ["Palais"],
}

# =============================================================================
# FRENCH COMMON WORDS — capitalized words to ignore during heuristic scan
# (sentence starters, common nouns that can appear capitalized, etc.)
# =============================================================================

_FRENCH_COMMON_CAPS = {
    # Common sentence-starting words / false positives
    "Le", "La", "Les", "Un", "Une", "Des", "Du", "De", "Ce", "Ces",
    "Cette", "Il", "Elle", "Ils", "Elles", "On", "Nous", "Vous",
    "Je", "Tu", "Mon", "Ma", "Mes", "Ton", "Ta", "Tes", "Son", "Sa",
    "Ses", "Notre", "Votre", "Leur", "Leurs", "Qui", "Que", "Quoi",
    "Quel", "Quelle", "Quels", "Quelles", "Où", "Comment", "Pourquoi",
    "Quand", "Si", "Mais", "Ou", "Et", "Donc", "Or", "Ni", "Car",
    "Puis", "Alors", "Aussi", "Bien", "Comme", "Dans", "En", "Par",
    "Pour", "Sans", "Sous", "Sur", "Avec", "Vers", "Chez", "Tout",
    "Tous", "Toute", "Toutes", "Autre", "Autres", "Même", "Très",
    "Plus", "Moins", "Peu", "Trop", "Assez", "Encore", "Jamais",
    "Rien", "Personne", "Chaque", "Plusieurs", "Certain", "Certains",
    "Certaine", "Certaines", "Aucun", "Aucune", "Nul", "Nulle",
    "Tel", "Telle", "Tels", "Telles",
    # Common capitalized words that aren't names
    "Chapitre", "Partie", "Livre", "Page", "Note", "Table",
    "Section", "Appendice", "Préface", "Introduction", "Conclusion",
    "Premier", "Première", "Deuxième", "Troisième",
    # Asimov-specific non-name capitalized words
    "Empire", "Galaxie", "Galactique", "Fondation", "Encyclopaedia",
    "Galactica", "Université", "Bibliothèque", "Palais",
    "Mathématicien", "Psychohistoire",
    # Verbs / adjectives that may appear capitalized at sentence start
    "Après", "Avant", "Durant", "Pendant", "Depuis",
    "Cela", "Ceci", "Celui", "Celle", "Ceux", "Celles",
    "Voici", "Voilà", "Oui", "Non", "Peut", "Doit",
    "Faut", "Fait", "Dit", "Bon", "Mal",
    # Days / months (French capitalizes less, but just in case)
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche",
    # Imperative / conjugated verbs commonly appearing capitalized in dialogue
    "Continuez", "Espérons", "Attendez", "Regardez", "Allez", "Venez",
    "Arrêtez", "Écoutez", "Prenez", "Entrez", "Sortez", "Restez",
    "Montrez", "Laissez", "Suivez", "Voyez", "Dites", "Parlez",
    "Permettez", "Pensez", "Croyez", "Savez", "Voulez", "Pouvez",
    "Devez", "Faites", "Donnez", "Tenez", "Allons", "Voyons",
    "Essayez", "Supposez", "Imaginez", "Comprenez", "Excusez",
    "Pardonnez", "Cherchez", "Trouvez", "Passez", "Revenez",
    "Connaissez", "Expliquez", "Racontez", "Appelez", "Asseyez",
    "Répondez", "Demandez", "Reprenez", "Cessez", "Finissez",
    # Common nouns that appear capitalized mid-sentence in Asimov novels
    "Soleil", "Astronef", "Société", "Congés", "Secteur", "Planète",
    "Monde", "Ciel", "Dôme", "Terre", "Science", "Histoire",
    "Docteur", "Monsieur", "Madame", "Mademoiselle", "Seigneur",
    "Majesté", "Excellence", "Altesse", "Maître",
    "Empereur", "Impératrice", "Impérial", "Ministre", "Conseil",
    "Gouverneur", "Gouvernement", "République", "Royaume",
    "Robot", "Robots", "Robotique", "Spacien", "Spaciens",
    "Terrien", "Terriens", "Terrienne", "Extérieur", "Extérieurs",
    # Adjectives / participles that appear capitalized
    "Étouffant", "Fort", "Exact", "Parfait", "Excellent", "Impossible",
    "Naturellement", "Évidemment", "Vraiment", "Absolument",
    "Certainement", "Effectivement", "Probablement", "Simplement",
    "Précisément", "Justement", "Seulement", "Manifestement",
    "Apparemment", "Visiblement", "Heureusement", "Malheureusement",
    # Dialogue exclamations and starters
    "Merci", "Bravo", "Hélas", "Tiens", "Bah", "Hein",
    "Voyons", "Enfin", "Bref", "Toutefois", "Cependant",
    "Néanmoins", "Pourtant", "Autrement", "Finalement",
    "Écoute", "Regarde", "Attends", "Viens", "Sois",
    # Additional common French capitalized false positives
    "Grand", "Petit", "Nouveau", "Nouvelle", "Vieux", "Vieille",
    "Bonne", "Mauvais", "Mauvaise", "Haut", "Bas",
    "Ère", "Siècle", "Temps", "Jour", "Nuit",
    # Asimov demonyms / gentilés (derived from planet names, not character names)
    "Trantorien", "Trantorians", "Trantorien", "Trantoriens",
    "Trantorien", "Trantorians", "Trantorienne", "Trantoriennes",
    "Héliconien", "Héliconiens", "Héliconienne", "Héliconiennes",
    "Auroran", "Aurorain", "Aurorains", "Auroraine", "Auroraines",
    "Solarien", "Solariens", "Solarienne", "Solariennes",
    "Anacreonien", "Anacreoniens",
    "Terminusien", "Terminusiens",
    "Gaïen", "Gaïens", "Gaïenne", "Gaïennes",
    "Kalgannais", "Kalgannaise",
    # Mycogène / Dahl / other sector demonyms
    "Mycogénien", "Mycogéniens", "Mycogénienne", "Mycogéniennes",
    "Dahlite", "Dahlites",
    "Impériaux", "Impérial", "Impériale", "Impériales",
    "Exo", "Exos",
    "Galactos",
    "New Yorkais",
    "Médiévaliste", "Médiévalistes",
    # Asimov-specific capitalized common nouns (not character names)
    "Sciences", "Empereurs", "Universités", "Couverture",
    "Toilettes", "Mondes", "Cité", "Cités",
    "Frère", "Sœur", "Fils", "Filles",
    "Ancien", "Anciens", "Ancienne", "Anciennes",
    "Fraternité", "Loi", "Lois",
    "Médiévale", "Médiévales", "Médiéval",
    "Maîtresse", "Mairie", "Maire",
    "Dieu", "Bible", "Fuite",
    "Ier", "IIe", "IIIe",
    "Controverse", "Machinchose",
    "Strelitzia", "Suaverose",
    "Don", "Quichotte",
    # Biblical / literary figure names (not novel characters)
    "Ahab", "J\u00e9hu", "Naboth", "J\u00e9horam", "Jesreel",
    "J\u00e9hovah", "Baal", "Baalites",
    "Rois",
    "York", "New",
    # Additional common words
    "Gouttes", "Goutte",
    "Billibottains", "Billibottain",
    "Etats", "Junior", "Groupe",
    "Brunswick", "Jersey", "Bronx", "Alleghanis",
    # Additional common French words / terms
    "Caisse", "Congrès", "Déduction", "Guerre", "Traité",
    "Inévitablement", "Ire", "Mère", "Père",
    "Médiévalisme", "Nouveaux", "Nouvelle", "Nouveau",
    "Plastofilm", "Police", "Préfecture",
    "Zoo", "Ville", "Space", "Island",
    "Hall", "Building", "City", "Trinité",
    "Frères", "Sœurs",
    "San", "Buenos", "Aires", "Francisco",
    "Yorkais",
    # Historical / cultural figure names (not novel characters)
    "Shakespeare", "Churchill", "Heisenberg", "Frankenstein",
    "Chester", "Jésus", "Manuel",
}

# Lowercase set for fast membership test
_COMMON_CAPS_LOWER = {w.lower() for w in _FRENCH_COMMON_CAPS}

# =============================================================================
# TITLE PATTERNS for regex-based detection
# =============================================================================

_TITLE_PREFIXES = (
    r"Docteur|Dr\.|Professeur|Prof\.|Monsieur|M\.|Madame|Mme\.?"
    r"|Mademoiselle|Mlle\.?|Capitaine|Colonel|Général|Lieutenant"
    r"|Sergent|Commissaire|Inspecteur|Maître"
)

# Robot naming convention: R. Daneel, R. Giskard
_ROBOT_PATTERN = re.compile(
    r"\bR\.\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)",
    re.UNICODE,
)

# Title + Name pattern
_TITLE_NAME_PATTERN = re.compile(
    rf"\b(?:{_TITLE_PREFIXES})\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)",
    re.UNICODE,
)

# =============================================================================
# UTILITY
# =============================================================================

def normalize_span(text: str) -> str:
    """Strip whitespace and common quotation marks from entity surface form.
    Also collapse internal whitespace (newlines, tabs, multiple spaces)
    into a single space to avoid duplicate entries."""
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned.strip("«»“”\"'")
def _load_characters_file(path: str = "characters.txt") -> list[str]:
    """
    Read characters.txt — one name per line, '#' lines are comments.
    Returns list of non-empty name strings.
    """
    names = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    names.append(line)
    except FileNotFoundError:
        pass
    return names


def _build_word_boundary_re(name: str) -> re.Pattern:
    """
    Build a regex that matches `name` with proper French word boundaries.

    Python's \\b doesn't handle accented chars well, so we use lookaround
    with a custom "word character" class that includes accented letters.
    """
    # Escape the name for regex special chars (handles "R. Daneel" etc.)
    escaped = re.escape(name)
    # Allow flexible whitespace between words
    escaped = re.sub(r"\\ ", r"\\s+", escaped)
    # Use lookaround for word boundaries that work with accented chars
    # A "word char" in French: letters (including accents), digits, underscore
    word_char = r"[a-zA-ZÀ-ÿ0-9_]"
    pattern = rf"(?<!{word_char}){escaped}(?!{word_char})"
    return re.compile(pattern, re.UNICODE)


# =============================================================================
# STRATEGY 1: GAZETTEER LOOKUP
# =============================================================================

def build_gazetteer(character_file: str = "characters.txt",
                    include_locations: bool = False) -> list[tuple[str, str]]:
    """
    Build a gazetteer list of (surface_form, label) pairs.

    Sources:
      - ASIMOV_CHARACTERS (hard-coded)
      - characters.txt file
      - Optionally ASIMOV_LOCATIONS

    Returns sorted longest-first to ensure "Hari Seldon" matches
    before "Hari" or "Seldon".
    """
    entries = {}  # {surface_form: label}

    # 1. Hard-coded Asimov characters: canonical + aliases
    for canonical, aliases in ASIMOV_CHARACTERS.items():
        entries[canonical] = "PER"
        for alias in aliases:
            entries[alias] = "PER"

    # 2. characters.txt file
    for name in _load_characters_file(character_file):
        if name not in entries:
            entries[name] = "PER"

    # 3. Optional: locations
    if include_locations:
        for canonical, aliases in ASIMOV_LOCATIONS.items():
            entries[canonical] = "LOC"
            for alias in aliases:
                entries[alias] = "LOC"

    # Sort longest-first for greedy matching
    sorted_entries = sorted(entries.items(), key=lambda x: len(x[0]), reverse=True)
    return sorted_entries


def _gazetteer_scan(text: str,
                    gazetteer: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Scan text for all gazetteer entries using regex word-boundary matching.
    Returns one (surface_form, label) tuple per occurrence found.

    Uses longest-match-first and marks matched character positions
    to avoid overlapping matches (e.g., "Hari Seldon" won't also
    produce a separate "Hari" match at the same position).
    """
    results = []
    # Track which character positions are already matched
    matched_positions = set()

    for name, label in gazetteer:  # already sorted longest-first
        if len(name) < 2:
            continue

        pattern = _build_word_boundary_re(name)

        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            # Check if any position in this span is already matched
            span_positions = set(range(start, end))
            if span_positions & matched_positions:
                continue  # overlap with a longer match — skip

            matched_positions.update(span_positions)
            surface = normalize_span(match.group())
            if surface:
                results.append((surface, label))

    return results


# =============================================================================
# STRATEGY 2: CAPITALIZATION HEURISTICS
# =============================================================================

# Sentence boundary: punctuation followed by whitespace and uppercase letter
# Also split on paragraph breaks (newline + optional whitespace + uppercase)
_SENTENCE_SPLIT = re.compile(
    r'(?<=[.!?…»"\n])\s*\n\s*(?=[A-ZÀ-Ü])|(?<=[.!?…»"])\s+(?=[A-ZÀ-Ü])',
    re.UNICODE,
)

# Dialogue-opening markers — the word right after these is "sentence-initial"
# and should be skipped by the capitalization heuristic
_DIALOGUE_OPEN = re.compile(
    r'^[«—–\-"]\s*',
    re.UNICODE,
)

# A "capitalized word" in French text (including accented uppercase)
_CAP_WORD = re.compile(
    r"[A-ZÀ-Ü][a-zà-ü]+",
    re.UNICODE,
)


def _build_lowercase_vocabulary(text: str) -> set[str]:
    """
    Build a set of all words that appear in lowercase in the text.

    If a word appears lowercased *anywhere* in the text, it is almost
    certainly not a proper noun when it appears capitalized (it was just
    at a sentence/dialogue start).  e.g. "étouffant" appearing lowercased
    means "Étouffant" is not a name.
    """
    # Extract all lowercase words (2+ chars, allows accents)
    return set(re.findall(r'\b([a-zà-ÿ]{2,})\b', text))


def _capitalization_scan(text: str,
                         anti_dict: set | None = None,
                         known_names: set | None = None) -> list[tuple[str, str]]:
    """
    Detect unknown proper nouns by capitalization heuristics.

    For each sentence, skip the first word (likely capitalized by grammar),
    then find capitalized words that:
      - are not in anti_dict
      - are not in _FRENCH_COMMON_CAPS
      - are not already in the gazetteer (known_names)
      - are longer than 1 character
      - are not ALL CAPS
      - do NOT appear in lowercase form elsewhere in the text

    Consecutive capitalized tokens are grouped into multi-word names
    (e.g., "Alban Wellis" → single entity).
    """
    if anti_dict is None:
        anti_dict = set()
    if known_names is None:
        known_names = set()

    known_lower = {n.lower() for n in known_names}

    # KEY HEURISTIC: build vocabulary of words that appear lowercased in text.
    # If "étouffant" exists in lowercase, then "Étouffant" is not a name.
    lowercase_vocab = _build_lowercase_vocabulary(text)

    results = []

    # Split into rough sentences
    sentences = _SENTENCE_SPLIT.split(text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if sentence starts with a dialogue marker (« — – -)
        # If so, strip the marker and also skip the first real word
        dialogue_match = _DIALOGUE_OPEN.match(sentence)
        if dialogue_match:
            sentence = sentence[dialogue_match.end():]

        # Tokenize: split on whitespace, keeping punctuation attached
        tokens = sentence.split()
        if not tokens:
            continue

        # Find capitalized tokens (skip index 0 — sentence-initial)
        i = 1
        while i < len(tokens):
            token = tokens[i]
            # Clean trailing punctuation for checking
            clean = token.rstrip(".,;:!?»\"')")
            clean = clean.lstrip("«\"'(")

            # Also skip tokens right after inline dialogue markers
            if i > 0 and tokens[i-1].rstrip() in (':', '«', '—', '–', '"'):
                i += 1
                continue

            if (_CAP_WORD.fullmatch(clean)
                    and clean.lower() not in _COMMON_CAPS_LOWER
                    and clean.lower() not in anti_dict
                    and clean.lower() not in lowercase_vocab
                    and clean.lower() not in known_lower
                    and not clean.isupper()):

                # Start collecting a multi-word capitalized name
                name_parts = [clean]
                j = i + 1
                while j < len(tokens):
                    next_token = tokens[j]
                    next_clean = next_token.rstrip(".,;:!?»\"')")
                    next_clean = next_clean.lstrip("«\"'(")
                    if (_CAP_WORD.fullmatch(next_clean)
                            and next_clean.lower() not in _COMMON_CAPS_LOWER
                            and next_clean.lower() not in anti_dict
                            and next_clean.lower() not in lowercase_vocab
                            and next_clean.lower() not in known_lower
                            and not next_clean.isupper()):
                        name_parts.append(next_clean)
                        j += 1
                    else:
                        break

                full_name = " ".join(name_parts)
                # Only add if not already covered by gazetteer
                if full_name.lower() not in known_lower:
                    results.append((full_name, "PER"))
                    # Also add individual parts if multi-word
                    # (for alias grouping downstream to work)
                    if len(name_parts) > 1:
                        for part in name_parts:
                            if (part.lower() not in known_lower
                                    and len(part) > 1):
                                results.append((part, "PER"))

                i = j  # skip past the grouped tokens
            else:
                i += 1

    return results


# =============================================================================
# STRATEGY 3: REGEX PATTERNS (titled names, robot names)
# =============================================================================

def _title_regex_scan(text: str) -> list[tuple[str, str]]:
    """
    Detect names preceded by French titles (Docteur, M., Lieutenant, etc.)
    and robot-convention names (R. Daneel).

    Returns the name part only (without the title) as PER.
    """
    results = []

    # Title + Name → extract name
    for match in _TITLE_NAME_PATTERN.finditer(text):
        name = normalize_span(match.group(1))
        if name and len(name) > 1:
            results.append((name, "PER"))

    # R. Name (robot convention)
    for match in _ROBOT_PATTERN.finditer(text):
        # Return "R. Name" as the full surface form
        full = normalize_span(match.group(0))
        name_part = normalize_span(match.group(1))
        if full and len(name_part) > 1:
            results.append((f"R. {name_part}", "PER"))

    return results


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def manual_extract_entities(text: str,
                            character_file: str = "characters.txt",
                            anti_dict: set | None = None,
                            include_locations: bool = False
                            ) -> list[tuple[str, str]]:
    """
    Rule-based NER — no AI models.

    Combines three strategies:
      1. Gazetteer lookup (known Asimov character names)
      2. Capitalization heuristics (unknown proper nouns mid-sentence)
      3. Regex patterns (titled names, robot convention)

    Parameters
    ----------
    text : str
        The chapter text to process.
    character_file : str
        Path to characters.txt gazetteer file.
    anti_dict : set or None
        Set of lowercase stopwords to exclude from heuristic matches.
    include_locations : bool
        If True, also detect locations from ASIMOV_LOCATIONS.

    Returns
    -------
    list[tuple[str, str]]
        List of (surface_form, label) tuples — same format as
        ensemble_entities() for full compatibility with downstream code.
    """
    # Build gazetteer
    gazetteer = build_gazetteer(character_file, include_locations=include_locations)
    known_names = {name for name, _label in gazetteer}

    # Strategy 1: Gazetteer scan
    gaz_results = _gazetteer_scan(text, gazetteer)

    # Strategy 3: Regex (titled names / robot names)
    regex_results = _title_regex_scan(text)

    # Strategy 2: Capitalization heuristics (use known names to avoid duplicates)
    # Add names found by regex to known set for deduplication
    regex_names = {name for name, _label in regex_results}
    all_known = known_names | regex_names
    cap_results = _capitalization_scan(text, anti_dict=anti_dict, known_names=all_known)

    # Combine all results
    all_entities = gaz_results + regex_results + cap_results

    return all_entities

"""
nlp_manual_ner.py — Rule-based NER for novels (no AI models).

Three strategies combined:
  1. Gazetteer lookup (characters.txt + optional hard-coded names)
  2. Capitalization heuristics (unknown proper nouns mid-sentence)
  3. Regex patterns (titled names: Docteur X, R. Name, etc.)

Output format: list[tuple[str, str]]  — identical to ensemble_entities()
so all downstream code (count_entities, filter_persons, aliases, etc.)
works unchanged.

To use with a different book, provide your own characters.txt and/or
gazetteer dictionaries via the gazetteer_characters and gazetteer_locations
parameters to manual_extract_entities().
"""

import re
from collections import Counter
from pathlib import Path

MIN_CAP_FREQ = 2  # Minimum occurrences to keep a capitalization-heuristic name

# =============================================================================
# DEFAULT GAZETTEER — Asimov novels (can be overridden via parameters)
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

# Capitalization false positives are maintained in antidict.txt and merged
# into anti_dict at runtime.

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
                    include_locations: bool = False,
                    gazetteer_characters: dict[str, list[str]] | None = None,
                    gazetteer_locations: dict[str, list[str]] | None = None,
                    ) -> list[tuple[str, str]]:
    """
    Build a gazetteer list of (surface_form, label) pairs.

    Sources (merged in order):
      - gazetteer_characters parameter (if provided, overrides ASIMOV_CHARACTERS)
      - characters.txt file
      - gazetteer_locations parameter (if provided, overrides ASIMOV_LOCATIONS)

    Parameters
    ----------
    character_file : str
        Path to characters.txt gazetteer file.
    include_locations : bool
        If True, also include locations.
    gazetteer_characters : dict or None
        Custom character dictionary {canonical: [aliases, ...]}.
        If None, uses ASIMOV_CHARACTERS.
    gazetteer_locations : dict or None
        Custom location dictionary {canonical: [aliases, ...]}.
        If None and include_locations is True, uses ASIMOV_LOCATIONS.

    Returns sorted longest-first to ensure "Hari Seldon" matches
    before "Hari" or "Seldon".
    """
    entries = {}  # {surface_form: label}

    # 1. Character gazetteer (custom or default)
    char_dict = gazetteer_characters if gazetteer_characters is not None else ASIMOV_CHARACTERS
    for canonical, aliases in char_dict.items():
        entries[canonical] = "PER"
        for alias in aliases:
            entries[alias] = "PER"

    # 2. characters.txt file
    for name in _load_characters_file(character_file):
        if name not in entries:
            entries[name] = "PER"

    # 3. Optional: locations (custom or default)
    if include_locations:
        loc_dict = gazetteer_locations if gazetteer_locations is not None else ASIMOV_LOCATIONS
        for canonical, aliases in loc_dict.items():
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

def _title_regex_scan(text: str,
                      title_prefixes: str | None = None,
                      enable_robot_pattern: bool = True) -> list[tuple[str, str]]:
    """
    Detect names preceded by titles (Docteur, M., Lieutenant, etc.)
    and robot-convention names (R. Daneel).

    Parameters
    ----------
    text : str
        The text to scan.
    title_prefixes : str or None
        Custom regex alternation for title prefixes.
        If None, uses the default French _TITLE_PREFIXES.
    enable_robot_pattern : bool
        If True, also match "R. Name" robot convention.

    Returns the name part only (without the title) as PER.
    """
    results = []

    # Build regex patterns with custom or default prefixes
    prefixes = title_prefixes if title_prefixes is not None else _TITLE_PREFIXES

    title_name_re = re.compile(
        rf"\b(?:{prefixes})\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)",
        re.UNICODE,
    )

    # Title + Name → extract name
    for match in title_name_re.finditer(text):
        name = normalize_span(match.group(1))
        if name and len(name) > 1:
            results.append((name, "PER"))

    # R. Name (robot convention)
    if enable_robot_pattern:
        for match in _ROBOT_PATTERN.finditer(text):
            # Return "R. Name" as the full surface form
            full = normalize_span(match.group(0))
            name_part = normalize_span(match.group(1))
            if full and len(name_part) > 1:
                results.append((f"R. {name_part}", "PER"))

    return results


# =============================================================================
# DYNAMIC BLOCKLIST GENERATOR
# =============================================================================

def precompute_dynamic_blocklist(texts: list[str],
                                 cap_ratio_threshold: float = 0.70,
                                 min_count: int = 5,
                                 gazetteer_characters: dict[str, list[str]] | None = None,
                                 gazetteer_locations: dict[str, list[str]] | None = None,
                                 ) -> set:
    """
    Identifies common capitalized non-names automatically from the corpus.
    Builds a list of words where the capitalization ratio is >= cap_ratio_threshold
    and total occurrences >= min_count.
    Excludes known names from the provided gazetteers (or defaults).

    Parameters
    ----------
    texts : list[str]
        List of text passages to analyze.
    cap_ratio_threshold : float
        Minimum ratio of capitalized occurrences to total.
    min_count : int
        Minimum total occurrences to consider.
    gazetteer_characters : dict or None
        Custom character gazetteer. If None, uses ASIMOV_CHARACTERS.
    gazetteer_locations : dict or None
        Custom location gazetteer. If None, uses ASIMOV_LOCATIONS.
    """
    cap_counts = Counter()
    lower_counts = Counter()

    # Tokenize words using basic regex
    word_pattern = re.compile(r'\b[A-Za-zÀ-ÿ]+\b')
    for text in texts:
        for match in word_pattern.finditer(text):
            word = match.group()
            if word.istitle():
                cap_counts[word.lower()] += 1
            elif word.islower():
                lower_counts[word.lower()] += 1

    # Gather known gazetteer words to exclude (canonical names + aliases).
    known_names = set()
    gazetteer_forms = []
    char_dict = gazetteer_characters if gazetteer_characters is not None else ASIMOV_CHARACTERS
    loc_dict = gazetteer_locations if gazetteer_locations is not None else ASIMOV_LOCATIONS

    for canonical, aliases in char_dict.items():
        gazetteer_forms.append(canonical)
        gazetteer_forms.extend(aliases)
    for canonical, aliases in loc_dict.items():
        gazetteer_forms.append(canonical)
        gazetteer_forms.extend(aliases)

    for form in gazetteer_forms:
        for token in re.findall(r"\b[A-Za-zÀ-ÿ]+\b", form.lower()):
            known_names.add(token)

    blocklist = set()
    for word in set(cap_counts.keys()).union(lower_counts.keys()):
        if word in known_names:
            continue

        total = cap_counts[word] + lower_counts[word]
        if total >= min_count and (cap_counts[word] / total) >= cap_ratio_threshold:
            blocklist.add(word)

    return blocklist

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def manual_extract_entities(text: str,
                            character_file: str = "characters.txt",
                            anti_dict: set | None = None,
                            include_locations: bool = False,
                            dynamic_blocklist: set | None = None,
                            gazetteer_characters: dict[str, list[str]] | None = None,
                            gazetteer_locations: dict[str, list[str]] | None = None,
                            title_prefixes: str | None = None,
                            enable_robot_pattern: bool = True,
                            ) -> list[tuple[str, str]]:
    """
    Rule-based NER — no AI models.

    Combines three strategies:
      1. Gazetteer lookup (known character names)
      2. Capitalization heuristics (unknown proper nouns mid-sentence)
         Filters out heuristic-only names that do not appear at least
         MIN_CAP_FREQ times, ensuring a cleaner baseline.
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
        If True, also detect locations from gazetteer.
    dynamic_blocklist : set or None
        Set of dynamic stopwords correctly identified from the corpus.
    gazetteer_characters : dict or None
        Custom character gazetteer {canonical: [aliases, ...]}.
        If None, uses the default ASIMOV_CHARACTERS.
    gazetteer_locations : dict or None
        Custom location gazetteer {canonical: [aliases, ...]}.
        If None and include_locations is True, uses default ASIMOV_LOCATIONS.
    title_prefixes : str or None
        Custom regex pattern for title prefixes (e.g., "Docteur|Dr\\.|Professeur").
        If None, uses the default French titles.
    enable_robot_pattern : bool
        If True, also match robot naming convention "R. Name".
        Set to False for non-Asimov texts.

    Returns
    -------
    list[tuple[str, str]]
        List of (surface_form, label) tuples — same format as
        ensemble_entities() for full compatibility with downstream code.
    """
    if dynamic_blocklist:
        if anti_dict is None:
            anti_dict = set()
        else:
            anti_dict = set(anti_dict)
        anti_dict.update({w.lower() for w in dynamic_blocklist})

    # Build gazetteer (custom or default)
    gazetteer = build_gazetteer(
        character_file,
        include_locations=include_locations,
        gazetteer_characters=gazetteer_characters,
        gazetteer_locations=gazetteer_locations,
    )
    known_names = {name for name, _label in gazetteer}

    # Strategy 1: Gazetteer scan
    gaz_results = _gazetteer_scan(text, gazetteer)

    # Strategy 3: Regex (titled names / robot names)
    regex_results = _title_regex_scan(
        text,
        title_prefixes=title_prefixes,
        enable_robot_pattern=enable_robot_pattern,
    )

    # Strategy 2: Capitalization heuristics (use known names to avoid duplicates)
    # Add names found by regex to known set for deduplication
    regex_names = {name for name, _label in regex_results}
    all_known = known_names | regex_names

    cap_results = _capitalization_scan(text, anti_dict=anti_dict, known_names=all_known)

    # Filter out purely heuristic names that do not appear MIN_CAP_FREQ times
    cap_counts = Counter(name for name, _ in cap_results)
    cap_results = [(name, label) for name, label in cap_results
                   if cap_counts[name] >= MIN_CAP_FREQ]

    # Combine all results
    all_entities = gaz_results + regex_results + cap_results

    return all_entities

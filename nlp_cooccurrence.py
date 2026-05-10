import re
from collections import Counter
from itertools import combinations
from bisect import bisect_left

def detect_cooccurrences(text, character_counts, distance_max=25):
    """
    Detect co-occurrences between characters within a distance window.

    Args:
        text (str): Full text to analyze
        character_counts (Counter): Counter of character names
        distance_max (int): Window size in words

    Returns:
        Counter: Co-occurrence pairs with counts
    """

    # --- normalize & tokenize ---
    tokens = re.findall(r"\w+", text.lower())

    # --- normalize character names but keep mapping to original ---
    # supports multi-word names
    # IMPORTANT: Tokenize character names the same way as text (using \w+)
    lowercase_to_original = {}  # maps tokenized lowercase name to original name
    char_names_lower = []
    
    for name in character_counts.keys():
        name_lower = name.lower()
        # Tokenize the same way as the text to handle apostrophes correctly
        name_tokens = re.findall(r"\w+", name_lower)
        char_names_lower.append(name_tokens)
        # Map the space-joined tokenized form to original
        lowercase_to_original[" ".join(name_tokens)] = name

    # --- find positions of each character name ---
    char_positions = {}

    for name_tokens in char_names_lower:
        name_len = len(name_tokens)
        name_str = " ".join(name_tokens)
        positions = []

        for i in range(len(tokens) - name_len + 1):
            if tokens[i:i+name_len] == name_tokens:
                positions.append(i)

        char_positions[name_str] = positions

    # Sort positions for binary search optimization
    for char in char_positions:
        char_positions[char].sort()

    # --- sliding window co-occurrence ---
    cooccurrences = Counter()

    for i in range(len(tokens)):
        window_start = i
        window_end = i + distance_max

        present_chars = []

        for char, positions in char_positions.items():
            # Use binary search (bisect) to quickly check if any position falls within the window.
            # This changes lookup from O(N) to O(log N) where N is number of occurrences.
            idx = bisect_left(positions, window_start)
            if idx < len(positions) and positions[idx] <= window_end:
                present_chars.append(char)

        # count all pairs inside window
        # Convert back to original case before storing
        for a, b in combinations(sorted(set(present_chars)), 2):
            original_a = lowercase_to_original[a]
            original_b = lowercase_to_original[b]
            pair = tuple(sorted([original_a, original_b]))
            cooccurrences[pair] += 1

    return cooccurrences

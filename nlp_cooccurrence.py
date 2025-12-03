from collections import Counter

def detect_cooccurrences(text, character_counts, distance_max=25):
    """
    Detect co-occurrences between characters within a distance window.
    
    Args:
        text (str): Full text to analyze
        character_counts (Counter): Counter of character names
        distance_max (int): Maximum word distance for co-occurrence
    
    Returns:
        Counter: Co-occurrence pairs with counts
    """
    # Get list of characters
    characters = list(character_counts.keys())
    
    # Tokenize text
    tokens = text.split()
    
    cooccurrences = Counter()
    
    # For each character pair
    for i, char1 in enumerate(characters):
        for char2 in characters[i+1:]:  # Avoid duplicates
            # Find positions of char1 in text
            indices1 = [idx for idx, token in enumerate(tokens) 
                       if char1.lower() in token.lower()]
            
            # Find positions of char2 in text
            indices2 = [idx for idx, token in enumerate(tokens) 
                       if char2.lower() in token.lower()]
            
            # Check if they appear within distance_max
            for idx1 in indices1:
                for idx2 in indices2:
                    if abs(idx1 - idx2) <= distance_max:
                        # Use sorted tuple to ensure consistency
                        pair = tuple(sorted([char1, char2]))
                        cooccurrences[pair] += 1
                        break  # Count once per proximity instance
    
    return cooccurrences
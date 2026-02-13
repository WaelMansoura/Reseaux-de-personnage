#!/usr/bin/env python3
"""
Test script to demonstrate EntityRuler usage in nlp_multi_ner.py
"""

from nlp_multi_ner import extract_spacy, ensemble_entities, spacy_nlp

# Example text from Foundation
test_text = """
Golan Trevize regardait Janov Pelorat avec inquiétude. 
Hari Seldon avait prédit la chute de l'Empire. 
Salvor Hardin, le maire de Terminus, était un homme astucieux.
Bayta et Toran discutaient avec Ebling Mis de la Seconde Fondation.
"""

print("=" * 70)
print("DEMONSTRATION: EntityRuler in Action")
print("=" * 70)

# Method 1: Using extract_spacy (already uses EntityRuler)
print("\n[1] Using extract_spacy() - EntityRuler is AUTOMATICALLY active:")
print("-" * 70)
entities_spacy = extract_spacy(test_text)
for entity, label in entities_spacy:
    print(f"  {entity:25} → {label}")

# Method 2: Using ensemble (combines spacy + stanza)
print("\n[2] Using ensemble_entities() - EntityRuler enhances spacy side:")
print("-" * 70)
entities_ensemble = ensemble_entities(test_text, method="union")
for entity, label in entities_ensemble:
    print(f"  {entity:25} → {label}")

# Method 3: Direct spacy_nlp usage
print("\n[3] Direct usage with spacy_nlp object:")
print("-" * 70)
doc = spacy_nlp(test_text)
for ent in doc.ents:
    print(f"  {ent.text:25} → {ent.label_:8} (start: {ent.start_char}, end: {ent.end_char})")

# Method 4: Testing with a specific character
print("\n[4] Testing specific character recognition:")
print("-" * 70)
test_specific = "R. Daneel Olivaw accompagnait Fallom sur Terre."
doc = spacy_nlp(test_specific)
print(f"Text: {test_specific}")
print(f"Found entities: {[(ent.text, ent.label_) for ent in doc.ents]}")

print("\n" + "=" * 70)
print("EntityRuler is working! 🎉")
print("=" * 70)

# FinalProject — Extraction de réseau de personnages

Pipeline d'extraction de personnages et de relations à partir de textes français (corpus Asimov). Sortie : graphe interactif HTML par chapitre + graphe global agrégé.

## Pipeline

1. **Extraction de personnages** — NER manuel basé règles + gazetteer (`nlp_manual_ner.py`, `nlp_extract_characters.py`).
2. **Résolution d'alias** — regroupement des surfaces vers une forme canonique (`nlp_aliases.py`).
3. **Détection de co-occurrences** — fenêtre glissante de tokens (`nlp_cooccurrence.py`).
4. **Étiquetage de relations** — sentiment XLM-RoBERTa multilingue → friendly/hostile/neutral (`nlp_relation.py`).
5. **Construction du graphe** — agrégation NetworkX (`nlp_graph.py`).
6. **Visualisation web** — export PyVis HTML interactif (`nlp_visualize_web.py`).

Orchestration : [`main`](main).

## Documentation des modules

- [nlp_extract_characters](docs/nlp_extract_characters.md) — extraction d'entités
- [nlp_manual_ner](docs/nlp_manual_ner.md) — NER manuel + gazetteer
- [nlp_aliases](docs/nlp_aliases.md) — résolution d'alias
- [nlp_cooccurrence](docs/nlp_cooccurrence.md) — détection de co-occurrences
- [nlp_relation](docs/nlp_relation.md) — étiquetage par sentiment
- [nlp_graph](docs/nlp_graph.md) — construction du graphe
- [nlp_visualize_web](docs/nlp_visualize_web.md) — visualisation HTML

## Données

- `data/` — chapitres prétraités (`chapter_{n}.txt.preprocessed`)
- `characters.txt` — gazetteer canoniques
- `antidict.txt` — blocklist mots capitalisés non-personnages

## Exécution

Ouvrir `main`. Premier run télécharge `cardiffnlp/twitter-xlm-roberta-base-sentiment` (~500 Mo). Caches persistés sur disque (`ner_cache3.pkl`, `relation_cache.pkl`).

Sortie finale : `all_networks.html`.

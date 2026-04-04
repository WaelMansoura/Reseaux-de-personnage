# Rapport d'Avancement — Semestre 2

**Date** : Mars 2026  
**Projet** : Extraction de réseaux de personnages à partir de textes narratifs  
**Étudiants** : Lotfi ABDALLAH, Wael MANSOURA  
**Formation** : Master 1 Informatique, parcours ILSEN  
**Université** : Université d'Avignon  
**Année universitaire** : 2025-2026

---

## Table des matières

1. [Rappel du contexte](#1-rappel-du-contexte)
2. [État d'avancement — Tableau de suivi des exigences](#2-état-davancement--tableau-de-suivi-des-exigences)
3. [Travaux réalisés au semestre 2](#3-travaux-réalisés-au-semestre-2)
4. [Indicateurs de performance](#4-indicateurs-de-performance-kpis)
5. [Préparation de la campagne d'expérimentation (avril)](#5-préparation-de-la-campagne-dexpérimentation-avril)
6. [Anticipation du rapport final (>12 mai)](#6-anticipation-du-rapport-final-12-mai)
7. [Répartition des tâches](#7-répartition-des-tâches)

---

## 1. Rappel du contexte

### Projet

Le projet consiste à extraire automatiquement des réseaux de personnages à partir de deux romans d'Isaac Asimov traduits en français :

- _Prélude à Fondation_ (19 chapitres: paf0–paf18)
- _Les Cavernes d'Aciel_ (18 chapitres: lca0–lca17)

**Total** : 37 chapitres traités.

Le pipeline extrait les entités nommées (personnages), regroupe leurs alias, détecte les co-occurrences par fenêtre glissante, et construit un graphe de personnages au format GraphML pour chaque chapitre. Les résultats sont soumis dans le cadre d'une compétition Kaggle.

### Bilan du semestre 1 (terminé)

Le S1 a livré un pipeline fonctionnel de bout en bout :

- Extraction NER multi-modèles (spaCy + Stanza, vote majoritaire)
- Filtrage des personnages (LP) et des lieux (LL) avec anti-dictionnaire
- Regroupement d'alias (Union-Find + similarité floue)
- Détection des co-occurrences (fenêtre glissante configurable)
- Génération de graphes NetworkX + export GraphML/CSV
- Soumission Kaggle fonctionnelle

### Objectif du semestre 2

**Étiquetage des relations entre les personnages** : enrichir chaque arête du graphe avec un type de relation (_friendly_, _hostile_, _neutral_) afin de qualifier la nature des interactions au-delà de la simple co-occurrence.

---

## 2. État d'avancement — Tableau de suivi des exigences

### Exigences du cahier des charges (S1)

| #   | Exigence                               | Priorité | Responsable | Statut     | Commentaire                                     |
| --- | -------------------------------------- | -------- | ----------- | ---------- | ----------------------------------------------- |
| 1   | Extraction des entités nommées (NER)   | Haute    | Lotfi       | ✅ Terminé | Multi-modèles (spaCy + Stanza) + NER rule-based |
| 2   | Filtrage des personnes (liste LP)      | Haute    | Lotfi       | ✅ Terminé | Anti-dictionnaire (~868 entrées)                |
| 3   | Filtrage des lieux (liste LL)          | Moyenne  | Lotfi       | ✅ Terminé | Inclut gazetteer Asimov                         |
| 4   | Regroupement des alias                 | Haute    | Lotfi       | ✅ Terminé | Union-Find + fuzzy matching + overrides manuels |
| 5   | Détection des co-occurrences           | Haute    | Wael        | ✅ Terminé | Fenêtre glissante (distance_max=150)            |
| 6   | Génération du graphe NetworkX          | Haute    | Wael        | ✅ Terminé | Attributs : count, names, weight                |
| 7   | Visualisation du réseau de personnages | Moyenne  | Wael        | ✅ Terminé | HTML interactif (PyVis/vis.js)                  |
| 8   | Export CSV pour soumission Kaggle      | Haute    | Lotfi, Wael | ✅ Terminé | 37 chapitres, GraphML complet                   |

### Exigences supplémentaires du semestre 2

| #   | Exigence                                            | Priorité | Responsable  | Statut          | Commentaire                                                |
| --- | --------------------------------------------------- | -------- | ------------ | --------------- | ---------------------------------------------------------- |
| 9   | Étiquetage des relations (friendly/hostile/neutral) | Haute    | Lotfi + Wael | ✅ Terminé      | NLI zero-shot (mDeBERTa-v3-base-mnli-xnli)                 |
| 10  | Cache des labels de relations                       | Haute    | Lotfi + Wael | ✅ Terminé      | Pickle, clé (chapter_id, charA, charB)                     |
| 11  | Visualisation colorée des arêtes                    | Moyenne  | Wael         | ✅ Terminé      | edge_type + Vert/rouge/gris + HTML combiné multi-chapitres |
| 12  | Rapport de validation (spot-check)                  | Moyenne  | Lotfi + Wael | ✅ Terminé      | `print_validation_report()`                                |
| 13  | NER rule-based (sans modèles IA)                    | Basse    | Lotfi        | ✅ Terminé      | Alternative légère : gazetteer + heuristiques              |
| 14  | Campagne d'expérimentation                          | Haute    | Lotfi + Wael | 🔄 En cours     | Plan défini, exécution prévue en avril                     |
| 15  | Rédaction du rapport final (article en anglais)     | Haute    | Lotfi + Wael | ⬜ Non commencé | Prévu pour avril–mai                                       |

---

## 3. Travaux réalisés au semestre 2

### 3.1 Étiquetage des relations `nlp_relation.py` (nouveau)

**Objectif** : Pour chaque paire de personnages co-occurrents dans un chapitre, attribuer un label de relation parmi `friendly`, `hostile`, ou `neutral`.

**Approche retenue** : Classification zero-shot par Natural Language Inference (NLI).

```
                    Texte du chapitre
                           │
      ┌────────────────────┼────────────────────┐
      │      Pour chaque paire (charA, charB)     │
      │                    │                      │
      │    extract_cooccurrence_contexts()        │
      │    → jusqu'à 5 extraits textuels          │
      │                    │                      │
      │    classify_relationship()                │
      │    → NLI zero-shot sur chaque extrait     │
      │    → vote pondéré par confiance           │
      │                    │                      │
      │    Si confiance < 0.55 → "neutral"        │
      │    Sinon → label gagnant                  │
      └────────────────────┼────────────────────┘
                           │
              dict{(charA, charB): label}
```

**Modèle NLI** : `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` (~350 Mo)

| Critère                 | Justification                                         |
| ----------------------- | ----------------------------------------------------- |
| Pas de données annotées | Le modèle fonctionne en zero-shot                     |
| Support du français     | Entraîné sur XNLI multilingue, performant en français |
| Compatible CPU          | ~1–3 s/extrait sur Colab gratuit                      |
| Déterministe            | Inférence greedy + cache = résultats reproductibles   |
| Simple d'utilisation    | 5 lignes via HuggingFace `pipeline()`                 |

**Approches rejetées** :

- _Analyse de sentiment_ : le sentiment ≠ la relation ; la prose d'Asimov est souvent expositoire, conduisant à de faux « neutres »
- _Règles syntaxiques_ : bonne précision mais rappel quasi-nul sur du texte littéraire
- _Transformer fine-tuné_ : nécessite des données annotées que nous n'avons pas
- _LLM local (GGUF)_ : trop lent sur CPU Colab ; réservé comme voie d'escalade

**Hypothèses NLI** (en français) :

1. « ces deux personnages ont une relation amicale » → `friendly`
2. « ces deux personnages ont une relation hostile » → `hostile`
3. « ces deux personnages ont une relation neutre » → `neutral`

**Stratégie de cache** :

- Clé : `(chapter_id, canonA, canonB)` avec canonA < canonB (trié)
- Fichier : `relation_cache.pkl` (pickle)
- Invalidation : uniquement si changement du modèle NLI ou du seuil de confiance

### 3.2 NER rule-based `nlp_manual_ner.py` (nouveau)

Alternative au NER multi-modèles (S1), fonctionnant **sans aucun modèle IA** :

1. **Gazetteer** : dictionnaires en dur des personnages et lieux des deux romans d'Asimov (correspondance la plus longue d'abord, non chevauchante)
2. **Heuristiques de capitalisation** : mots capitalisés en milieu de phrase, absents d'une liste noire de ~200 mots courants français, non trouvés en minuscule ailleurs dans le texte
3. **Patterns regex** : « Docteur X », « R. Daneel » (convention de nommage des robots), préfixes de titres

**Avantage** : exécution quasi-instantanée (pas de téléchargement de modèle), utile pour le développement itératif rapide.

### 3.3 Modifications de `nlp_graph.py`

- Ajout du paramètre `edge_labels` à `generate_graph()`
- Écriture de l'attribut `edge_type` sur chaque arête du graphe NetworkX
- L'attribut `edge_type` apparaît automatiquement dans la sortie GraphML (devient un champ `<data>` standard)
- Ajout du reverse alias map pour l'attribut `names` des nœuds

### 3.4 Visualisation enrichie — `nlp_visualize_web.py`

**Arêtes colorées par type de relation** :

- 🟢 Vert → friendly
- 🔴 Rouge → hostile
- ⚫ Gris → neutral

**Nouvelle fonction `create_combined_html()`** — génère un **seul fichier HTML :** (_all_networks.html_) contenant les 37 chapitres :

- Barre de navigation par livre et par chapitre
- Barre horizontale affichant le nombre de noeuds et arêtes pour chaque chapitre
- Infobulles au survol : poids de co-occurrence + type de relation
- Légende visuelle (points colorés) dans la barre horizontale
- Le fichier HTML peut être trouvé avec le reste des livrables code.

### 3.5 Notebook intégrateur — `nomodels.ipynb`

Notebook complet orchestrant le pipeline de bout en bout avec la NER rule-based :

| Section               | Contenu                                                 | Vitesse             |
| --------------------- | ------------------------------------------------------- | ------------------- |
| 1. Setup              | Imports, rechargement des modules                       | Instantané          |
| 2. Configuration      | `books_config`, anti-dictionnaire                       | Instantané          |
| 3. Extraction NER     | NER rule-based sur 37 chapitres                         | Rapide (secondes)   |
| 3.1 Cache NER         | Sauvegarde/chargement pickle (Google Drive)             | Instantané          |
| 4. Relation cache     | Chargement `relation_cache.pkl`                         | Instantané          |
| 4.1 Boucle principale | Co-occurrences + `label_relationships()` + graphe + CSV | Heures (modèle NLI) |
| 4.2 Cache relations   | Sauvegarde du cache de relations mis à jour             | Instantané          |
| 5. Vérification       | Aperçu de la soumission + `print_validation_report()`   | Instantané          |
| 6. Test fenêtres      | Comparaison distance_max = [25, 50, 75, 100, 150]       | Secondes            |
| 7. Visualisation HTML | Fichier HTML combiné multi-chapitres interactif         | Secondes            |

### 3.6 Pipeline complet (S1 + S2)

```
chapter_N.txt.preprocessed
        │
        ▼  manual_extract_entities()          [nlp_manual_ner.py]
           Gazetteer + heuristiques capitalisation + regex
        │
        ▼  count_entities() → filter_persons() [nlp_extract_characters.py]
           L (toutes entités) → LP (personnes, filtré par anti-dict)
        │
        ▼  group_aliases() → alias_dictionary() → apply_manual_aliases()
           [nlp_aliases.py] — Union-Find + fuzzy matching + overrides manuels
        │
        ▼  merge_alias_counts() → filter_by_frequency(min_occ=2)
           LP_merged : {nom_canonique: nombre_mentions}
        │
        ▼  detect_cooccurrences(text, LP_merged, distance_max=150)
           [nlp_cooccurrence.py] — fenêtre glissante
           Counter{(charA, charB): nombre_fenêtres}
        │
        ▼  label_relationships(text, cooccurrences, alias_map, cache)   ← NOUVEAU S2
           [nlp_relation.py] — classification NLI zero-shot
           dict{(charA, charB): "friendly"|"hostile"|"neutral"}
        │
        ▼  generate_graph(cooccurrences, LP_merged, alias_map, edge_labels)
           [nlp_graph.py] — nx.Graph avec attribut edge_type
        │
        ▼  remove_isolated_nodes(G) → nx.generate_graphml(G)
           → submission.csv + visualisation HTML combinée
```

---

## 4. Indicateurs de performance (KPIs)

### Couverture du corpus

| Indicateur                   | Valeur                                               |
| ---------------------------- | ---------------------------------------------------- |
| Chapitres traités            | **37/37** (100 %)                                    |
| Livres couverts              | 2/2 (_Prélude à Fondation_ + _Les Cavernes d'Acier_) |
| Nœuds typiques par chapitre  | 5–20                                                 |
| Arêtes typiques par chapitre | 5–30                                                 |

### Paramètres du système

| Paramètre               | Valeur   | Rôle                                                   |
| ----------------------- | -------- | ------------------------------------------------------ |
| `distance_max`          | 150 mots | Taille de la fenêtre de co-occurrence                  |
| `min_occurrences`       | 2        | Seuil minimal de mentions pour conserver un personnage |
| `CONFIDENCE_THRESHOLD`  | 0.55     | Seuil de confiance NLI (en dessous → neutral)          |
| `MAX_CONTEXTS_PER_PAIR` | 5        | Nombre max d'extraits analysés par paire               |
| `MAX_SNIPPET_CHARS`     | 400      | Longueur max des extraits envoyés au modèle            |

### Modèle NLI

| Indicateur        | Valeur                                    |
| ----------------- | ----------------------------------------- |
| Modèle            | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` |
| Taille            | ~350 Mo                                   |
| Taxonomie         | 3 classes (friendly / hostile / neutral)  |
| Exécution         | CPU uniquement (Google Colab gratuit)     |
| Temps par extrait | ~1–3 secondes                             |

### Distribution attendue des labels

> **Note Asimov** : Les chapitres d'Asimov sont souvent expositoires ou philosophiques — de longs passages où les personnages débattent de mathématiques, politique ou sociologie sans vocabulaire émotif. Une proportion élevée de labels `neutral` est attendue, même pour des paires ayant une relation établie dans d'autres chapitres. Ce n'est pas un défaut du système, mais le reflet du fait que _le chapitre en question_ ne contient pas suffisamment de signaux d'interaction.

### Performance technique

| Indicateur                                                  | Valeur                                                |
| ----------------------------------------------------------- | ----------------------------------------------------- |
| Temps d'extraction NER (37 chapitres, rule-based)           | ~quelques secondes                                    |
| Temps de la boucle principale (NER + co-occ + NLI + graphe) | ~quelques heures (Google Colab CPU)                   |
| Taille du cache de relations                                | Variable (croît avec le nombre de paires classifiées) |
| Exécution reproductible                                     | Oui (inférence greedy + cache pickle)                 |

---

## 5. Préparation de la campagne d'expérimentation (avril)

La campagne d'expérimentation vise à évaluer rigoureusement la qualité de l'étiquetage des relations et à explorer des axes d'amélioration. Voici les expériences planifiées :

### Exp 1 : Annotation manuelle (ground truth)

**Objectif** : Construire un jeu de référence (gold standard) pour évaluer quantitativement la qualité des labels.

**Protocole** :

- Sélectionner ~50 paires de personnages (25 par livre), représentatives des trois classes
- Chaque binôme annote indépendamment le type de relation en lisant le texte source

**Livrable** : Fichier `gold_annotations.csv` avec colonnes `chapter_id, charA, charB, gold_label`

### Exp 2 : Comparaison de modèles NLI

**Objectif** : Déterminer si un modèle alternatif produit des labels de meilleure qualité.

**Modèles à comparer** :

| Modèle                                        | Caractéristique                     |
| --------------------------------------------- | ----------------------------------- |
| `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`     | Multilingue, actuel                 |
| `cmarkea/distilcamembert-base-nli`            | Spécifique au français              |
| Mistral API (`mistral-medium`, temperature=0) | LLM en batch, qualité quasi-humaine |

**Protocole** : Évaluer chaque modèle sur le gold standard (Exp. 1).

### Exp 3 : Impact de la taille de fenêtre sur la qualité des relations

**Objectif** : Évaluer si `distance_max` affecte la qualité des labels (et pas seulement le nombre de co-occurrences).

**Protocole** :

- Faire varier `distance_max` : [25, 50, 75, 100, 150, 200]
- Comparer la distribution des labels et la qualité sur le gold standard
- Mesurer le nombre moyen de nœuds et d'arêtes par graphe

### Exp 4 : Faisabilité d'une taxonomie étendue (5 classes)

**Objectif** : Explorer l'extension de la taxonomie à 5 classes.

**Taxonomie proposée** :

| Label      | Signification                       |
| ---------- | ----------------------------------- |
| `ally`     | Coopération avec un objectif commun |
| `mentor`   | Relation de guidance/enseignement   |
| `hostile`  | Conflit, opposition                 |
| `romantic` | Relation intime                     |
| `neutral`  | Pas de signal clair                 |

**Protocole** :

- Tester avec le modèle NLI mDeBERTa (5 hypothèses françaises)
- Évaluer sur un sous-ensemble annoté (extension du gold standard)

### Exp 5 : Utilisation d'un LLM comme baseline de qualité supérieure

**Objectif** : Évaluer si un appel unique par lot à un API LLM peut servir de référence (ou de remplacement) pour le modèle NLI.

### Exp 5: Utilisation d'un LLM comme baseline de qualité supérieure

**Objectif** : Évaluer si un appel unique par lot à un LLM peut servir de référence (ou de remplacement) pour le modèle NLI.

**Protocole** :

- Appeler un LLM avec `temperature=0` (mode déterministe) et un prompt structuré :
  > _« Dans ce passage, la relation entre {charA} et {charB} est-elle amicale, hostile ou neutre ? Réponds par un seul mot. »_
- Stocker les résultats dans le cache existant
- Comparer avec les labels NLI

### Calendrier prévisionnel

| Semaine              | Activité                                                          |
| -------------------- | ----------------------------------------------------------------- |
| 1ère semaine d'avril | Exp. 1 : annotation manuelle (gold standard, 50 paires)           |
| 2ème semaine d'avril | Exp. 2 : comparaison de modèles NLI (mDeBERTa vs DistilCamemBERT) |
| 3ème semaine d'avril | Exp. 3 : impact de `distance_max` sur la qualité des relations    |
| 4ème semaine d'avril | Exp. 4 : faisabilité taxonomie 5 classes + Exp. 5 : LLM baseline  |

---

## 6. Anticipation du rapport final (>12 mai)

### Format imposé

Le rapport final est un **article scientifique en anglais**, rédigé en **LaTeX**, suivant la structure imposée :

1. **Introduction** — Contexte, problématique, revue de la littérature
2. **Methodology** — Pipeline complet (NER, alias, co-occurrence, étiquetage NLI), choix techniques justifiés
3. **Experimental Results** — Résultats de la campagne d'expérimentation (avril), métriques, comparaisons
4. **Conclusion** — Bilan, limites, perspectives
5. **References** — Bibliographie complète

### Références bibliographiques à collecter

| Thème                   | Références clés à rechercher                                                            |
| ----------------------- | --------------------------------------------------------------------------------------- |
| Zero-shot NLI           | Yin et al. (2019) — _Benchmarking Zero-shot Text Classification_                        |
| mDeBERTa / DeBERTa      | He et al. (2021) — _DeBERTa: Decoding-enhanced BERT with Disentangled Attention_        |
| XNLI (multilingual NLI) | Conneau et al. (2018) — _XNLI: Evaluating Cross-lingual Sentence Representations_       |
| Réseaux de personnages  | Elson & McKeown (2010) — _Automatic Attribution of Quoted Speech in Literary Narrative_ |
| Réseaux de personnages  | Labatut & Bost (2019) — _Extraction and Analysis of Fictional Character Networks_       |
| NER en français         | spaCy / Stanza documentation et articles associés                                       |
| Résolution d'alias      | Vala et al. (2015) — _Mr. Bennet, his coachman, and the Archbishop walk into a bar..._  |

### Planning de rédaction

| Période             | Activité                                             |
| ------------------- | ---------------------------------------------------- |
| Mi-avril            | Collecte des résultats expérimentaux + bibliographie |
| Fin avril           | Rédaction de la méthodologie + résultats             |
| 1ère semaine de mai | Rédaction introduction + revue de littérature        |
| 2ème semaine de mai | Conclusion + relecture croisée + soumission          |

---

## 7. Répartition des tâches

### Travaux réalisés (S2)

| Tâche                                                                   | Responsable  |
| ----------------------------------------------------------------------- | ------------ |
| Conception du plan d'implémentation                                     | Lotfi + Wael |
| Implémentation de `nlp_relation.py` (NLI zero-shot)                     | Lotfi + Wael |
| Implémentation de `nlp_manual_ner.py` (NER rule-based)                  | Lotfi        |
| Modification de `nlp_graph.py` (attribut `edge_type`)                   | Wael         |
| Intégration dans le notebook `nomodels.ipynb`                           | Wael         |
| Modification de `nlp_visualize_web.py` (arêtes colorées + HTML combiné) | Lotfi        |

### Travaux à venir

| Tâche                                          | Responsable  | Échéance           |
| ---------------------------------------------- | ------------ | ------------------ |
| Annotation manuelle (gold standard, 50 paires) | Lotfi + Wael | Début avril        |
| Campagne d'expérimentation (Exp. 1–5)          | Lotfi + Wael | Avril              |
| Collecte des références bibliographiques       | Lotfi        | Mi-avril           |
| Rédaction du rapport final (LaTeX, anglais)    | Lotfi + Wael | Fin avril – 12 mai |
| Relecture croisée et soumission                | Lotfi + Wael | 12 mai             |

---

## Annexes

### A. Fichiers du projet

| Fichier                     | Statut S2   | Rôle                                                            |
| --------------------------- | ----------- | --------------------------------------------------------------- |
| `nlp_relation.py`           | **Nouveau** | Classification des relations (NLI zero-shot, cache, validation) |
| `nlp_manual_ner.py`         | **Nouveau** | NER rule-based sans modèle IA                                   |
| `nlp_graph.py`              | **Modifié** | Génération du graphe avec attribut `edge_type`                  |
| `nlp_visualize_web.py`      | **Modifié** | Visualisation interactive avec arêtes colorées                  |
| `nomodels.ipynb`            | **Nouveau** | Notebook complet (pipeline rule-based + étiquetage)             |
| `nlp_cooccurrence.py`       | Inchangé    | Détection des co-occurrences                                    |
| `nlp_extract_characters.py` | Inchangé    | Comptage et filtrage des entités                                |
| `nlp_aliases.py`            | Inchangé    | Regroupement d'alias (Union-Find)                               |
| `nlp_utils.py`              | Inchangé    | Utilitaires (lecture de fichiers, anti-dict)                    |
| `antidict.txt`              | **Modifié** | Anti-dictionnaire (~868 entrées)                                |
| `characters.txt`            | **Modifié** | Liste de personnages pour le gazetteer                          |

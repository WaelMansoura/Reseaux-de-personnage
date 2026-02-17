---
marp: true
theme: default
paginate: true
---

# Extraction de Réseaux de Personnages

## Pipeline NLP pour l'Analyse Littéraire

Isaac Asimov - Cycle de Fondation

---

## Vue d'ensemble du Pipeline

1. **Lecture** du fichier texte
2. **Extraction** d'entités (NER)
3. **Regroupement** par alias
4. **Détection** de co-occurrences
5. **Génération** du graphe
6. **Export** vers fichier CSV

---

## Étape 1 : Lecture du Fichier

```python
text = read_file(chapter_file)
```

### Objectif

- Charger le contenu d'un chapitre
- Format : `.txt.preprocessed`
- Encodage : UTF-8

### Exemple

```
data/les_cavernes_d_acier/chapter_1.txt.preprocessed
```

---

## Étape 2 : Extraction d'Entités (NER)

```python
raw_entities = ensemble_entities(text, method="vote")
L = count_entities(raw_entities)
LP = filter_persons(L, anti_dict=anti_dict)
LL = filter_locations(L)
```

### Méthode Ensemble

- **spaCy** : modèle fr_core_news_lg
- **Stanza** : modèle NER français
- **Vote** : consensus entre les deux modèles

---

## Étape 2 : Extraction (Suite)

### Résultats

**L** : Toutes les entités détectées

```
Hari Seldon          PER    45
Trantor             LOC    23
```

**LP** : Personnes filtrées

```
Hari Seldon               45
Gaal Dornick              32
```

**LL** : Lieux filtrés

```
Trantor                   23
Terminus                  18
```

---

## Étape 2 : Sauvegarde des Résultats

```python
with open(f"{base_filename}_L.txt", "w") as f:
    for (text, label), count in L.most_common():
        f.write(f"{text:30}  {label:5}  {count}\n")
```

### Fichiers générés

- `chapter_1_L.txt` → toutes entités
- `chapter_1_LP.txt` → personnes
- `chapter_1_LL.txt` → lieux

---

## Étape 3 : Regroupement par Alias

```python
groups = group_aliases(LP)
alias_map = alias_dictionary(groups)
LP_merged = merge_alias_counts(LP, alias_map)
```

### Problème résolu

"Hari Seldon", "Seldon", "Hari" → **même personne**

### Algorithme

- Normalisation des noms
- Détection de mots-clés communs
- Regroupement automatique

---

## Étape 3 : Exemple de Regroupement

### Avant fusion

```
Hari Seldon      45
Seldon          120
Hari             30
```

### Après fusion

```
Hari Seldon     195  ← (45 + 120 + 30)
```

### Mapping d'alias

```python
{
  "Seldon": "Hari Seldon",
  "Hari": "Hari Seldon"
}
```

---

## Étape 4 : Détection de Co-occurrences

```python
cooccurrences = detect_cooccurrences(
    text,
    LP_merged,
    distance_max=25
)
```

### Principe

- Deux personnages qui apparaissent **proche l'un de l'autre**
- Distance maximale : **25 mots**
- Indicateur d'**interaction**

---

## Étape 4 : Exemple de Co-occurrence

### Texte

```
Hari Seldon regardait Gaal Dornick.
"Bienvenue", dit Seldon à Gaal.
```

### Résultat

```python
{
  ("Hari Seldon", "Gaal Dornick"): 2
}
```

→ Les deux personnages **interagissent**

---

## Étape 5 : Génération du Graphe

```python
G = generate_graph(cooccurrences, LP_merged)
```

### Structure NetworkX

- **Nœuds** : personnages
  - Attribut `count` : nombre de mentions
  - Attribut `names` : liste d'alias
- **Arêtes** : co-occurrences
  - Attribut `weight` : fréquence d'interaction

---

## Étape 5 : Ajout des Alias au Graphe

```python
for group in groups:
    canonical = group[0]
    if canonical in G.nodes:
        G.nodes[canonical]["names"] = ";".join(group)
```

### Format requis (Kaggle)

```python
G.nodes["Hari Seldon"]["names"] = "Hari Seldon;Seldon;Hari"
```

**Important** : séparateur = **point-virgule**

---

## Étape 6 : Export vers CSV

```python
graphml = "".join(nx.generate_graphml(G))
df_dict["ID"].append(chapter_id)
df_dict["graphml"].append(graphml)
```

### Format de soumission

| ID  | graphml                  |
| --- | ------------------------ |
| A0  | `<graphml>...</graphml>` |
| A1  | `<graphml>...</graphml>` |

### Convention des ID

- **A** = Les Cavernes d'Acier
- **B** = Prélude à Fondation

---

## Pipeline Complet : Récapitulatif

```python
text = read_file(chapter_file)                    # 1
entities = ensemble_entities(text)                # 2a
LP = filter_persons(count_entities(entities))     # 2b
alias_map = alias_dictionary(group_aliases(LP))   # 3
LP_merged = merge_alias_counts(LP, alias_map)     # 3
cooc = detect_cooccurrences(text, LP_merged)      # 4
G = generate_graph(cooc, LP_merged)               # 5
# Ajout attribut 'names' + export GraphML         # 6
```

---

## Résultats Attendus

### Métriques par chapitre

- **15-30** personnages uniques
- **30-80** interactions (arêtes)
- **Précision** : 70-85%

### Amélioration v2

- Gazetteer : +40% de précision
- CamemBERT : +20% de précision
- Alias résolution : -30% de doublons

---

## Outils & Technologies

### Modèles NLP

- **spaCy** : `fr_core_news_lg`
- **Stanza** : modèle français
- **CamemBERT** : transformers (optionnel)

### Bibliothèques

- **NetworkX** : création de graphes
- **pandas** : manipulation CSV
- **fuzzywuzzy** : matching flou

---

## Merci !

### Questions ?

**GitHub** : WaelMansoura/Reseaux-de-personnage
**Contexte** : Projet AMS - Analyse de textes littéraires

---

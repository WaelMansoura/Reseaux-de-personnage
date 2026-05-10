# `nlp_manual_ner.py` — Reconnaissance d'entités nommées par règles

## Objectif

Extraire les entités personnages (PER) et lieux (LOC) de romans français **sans** aucun modèle d'IA. Pures règles, regex, gazetteers. Conçu comme remplacement direct du NER spaCy/transformer, retournant exactement le même format `list[tuple[str, str]]` consommé par `nlp_extract_characters.count_entities()`.

Utilisé comme première étape du pipeline dans `main` — remplace le NER d'ensemble IA du notebook original.

## Organisation du module

Trois stratégies indépendantes, combinées à la fin :

1. **Recherche dans le gazetteer** — noms connus depuis un dictionnaire codé en dur + fichier optionnel `characters.txt`.
2. **Heuristiques de capitalisation** — noms propres en milieu de phrase que l'analyse en minuscules suggère comme noms réels.
3. **Patrons regex** — noms avec titre (`Docteur X`, `Capitaine Y`) et convention robot (`R. Daneel`).

Plus un **générateur de blocklist dynamique** qui apprend les faux positifs courants depuis le corpus lui-même.

## Gazetteers par défaut

Deux dictionnaires associent un nom canonique à une liste d'alias. Les deux utilisés par tout le pipeline (NER, résolution d'alias, filtrage blocklist).

```python
ASIMOV_CHARACTERS = {
    "Hari Seldon": ["Seldon", "Hari"],
    "Eto Demerzel": ["Demerzel", "Eto"],
    "Cleon I": ["Cléon", "l'Empereur", "Empereur", "Sire"],
    "R. Daneel Olivaw": ["Daneel", "R. Daneel", "Daneel Olivaw", "Olivaw"],
    # ...
}

ASIMOV_LOCATIONS = {
    "Trantor": ["Trantor"],
    "Mycogène": ["Mycogène"],
    "Spacetown": ["Spacetown"],
    # ...
}
```

Surcharge via les paramètres `gazetteer_characters` / `gazetteer_locations` pour des textes non-Asimov :

```python
custom_chars = {"Frodo Baggins": ["Frodo"], "Gandalf": ["Mithrandir"]}
manual_extract_entities(text, gazetteer_characters=custom_chars, ...)
```

## Stratégie 1 — Scan du gazetteer

`_gazetteer_scan(text, gazetteer)` parcourt le gazetteer **du plus long au plus court** et utilise des limites de mots regex qui fonctionnent avec les caractères français accentués :

```python
def _build_word_boundary_re(name: str) -> re.Pattern:
    escaped = re.escape(name)
    escaped = re.sub(r"\\ ", r"\\s+", escaped)
    word_char = r"[a-zA-ZÀ-ÿ0-9_]"
    pattern = rf"(?<!{word_char}){escaped}(?!{word_char})"
    return re.compile(pattern, re.UNICODE)
```

Pourquoi des limites personnalisées : le `\b` Python ne traite pas `é`, `à`, `ü` comme caractères de mot, donc `\bSeldon\b` correspondrait joyeusement à l'intérieur de `Séldoné`. Le lookaround avec classe Unicode explicite corrige ce problème.

Protection contre le chevauchement : suit les positions appariées dans un set pour que `"Hari Seldon"` ne produise _pas aussi_ des correspondances séparées `"Hari"` et `"Seldon"` aux mêmes offsets.

```python
matched_positions = set()
for name, label in gazetteer:  # déjà trié du plus long au plus court
    for match in pattern.finditer(text):
        span_positions = set(range(match.start(), match.end()))
        if span_positions & matched_positions:
            continue
        matched_positions.update(span_positions)
        results.append((normalize_span(match.group()), label))
```

## Stratégie 2 — Heuristiques de capitalisation

Le plus difficile : détecter des noms propres inconnus absents du gazetteer. L'idée naïve « majuscule = nom » échoue car les phrases françaises commencent aussi par une majuscule.

### Astuce du vocabulaire en minuscules

Idée clé : si un mot apparaît _aussi_ en minuscules quelque part dans le texte, il n'est probablement pas un nom propre — c'est juste un mot ordinaire capitalisé en début de phrase.

```python
def _build_lowercase_vocabulary(text: str) -> set[str]:
    return set(re.findall(r'\b([a-zà-ÿ]{2,})\b', text))
```

Puis dans le scan : `clean.lower() not in lowercase_vocab` filtre `Étouffant`, `Maintenant`, `Cependant`, etc.

### Découpage de phrases sensible aux dialogues

```python
_SENTENCE_SPLIT = re.compile(
    r'(?<=[.!?…»"\n])\s*\n\s*(?=[A-ZÀ-Ü])|(?<=[.!?…»"])\s+(?=[A-ZÀ-Ü])',
    re.UNICODE,
)

_DIALOGUE_OPEN = re.compile(r'^[«—–\-"]\s*', re.UNICODE)
```

Pour chaque phrase, le premier token est ignoré (initial de phrase = capitalisé peu importe). Les tokens suivant des marqueurs de dialogue inline (`:`, `«`, `—`) aussi ignorés.

### Regroupement multi-mots

Tokens capitalisés consécutifs regroupés : `Alban Wellis` → une entité `"Alban Wellis"`, plus les parties individuelles `"Alban"` et `"Wellis"` pour que la résolution d'alias en aval puisse les fusionner.

### Plancher de fréquence

Les noms purement heuristiques doivent apparaître au moins `MIN_CAP_FREQ = 2` fois. Mentions uniques probablement bruit OCR ou faux positifs rares :

```python
cap_counts = Counter(name for name, _ in cap_results)
cap_results = [(name, label) for name, label in cap_results
               if cap_counts[name] >= MIN_CAP_FREQ]
```

## Stratégie 3 — Patrons regex

Deux patrons : noms avec titre et noms de robots.

```python
_TITLE_PREFIXES = (
    r"Docteur|Dr\.|Professeur|Prof\.|Monsieur|M\.|Madame|Mme\.?"
    r"|Mademoiselle|Mlle\.?|Capitaine|Colonel|Général|Lieutenant"
    r"|Sergent|Commissaire|Inspecteur|Maître"
)

_ROBOT_PATTERN = re.compile(
    r"\bR\.\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)",
    re.UNICODE,
)
```

Le patron de titre extrait _uniquement_ le nom, en abandonnant le titre (donc `"Docteur Sarton"` retourne `"Sarton"`). Le patron robot conserve le préfixe `R.` car il fait partie du nom canonique dans l'univers d'Asimov (`R. Daneel`, `R. Giskard`, `R. Sammy`).

Désactiver le patron robot pour textes non-Asimov :

```python
manual_extract_entities(text, enable_robot_pattern=False)
```

## Blocklist dynamique

`precompute_dynamic_blocklist()` s'exécute **une fois sur tout le corpus** avant le NER. Compte chaque mot en forme capitalisée vs minuscule, signale les mots apparaissant capitalisés ≥70 % du temps et ≥5 fois au total (en excluant les entrées du gazetteer) :

```python
dynamic_blocklist = precompute_dynamic_blocklist(
    all_texts,
    gazetteer_characters=GAZETTEER_CHARACTERS,
    gazetteer_locations=GAZETTEER_LOCATIONS,
)
```

Capture des mots comme `Galaxie`, `Terriens`, `Bible`, `Trantorien` — apparaissent capitalisés mais ne sont pas des noms propres. Le notebook utilise l'inspection du ratio pour valider :

```
Top 20 dynamic blocklist words (word, cap_ratio, total, cap_count, lower_count):
  terriens             ratio=1.000 total=  34 cap=  34 lower=   0
  galaxie              ratio=1.000 total=  32 cap=  32 lower=   0
  maîtresse            ratio=1.000 total=  21 cap=  21 lower=   0
  ...
```

## Point d'entrée principal

```python
def manual_extract_entities(text,
                            character_file="characters.txt",
                            anti_dict=None,
                            include_locations=False,
                            dynamic_blocklist=None,
                            gazetteer_characters=None,
                            gazetteer_locations=None,
                            title_prefixes=None,
                            enable_robot_pattern=True) -> list[tuple[str, str]]:
```

Ordre du pipeline :

1. Fusionner `dynamic_blocklist` dans `anti_dict`.
2. Construire le gazetteer (personnalisé ou par défaut).
3. Lancer le scan du gazetteer → `gaz_results`.
4. Lancer le scan regex → `regex_results`.
5. Calculer noms connus = gazetteer ∪ noms regex.
6. Lancer le scan de capitalisation, filtrant contre noms connus + `anti_dict` + vocabulaire minuscule.
7. Éliminer les noms heuristiques sous `MIN_CAP_FREQ`.
8. Concaténer les trois listes de résultats.

## Utilisation dans le notebook

Depuis la cellule `251253d0` de `main` :

```python
raw_entities = manual_extract_entities(
    text,
    anti_dict=anti_dict,
    include_locations=True,
    dynamic_blocklist=dynamic_blocklist,
    gazetteer_characters=GAZETTEER_CHARACTERS,
    gazetteer_locations=GAZETTEER_LOCATIONS,
    title_prefixes=TITLE_PREFIXES,
    enable_robot_pattern=ENABLE_ROBOT_PATTERN,
)

L  = count_entities(raw_entities)
LP = filter_persons(L, anti_dict=anti_dict)
LL = filter_locations(L)
```

Exécution complète sur 37 chapitres ~4 secondes (vs ~2-5 minutes pour l'ensemble IA), sortie mise en cache dans `ner_cache3.pkl` pour réutilisation.

## Adaptation à d'autres textes

Pour un roman français non-Asimov :

```python
custom_chars = {"Jean Valjean": ["Valjean", "Jean"], "Cosette": ["Cosette"]}
custom_locs  = {"Paris": ["Paris"], "Digne": ["Digne"]}

raw = manual_extract_entities(
    text,
    gazetteer_characters=custom_chars,
    gazetteer_locations=custom_locs,
    enable_robot_pattern=False,  # pas de SF
    include_locations=True,
)
```

Pour l'anglais : passer `title_prefixes=r"Lord|Lady|Sir|Mr\.?|Mrs\.?|Dr\.?|Captain|King|Queen"`.

## Modes d'échec

- **Titres en majuscules** (`CHAPITRE PREMIER`) — gérés par `is_valid_entity()` dans `nlp_extract_characters.py`, qui rejette les spans uniquement en majuscules.
- **Noms à trait d'union** (`Jean-Pierre`) — actuellement rejetés par `is_valid_entity` car les traits d'union introduisent souvent des faux positifs (`grand-père`, `peut-être`).
- **Erreurs OCR** capitalisant des mots aléatoires — interceptées par le plancher `MIN_CAP_FREQ` + blocklist dynamique.
- **« Noms » d'une seule lettre** (`R.`, `M.`) — interceptés par le contrôle de longueur d'`is_valid_entity`.

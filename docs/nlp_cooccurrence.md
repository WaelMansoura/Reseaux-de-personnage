# `nlp_cooccurrence.py` — Détection de co-occurrence par fenêtre glissante

## Objectif

Construire les **données d'arêtes** du réseau de personnages : compter combien de fois chaque paire de personnages apparaît dans une fenêtre de distance fixe en mots. Le `Counter` de sortie indexé sur `(charA, charB)` devient les poids des arêtes dans le graphe final.

Fonction unique : `detect_cooccurrences(text, character_counts, distance_max=25)`. Pas d'état, pas d'effets de bord.

## Vue d'ensemble de l'algorithme

1. Tokeniser le texte et les noms de personnages avec la même regex (critique pour la cohérence).
2. Trouver chaque position de chaque nom de personnage dans l'espace des tokens.
3. Faire glisser une fenêtre de taille `distance_max` à travers le flux de tokens.
4. Pour chaque fenêtre, trouver quels personnages sont présents.
5. Incrémenter le compte pour chaque paire `(a, b)` de personnages dans la fenêtre.
6. Retourner un `Counter` de paires.

La recherche de position utilise la **recherche binaire** (`bisect`) pour garder la boucle interne en O(log N) par personnage par pas de fenêtre.

## Cohérence de tokenisation

Le détail le plus important du fichier :

```python
tokens = re.findall(r"\w+", text.lower())
```

Et les noms de personnages utilisent la **même** regex :

```python
for name in character_counts.keys():
    name_lower = name.lower()
    name_tokens = re.findall(r"\w+", name_lower)
    char_names_lower.append(name_tokens)
    lowercase_to_original[" ".join(name_tokens)] = name
```

Pourquoi c'est important : le texte français a des apostrophes (`l'Empereur`). Si la tokenisation du texte sépare `"l'Empereur"` en `["l", "empereur"]` mais la tokenisation du nom sépare `"l'Empereur"` en `["l'empereur"]` (ou inversement), le matcher rate silencieusement chaque occurrence. Le même `\w+` des deux côtés les garde alignés : les deux produisent `["l", "empereur"]`.

`\w+` ne correspond *pas* aux apostrophes — elles deviennent des limites de tokens. C'est le comportement souhaité étant donné le reste du pipeline.

## Cartographie des positions

Pour chaque personnage, localiser chaque occurrence dans le flux de tokens :

```python
char_positions = {}
for name_tokens in char_names_lower:
    name_len = len(name_tokens)
    name_str = " ".join(name_tokens)
    positions = []
    for i in range(len(tokens) - name_len + 1):
        if tokens[i:i+name_len] == name_tokens:
            positions.append(i)
    char_positions[name_str] = positions

for char in char_positions:
    char_positions[char].sort()
```

`positions` stocke l'indice de token de **début** de chaque correspondance. Les noms multi-tokens (`"hari seldon"` = 2 tokens) correspondent à `tokens[i:i+2]`. La liste est ensuite triée pour permettre la recherche binaire.

Complexité : O(T × C) pour la passe de recherche, où T est le total de tokens et C le nombre de personnages. Pour ~10k tokens et ~10 personnages, c'est correct.

## Fenêtre glissante avec recherche binaire

La boucle externe parcourt position par position :

```python
for i in range(len(tokens)):
    window_start = i
    window_end = i + distance_max

    present_chars = []
    for char, positions in char_positions.items():
        idx = bisect_left(positions, window_start)
        if idx < len(positions) and positions[idx] <= window_end:
            present_chars.append(char)

    for a, b in combinations(sorted(set(present_chars)), 2):
        original_a = lowercase_to_original[a]
        original_b = lowercase_to_original[b]
        cooccurrences[(original_a, original_b)] += 1
```

`bisect_left(positions, window_start)` retourne l'indice de la première position ≥ `window_start`. Si cette position est ≤ `window_end`, le personnage a au moins une occurrence dans `[window_start, window_end]`.

Cela remplace un `any(window_start <= p <= window_end for p in positions)` naïf (O(N)) par une recherche O(log N). Pour un chapitre avec des milliers de fenêtres × dizaines de personnages × centaines de positions chacun, le gain s'accumule.

## Pourquoi `combinations` sur `present_chars`

`itertools.combinations` produit chaque paire non ordonnée exactement une fois. `sorted(set(...))` garantit un ordre de clé déterministe — `(charA, charB)` est toujours trié alphabétiquement, donc deux exécutions produisent des clés `Counter` identiques. Sans tri, la même paire pourrait être stockée à la fois en `(A, B)` et `(B, A)` dans des exécutions différentes, cassant les caches.

## Sémantique de la fenêtre glissante

Un personnage est « dans la fenêtre » si **au moins une** occurrence tombe dans `[i, i+distance_max]`. La fenêtre glisse d'un token à la fois. Conséquence : une paire de personnages qui co-apparaît une fois est comptée plusieurs fois — une fois pour chaque fenêtre qui contient les deux.

Si `A` est en position 100 et `B` en position 110 avec `distance_max=25` :
- `i=85` à `i=100` (16 fenêtres) : à la fois `A` et `B` atteignables depuis le début de fenêtre dans 25 tokens → 16 incréments.

Intentionnel. **Les paires plus proches accumulent plus de poids** car elles apparaissent dans plus de fenêtres qui se chevauchent. Donc le compte de co-occurrence est approximativement inversement proportionnel à la distance — les paires courte distance obtiennent des poids d'arête plus élevés, capturant l'intimité de l'interaction.

## Astuce de préservation de la casse

```python
lowercase_to_original = {}
...
lowercase_to_original[" ".join(name_tokens)] = name
```

Le calcul interne est en minuscules (pour des vérifications d'égalité rapides), mais le `Counter` de sortie est indexé sur les noms à **casse originale** préservée. La carte inverse `lowercase_to_original` reconstruit les clés en casse correcte avant le stockage.

Exemple de mapping :
```python
{"hari seldon": "Hari Seldon", "demerzel": "Demerzel"}
```

Cela signifie que la résolution d'alias en amont doit finaliser les noms canoniques *avant* d'appeler cette fonction — sinon différentes variantes de casse du même personnage produisent des arêtes séparées.

## Réglage de `distance_max`

Le paramètre principal du notebook :

```python
distance_max    = 150   # Taille de la fenêtre de co-occurrence en mots
min_occurrences = 2     # Seuil de filtrage
```

Compromis :

| Valeur | Effet |
|--------|-------|
| 25     | Échelle conversation : seulement paires même paragraphe |
| 50     | Échelle scène : paragraphe à paragraphe |
| 150    | Échelle page : personnages dans le même bloc de scène |
| 500    | Échelle chapitre : la plupart des paires co-occurrent, arêtes bruitées |

*Prélude à Fondation* d'Asimov répond bien à 150 car les scènes s'étendent sur plusieurs paragraphes de dialogue + description. Les textes au rythme plus rapide peuvent vouloir 50.

## Utilisation dans le notebook

```python
from nlp_cooccurrence import detect_cooccurrences

cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
```

Échantillon de sortie (depuis `paf0`) :
```python
Counter({
    ("Cléon", "Demerzel"): 47,
    ("Cléon", "Seldon"): 31,
    ("Demerzel", "Seldon"): 28,
    ("Hummin", "Seldon"): 12,
    ...
})
```

Puis injecté dans `nlp_relation.label_relationships()` et `nlp_graph.generate_graph()`.

## Notes de performance

- Le pré-tri de `positions` est obligatoire pour la correction de `bisect_left`.
- Le `range(len(tokens))` externe pourrait sauter `distance_max` tokens à la fois sans perdre d'arêtes (au prix de gonfler les poids de courte distance). L'implémentation actuelle privilégie l'échantillonnage uniforme.
- Pour de très gros textes (>100k tokens), envisager de remplacer la boucle de personnages par position par une requête d'arbre d'intervalles.

## Modes d'échec

- **Apostrophes tokenisées de manière incohérente** — corrigé en utilisant le même `\w+` partout ; si vous changez la tokenisation, changez-la aux *deux* endroits.
- **Alias pas encore fusionnés** — le même personnage avec deux formes de surface (`Cléon`, `Empereur`) compté comme nœuds séparés. Toujours exécuter la résolution d'alias en premier.
- **Noms multi-mots avec tokens répétés** — par ex. un hypothétique `"Anna Anna"` correspondrait à chaque paire de tokens `anna anna`, pas de gestion spéciale nécessaire mais semble bizarre.
- **`distance_max` plus petit que le nom de personnage le plus long** — les noms multi-tokens (`"Hari Seldon"` = 2 tokens) fonctionnent toujours car la position est le *début* de la correspondance, mais si `distance_max < name_len` vous ne pouvez avoir deux tels noms dans une fenêtre. Mettre `distance_max ≥ 10` pour être sûr.

## Exemple détaillé

Petit texte :
```python
text = "Hari Seldon entered the room. Demerzel watched silently. Cléon spoke to Demerzel. Hari nodded."
LP_merged = Counter({"Hari Seldon": 1, "Demerzel": 2, "Cléon": 1})
```

Après `re.findall(r"\w+", text.lower())` :
```python
tokens = ["hari", "seldon", "entered", "the", "room",
          "demerzel", "watched", "silently",
          "cléon", "spoke", "to", "demerzel",
          "hari", "nodded"]
```

La recherche de position donne :
```python
{
    "hari seldon": [0],
    "demerzel":    [5, 11],
    "cléon":       [8],
}
```

Noter que `"hari"` seul (token 12) ne correspond pas à `"hari seldon"` car le token suivant est `"nodded"`, pas `"seldon"`. La résolution d'alias en amont aurait déjà fusionné `"Hari"` dans `"Hari Seldon"` — mais si cette étape était sautée, la mention isolée de `"Hari"` est invisible à cette fonction.

Avec `distance_max=10` :
- Fenêtre démarrant à 0 : contient `hari seldon` (pos 0) et `demerzel` (pos 5) → paire `("Demerzel", "Hari Seldon")` += 1.
- Fenêtres 1-5 : voient toujours les deux → 5 incréments de plus.
- Fenêtre démarrant à 5 : capture aussi `cléon` (pos 8) → triple `(Cléon, Demerzel)`, `(Cléon, Hari Seldon)`, `(Demerzel, Hari Seldon)`.
- Fenêtre 11+ : `Cléon` et second `Demerzel` coprésents.

`Counter` final (approximatif) :
```python
Counter({
    ("Demerzel", "Hari Seldon"): 11,
    ("Cléon",    "Demerzel"):     8,
    ("Cléon",    "Hari Seldon"):  3,
})
```

Les paires plus proches accumulent plus vite — exactement le comportement souhaité pour la sémantique « intimité » du réseau de personnages.

## Interaction avec le filtre de fréquence

`detect_cooccurrences` ne sait rien des seuils. Si un personnage avec un compte de 1 se faufile au-delà de `filter_by_frequency`, il obtient quand même des arêtes de co-occurrence. Le notebook filtre toujours en premier :

```python
LP_merged = filter_by_frequency(LP_merged, min_occurrences)
cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
```

Ainsi seuls les « vrais » personnages génèrent des arêtes. Les arêtes vers des personnages filtrés seraient éliminées plus tard dans `nlp_graph.generate_graph` via le contrôle d'appartenance, mais les sauter en amont économise du travail.

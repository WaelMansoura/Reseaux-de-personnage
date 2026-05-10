# `nlp_aliases.py` — Résolution d'alias et noms canoniques

## Objectif

Fusionner les variantes de forme de surface du même personnage en un nom canonique unique. Après le NER, le même personnage apparaît comme `"Hari Seldon"`, `"Seldon"`, `"Hari"`, `"Dr Seldon"` — tous doivent correspondre à un seul nœud du graphe.

Implémente un **regroupement union-find** avec des règles linguistiques pour décider quelles formes vont ensemble, plus des surcharges optionnelles via gazetteer et patches manuels.

## Contrat de sortie

Le pipeline attend :
```python
groups    = group_aliases(LP)         # list[list[str]] — clusters
alias_map = alias_dictionary(groups)  # {surface: canonical}
LP_merged = merge_alias_counts(LP, alias_map)  # Counter indexé sur canonique
```

Où canonique = forme de surface la plus fréquente dans chaque cluster.

## Normalisation

Avant toute comparaison, les noms sont normalisés :

```python
TITLES = ["mr", "mme", "mrs", "ms", "dr", "prof", "sir",
          "m", "mlle", "lord", "maître", "colonel", "commissaire",
          "inspecteur", "capitaine", "général", "docteur"]

def normalize_name(name: str) -> str:
    n = name.lower().strip()
    for t in TITLES:
        n = re.sub(rf"\b{t}\b\.?", "", n)
    n = re.sub(r"[^\w\sàâäéèêëîïôöùûüç-]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n
```

Effet : `"Dr Sarton"` → `"sarton"`, `"R. Daneel Olivaw"` → `"r daneel olivaw"`.

`name_keywords()` retourne le **set** de tokens normalisés — utilisé pour l'arithmétique d'ensembles lors des décisions de fusion.

## Union-Find

Classe interne `_UnionFind` avec compression de chemin :

```python
class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # compression
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[ry] = rx
```

Pourquoi union-find : la fusion est indépendante de l'ordre. `_should_merge("Hari", "Seldon") = False`, mais si les deux pointent vers `"Hari Seldon"` séparément, la transitivité les met dans le même cluster. Une approche gloutonne raterait cela selon l'ordre d'itération.

## Décision de fusion — `_should_merge`

La fonction la plus subtile du fichier. Quatre cas :

```python
def _should_merge(name1: str, name2: str) -> bool:
    kw1 = name_keywords(name1)
    kw2 = name_keywords(name2)
    if not kw1 or not kw2:
        return False

    shared = kw1 & kw2
    multi1 = len(kw1) > 1
    multi2 = len(kw2) > 1

    if shared:
        meaningful_shared = {k for k in shared if len(k) > 1}
        if not meaningful_shared:
            return False  # chevauchement uniquement de char unique (préfixe robot "r.")

        if not multi1 and not multi2:
            # Les deux mono-mot → correspondance floue requise
            return fuzz_ratio(normalize_name(name1), normalize_name(name2)) >= FUZZY_THRESHOLD

        if multi1 and multi2:
            # Les deux multi-mots → exiger sous-ensemble (l'un abréviation de l'autre)
            return kw1.issubset(kw2) or kw2.issubset(kw1)

        # Un mono-mot, un multi-mot → chevauchement significatif suffit
        return bool(meaningful_shared)

    # Aucun mot-clé partagé → repli flou (multi-mot uniquement)
    if multi1 or multi2:
        return fuzz_ratio(normalize_name(name1), normalize_name(name2)) >= FUZZY_THRESHOLD

    return False
```

### Pourquoi la règle de sous-ensemble multi-mots

Critique pour la famille `Darell`. Sans elle :

- `"Bayta Darell"` et `"Arcadia Darell"` partagent `{"darell"}` → fusionneraient → **incorrect**, ce sont des personnages différents.

Avec la règle de sous-ensemble :

- `kw("Bayta Darell")  = {"bayta", "darell"}`
- `kw("Arcadia Darell")= {"arcadia", "darell"}`
- Aucun n'est sous-ensemble de l'autre → pas de fusion. ✓

Mais :

- `kw("Hari Seldon")` et `kw("Seldon")={"seldon"}` — le second sous-ensemble du premier → fusion. ✓

### Pourquoi le seuil flou de 88

Les faux positifs mono-token sont méchants. `"Hari"` vs `"Harinder"` :
- Même préfixe
- Personnes différentes
- Ratio `SequenceMatcher` ~75 — sous 88 → pas de fusion. ✓

`"Cléon"` vs `"Cléone"` :
- Même personne en variantes orthographiques
- Ratio ~91 → fusion. ✓

Réglage : `FUZZY_THRESHOLD = 88`. Plus bas → fusion plus agressive. Plus haut → plus de clusters mono-nom isolés.

## Pré-passe d'ambiguïté

Avant la boucle de fusion principale, les noms mono-token correspondant à *plusieurs* noms multi-mots sont pré-assignés au plus fréquent :

```python
single_token_assignment: dict[str, str | None] = {}

for name in names:
    kw = kw_cache[name]
    if len(kw) != 1:
        continue
    (token,) = kw
    if len(token) <= 1:
        continue

    multiword_matches = [
        n for n in names
        if len(kw_cache[n]) > 1 and token in kw_cache[n]
    ]
    if len(multiword_matches) > 1:
        best = max(multiword_matches, key=lambda n: LP.get(n, 0))
        single_token_assignment[name] = best
    elif len(multiword_matches) == 1:
        single_token_assignment[name] = multiword_matches[0]
```

Puis la boucle de fusion respecte cette assignation :

```python
if len(kw1) == 1 and name in single_token_assignment:
    if single_token_assignment[name] != other:
        continue
```

Concret : si `"Darell"` pourrait s'attacher à `"Bayta Darell"` ou `"Arcadia Darell"`, il va vers celui qui a le compte le plus élevé dans ce chapitre. Imparfait (la bonne réponse dépend du contexte), mais cohérent et empêche un effondrement accidentel.

## Sélection canonique

```python
def group_aliases(LP: Counter) -> list:
    ...
    result = []
    for group in raw_groups:
        sorted_group = sorted(group, key=lambda n: LP.get(n, 0), reverse=True)
        result.append(sorted_group)
    return result
```

`group[0]` = forme de surface la plus fréquente = canonique. Pourquoi la fréquence : la forme la plus utilisée est la plus lisible dans les graphes et la moins surprenante pour les utilisateurs. `"Seldon"` (compte 47) bat `"Hari Seldon"` (compte 12) comme canonique.

## Surcharge gazetteer — `apply_gazetteer_aliases`

Corrige les cas où l'auto-grouper sépare ce que le gazetteer dit être un seul personnage. Pour chaque entrée du gazetteer :

```python
for gaz_canonical, gaz_aliases in gazetteer_characters.items():
    all_forms = [gaz_canonical] + list(gaz_aliases)

    current_canonicals: dict[str, int] = {}
    for form in all_forms:
        if form in patched:
            canon = patched[form]
            if canon not in current_canonicals:
                weight = sum(lp.get(f, 0) for f, c in patched.items() if c == canon)
                current_canonicals[canon] = weight

    if len(current_canonicals) <= 1:
        continue

    best = max(current_canonicals, key=lambda c: current_canonicals[c])
    displaced = {c for c in current_canonicals if c != best}
    for k in list(patched):
        if patched[k] in displaced:
            patched[k] = best
```

Choisit le canonique **observé** avec le plus de poids LP comme gagnant. Ainsi `"Cléon"` bat `"Cleon I"` quand le texte français n'utilise jamais l'orthographe anglaise — même si la clé du gazetteer est `"Cleon I"`.

## Surcharge manuelle — `apply_manual_aliases`

Dernier recours pour les cas que auto + gazetteer ne peuvent corriger. Depuis le notebook :

```python
MANUAL_ALIASES = {
    "Empereur":   "Cléon",
    "l'Empereur": "Cléon",
    "L’Empereur": "Cléon",
    "Sire":       "Cléon",
    "Cléon Ier":  "Cléon",
}
```

Pourquoi nécessaire : `"Empereur"` n'a aucun chevauchement de mot-clé avec `"Cléon"`. Aucune règle automatique ne pourrait jamais les connecter. L'entrée manuelle force la fusion.

L'implémentation redirige transitivement tout ce qui pointait *vers* l'ancien canonique :

```python
for surface, manual_canonical in manual_overrides.items():
    old_canonical = patched.get(surface, surface)
    patched[surface] = manual_canonical
    if old_canonical != manual_canonical:
        for k in list(patched):
            if patched[k] == old_canonical:
                patched[k] = manual_canonical
```

## Fusion et filtrage

```python
def merge_alias_counts(LP: Counter, alias_map: dict) -> Counter:
    merged = Counter()
    for name, count in LP.items():
        canonical = alias_map.get(name, name)
        merged[canonical] += count
    return merged

def filter_by_frequency(character_counts, min_occurrences=2):
    return Counter({n: c for n, c in character_counts.items() if c >= min_occurrences})
```

L'ordre compte : fusion d'alias **d'abord**, filtre de fréquence **ensuite**. Sinon `"Hari"` (compte 5) et `"Seldon"` (compte 30) pourraient passer individuellement `min=10` mais `"Hari Seldon"` ne devrait pas être filtré quand ses parties fusionnent à un compte de 35.

## Câblage dans le notebook

```python
groups    = group_aliases(LP)
alias_map = alias_dictionary(groups)
alias_map = apply_gazetteer_aliases(alias_map, ASIMOV_CHARACTERS, LP)
alias_map = apply_manual_aliases(alias_map, MANUAL_ALIASES)
LP_merged = merge_alias_counts(LP, alias_map)
LP_merged = filter_by_frequency(LP_merged, min_occurrences)
```

Ordre : auto-cluster → correction gazetteer → patch manuel → fusion des comptes → filtrage.

## Test de fumée

`_test_alias_grouping()` intégré s'exécute en lançant le module directement :

```bash
python3 nlp_aliases.py
```

Vérifie :
- `Hari Seldon` ↔ `Seldon` ↔ `Hari` fusionnent.
- `Bayta Darell` ≠ `Arcadia Darell` (règle de sous-ensemble).
- `Hari` ≠ `Harinder` (seuil flou).

## Modes d'échec

- Deux personnages avec noms de famille identiques ET fréquences de prénoms identiques perturbent la pré-passe d'ambiguïté — choisir un bris d'égalité déterministe et faire avec.
- Canonique du gazetteer non observé dans le chapitre ne contribue à rien — pas de mal, juste pas d'effet.
- `rapidfuzz` retombe sur `difflib.SequenceMatcher` s'il n'est pas installé ; les ratios changent légèrement, peuvent croiser le seuil 88 différemment. Installer `rapidfuzz` pour un comportement stable.

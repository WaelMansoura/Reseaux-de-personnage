# `nlp_extract_characters.py` — Comptage et filtrage d'entités

## Objectif

Pont entre la sortie NER brute (`list[tuple[str, str]]`) et les étapes en aval de regroupement d'alias / co-occurrence. Trois responsabilités :

1. **Chargement paresseux de spaCy** — pour le chemin de repli NER-IA optionnel.
2. **Comptage d'entités** — convertir une liste de paires `(text, label)` en `Counter`.
3. **Filtrage** — séparer en personnes (LP) vs lieux (LL), avec une règle de validité partagée qui rejette acronymes, tokens à trait d'union et chaînes ultra-courtes.

Dans `nomodels-relations.ipynb` seules `count_entities`, `filter_persons`, `filter_locations` et `is_valid_entity` sont utilisées — le chemin spaCy est dormant puisque le NER par règles le remplace.

## Chargement paresseux du modèle

`fr_core_news_lg` pèse ~500 Mo. Charger à l'import serait gaspilleur quand le pipeline par règles n'en a jamais besoin. Le module se protège derrière un singleton :

```python
_nlp_model = None

def get_spacy_model():
    global _nlp_model
    if _nlp_model is None:
        print("🔄 Loading spaCy model for entity extraction...")
        _nlp_model = spacy.load("fr_core_news_lg")
        print("✅ spaCy model loaded!")
    return _nlp_model
```

Le `global` + vérification `is None` garantit la survie du modèle au `importlib.reload(...)` dans Jupyter — recharger le module efface les définitions de fonctions mais l'objet module (et `_nlp_model` à l'intérieur) n'est rebindé que si le rechargement réexécute l'assignation. Plus sûr d'appeler `get_spacy_model()` défensivement plutôt que de compter sur l'état au niveau supérieur.

## `extract_entities(text)` — Chemin spaCy

Exécuté uniquement quand l'utilisateur *veut* le NER IA :

```python
def extract_entities(text: str):
    nlp = get_spacy_model()
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append((ent.text, ent.label_))
    return entities
```

Format de sortie : `[("Hari Seldon", "PER"), ("Trantor", "LOC"), ...]` — identique à ce que retourne `manual_extract_entities()`. Intentionnel : le code en aval ne peut distinguer quel NER s'est exécuté.

## `count_entities(entities)` — Agrégation de fréquences

```python
def count_entities(entities):
    return Counter(entities)
```

Le `Counter` retourné est indexé par **tuples** `(text, label)`, pas seulement par texte. Important : la même forme de surface peut porter différents labels (`"Cléon"` comme PER et `"Cléon"` comme LOC si une ville porte le nom de l'empereur), et nous voulons les compter indépendamment.

Exemple de sortie :
```python
Counter({
    ("Seldon", "PER"): 47,
    ("Hari Seldon", "PER"): 12,
    ("Trantor", "LOC"): 38,
    ("Cléon", "PER"): 21,
})
```

## `filter_persons(L, anti_dict=None)` — Extraction PER

```python
def filter_persons(L, anti_dict=None):
    if anti_dict is None:
        anti_dict = set()

    persons = Counter()
    for (text, label), count in L.items():
        if label == "PER" and is_valid_entity(text):
            norm = text.strip().lower()
            if norm not in anti_dict:
                persons[text] = persons[text] + count
    return persons
```

Étapes :
1. Garder seulement `label == "PER"`.
2. Rejeter via `is_valid_entity()` (longueur, casse, traits d'union).
3. Normaliser en minuscules et vérifier contre l'`anti_dict` fourni par l'utilisateur.
4. Forme de surface préservée en sortie (clé sensible à la casse) — la résolution d'alias canonicalisera plus tard.

Noter que la chaîne de label est `"PER"`, **pas** `"PERSON"`. Les modèles français de spaCy utilisent `PER`. Le NER par règles émet aussi `PER` pour rester compatible.

## `filter_locations(L)` — Extraction LOC

```python
def filter_locations(L):
    locations = Counter()
    for (text, label), count in L.items():
        if label in ("LOC", "GPE") and is_valid_entity(text):
            locations[text] = locations[text] + count
    return locations
```

Accepte à la fois `LOC` (lieu général) et `GPE` (entité géopolitique — pays, villes). spaCy les sépare ; le NER par règles n'émet que `LOC`. Même filtre `is_valid_entity` s'applique. Pas d'`anti_dict` ici car les faux positifs de lieux sont plus rares et le gazetteer est déjà soigné.

## `is_valid_entity(text)` — Règle de validité partagée

Le filtre le plus appelé du pipeline. Règles, dans l'ordre :

```python
_SHORT_NAME_WHITELIST = {
    "Pel", "Bay", "Ben", "Bel", "Eto", "Kal",
}

def is_valid_entity(text: str):
    t = text.strip()
    if not t:                                          return False  # vide
    if len(t) == 1:                                    return False  # "A", "X"
    if len(t) == 2 and t not in _SHORT_NAME_WHITELIST: return False  # "Or", "Eh"
    if t.isupper():                                    return False  # "ONU", "USA"
    if re.fullmatch(r"[A-Z\s]+", t):                   return False  # "HELLO WORLD"
    if "-" in t or "–" in t or "?" in t or '"' in t:   return False  # ponctuation
    return True
```

### Pourquoi la liste blanche ?

Asimov utilise plusieurs alias légitimes de 2 caractères (`Pel` pour `Janov Pelorat`, `Bay` pour `Bayta Darell`, `Eto` pour `Eto Demerzel`). Sans la liste blanche, la règle de longueur 2 les éliminerait, cassant la résolution d'alias.

### Pourquoi rejeter les majuscules totales ?

Acronymes (`ONU`, `USA`, `GNA`) et dialogues criés (`"NON !"`) sont des faux positifs courants. Le double contrôle (`isupper()` plus la regex `[A-Z\s]+`) capture les cas mono-token et multi-token.

### Pourquoi rejeter les traits d'union ?

Deux raisons :
1. Les mots français courants à trait d'union (`peut-être`, `grand-père`) se capitalisent en début de phrase.
2. La plupart des noms légitimes à trait d'union (`Jean-Pierre`) finissent quand même comme entités multi-mots via l'heuristique de capitalisation, appariées en `["Jean", "Pierre"]`.

La règle cause un faux négatif connu : `Maître-du-Soleil Quatorze` (un ancien Mycogénien) est rejeté par cette vérification, donc ajouté explicitement à `ASIMOV_CHARACTERS` pour contourner via le gazetteer.

## Position dans le pipeline

```
manual_extract_entities()  →  list[(text, label)]
                                    ↓
                              count_entities()
                                    ↓
                                 Counter
                                    ↓
              ┌──────────────────────┴──────────────────────┐
              ↓                                             ↓
       filter_persons()                            filter_locations()
              ↓                                             ↓
              LP                                            LL
              ↓
       group_aliases (nlp_aliases.py)
              ↓
       merge_alias_counts
              ↓
       filter_by_frequency
              ↓
       detect_cooccurrences (nlp_cooccurrence.py)
```

## Utilisation dans le notebook

```python
from nlp_extract_characters import count_entities, filter_persons, filter_locations

raw_entities = manual_extract_entities(text, ...)
L  = count_entities(raw_entities)
LP = filter_persons(L, anti_dict=anti_dict)
LL = filter_locations(L)

ner_cache[chapter_id] = {'text': text, 'L': L, 'LP': LP, 'LL': LL}
```

Le cache stocke les trois car les changements de paramètres alias/co-occurrence ne devraient pas déclencher une ré-extraction NER. Seul `LP` entre dans le pipeline d'alias ; `LL` est réservé pour de futures fonctionnalités sensibles aux lieux (actuellement non utilisé dans la génération du graphe).

## Ajustement pour d'autres langues

- **Codes de label** — les modèles anglais de spaCy utilisent `PERSON`, pas `PER`. Pour utiliser ce module avec un NER anglais, changer la comparaison dans `filter_persons` ou pré-traiter la liste d'entités.
- **Liste blanche** — alias de 2 caractères spécifiques à la langue. Les textes anglais ont probablement besoin de `{"Ed", "Al", "Bo"}` ou similaire.
- **Validité** — certains noms contiennent légitimement `-` (`Anne-Marie`, `Jean-Luc`). Assouplir la vérification du trait d'union si votre texte en a beaucoup.

## Modes d'échec

- Doublons de casse en surface (`"seldon"` minuscule depuis une faute, `"Seldon"` propre) deviennent des **entrées séparées** dans `LP`. Le regroupement d'alias gère la plupart via `normalize_name()` dans `nlp_aliases.py`, mais les fautes qui ne se normalisent pas identiquement passent à travers.
- Arithmétique `Counter` `persons[text] = persons[text] + count` équivalente à `persons[text] += count` — écrite en forme longue pour clarté, aucune différence sémantique.

## Exemple détaillé

Entrée depuis `manual_extract_entities` :
```python
raw = [
    ("Hari Seldon", "PER"),
    ("Hari Seldon", "PER"),
    ("Seldon",      "PER"),
    ("Trantor",     "LOC"),
    ("ONU",         "PER"),       # acronyme → rejeté
    ("J",           "PER"),       # caractère unique → rejeté
    ("Or",          "PER"),       # 2 caractères, pas en liste blanche → rejeté
    ("Eto",         "PER"),       # 2 caractères, en liste blanche → conservé
    ("Jean-Pierre", "PER"),       # trait d'union → rejeté
    ("le seldon",   "PER"),       # dans anti_dict → rejeté
]

L = count_entities(raw)
# Counter({
#     ("Hari Seldon", "PER"): 2,
#     ("Seldon", "PER"): 1,
#     ("Trantor", "LOC"): 1,
#     ("ONU", "PER"): 1,
#     ("J", "PER"): 1,
#     ("Or", "PER"): 1,
#     ("Eto", "PER"): 1,
#     ("Jean-Pierre", "PER"): 1,
#     ("le seldon", "PER"): 1,
# })

LP = filter_persons(L, anti_dict={"le seldon"})
# Counter({
#     "Hari Seldon": 2,
#     "Seldon": 1,
#     "Eto": 1,
# })

LL = filter_locations(L)
# Counter({"Trantor": 1})
```

`"ONU"`, `"J"`, `"Or"`, `"Jean-Pierre"` tous éliminés par `is_valid_entity`. `"le seldon"` éliminé par la vérification `anti_dict`. `"Eto"` survit car dans `_SHORT_NAME_WHITELIST`.

## Performance

Les quatre fonctions sont des opérations Python pures sur `Counter` et dict — pas d'I/O, pas d'appels de modèle. Un chapitre de 50 Ko avec ~20 entités brutes traverse cette étape bien en dessous de la milliseconde. Le travail coûteux s'est fait en amont dans le NER.

## Pourquoi garder le chemin spaCy

Deux scénarios où le NER IA bat le NER par règles :

1. **Bootstrap d'un nouveau gazetteer** — exécuter spaCy une fois sur un échantillon, récolter les noms, les organiser dans un dict style `ASIMOV_CHARACTERS`, puis basculer en règles pour les exécutions de production.
2. **Validation** — comparer la sortie du NER par règles à celle de spaCy pour détecter les manques du gazetteer. Les noms que spaCy trouve mais que les règles manquent sont candidats à ajouter au gazetteer.

Le chargeur paresseux rend le chemin optionnel peu coûteux : zéro coût si vous n'appelez jamais `extract_entities`, chargement complet du modèle au premier appel.

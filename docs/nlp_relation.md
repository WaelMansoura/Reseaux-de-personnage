# `nlp_relation.py` — Étiquetage de relations par analyse de sentiment

## Objectif

Étiqueter chaque paire de personnages co-occurrents avec un des trois types de relation — **friendly**, **hostile** ou **neutral** — en exécutant une analyse de sentiment sur les extraits de texte où ils apparaissent ensemble. La sortie pilote les couleurs d'arêtes dans la visualisation HTML finale (vert / rouge / gris).

Le seul composant à modèle d'IA du pipeline par règles. Utilise `cardiffnlp/twitter-xlm-roberta-base-sentiment` (sentiment multilingue) au niveau de l'extrait, puis agrège les votes sur tous les contextes de co-occurrence d'une paire.

## Choix du modèle

```python
_tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-xlm-roberta-base-sentiment")
_model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-xlm-roberta-base-sentiment")
```

Pourquoi ce modèle :
- **Multilingue** — gère le français sans fine-tuning spécifique au français.
- **Basé sentiment** — bien moins coûteux que le NLI zero-shot (approche originale, supprimée lors du nettoyage de code).
- Sortie **3 classes** : negative / neutral / positive, mappée directement à hostile / neutral / friendly.

Chargé à l'import du module — premier import déclenche un téléchargement de ~500 Mo. Le notebook le mentionne explicitement dans la cellule `2abc79af` et persiste les résultats via `relation_cache.pkl` pour éviter de relancer.

## Extraction d'extraits — `extract_cooccurrence_contexts`

Pour une paire `(charA, charB)`, trouver chaque région de texte où ils apparaissent à moins de `distance_max` tokens l'un de l'autre :

```python
def extract_cooccurrence_contexts(text, charA, charB, alias_map,
                                  distance_max=100,
                                  max_contexts=MAX_CONTEXTS_PER_PAIR):
    aliases_A = {sf for sf, canon in alias_map.items() if canon == charA} | {charA}
    aliases_B = {sf for sf, canon in alias_map.items() if canon == charB} | {charB}

    token_matches = list(re.finditer(r"\S+", text))
    token_texts_lower = [m.group().lower() for m in token_matches]
    n = len(token_matches)

    def find_positions(aliases: set) -> List[int]:
        positions = []
        for alias in aliases:
            alias_tokens = alias.lower().split()
            alen = len(alias_tokens)
            for i in range(n - alen + 1):
                if token_texts_lower[i : i + alen] == alias_tokens:
                    positions.append(i)
        return sorted(set(positions))

    pos_A = find_positions(aliases_A)
    pos_B = find_positions(aliases_B)

    contexts: List[str] = []
    used_windows: set = set()

    for a in pos_A:
        for b in pos_B:
            if abs(a - b) <= distance_max:
                win_start = min(a, b)
                win_end = max(a, b) + 1
                window_key = (win_start, win_end)
                if window_key in used_windows:
                    continue
                used_windows.add(window_key)
                char_start = token_matches[win_start].start()
                char_end = token_matches[min(win_end, n - 1)].end()
                snippet = text[char_start:char_end].strip()
                contexts.append(snippet)
                if len(contexts) >= max_contexts:
                    return contexts
    return contexts
```

Diffère de `nlp_cooccurrence.detect_cooccurrences` de trois façons :

1. **Tous les alias de chaque personnage** sont cherchés, pas seulement le nom canonique. Nécessaire car le texte brut contient `"Empereur"`, pas `"Cléon"`.
2. **Retourne des extraits de texte**, pas des comptes. Chaque extrait commence à la mention antérieure et se termine à la postérieure.
3. **Plafonné à `MAX_CONTEXTS_PER_PAIR = 5`** — la classification de sentiment est le goulot, plus d'extraits par paire = exécution plus lente pour un gain marginal.

Le tokeniseur ici est `r"\S+"` (séparation par espaces, garde la ponctuation), pas `r"\w+"`. Différent de `nlp_cooccurrence` car ici on veut **redécouper le texte original**, donc les offsets de tokens doivent pointer sur les spans sources exacts.

## Classification — `classify_relationship`

```python
def classify_relationship(context_snippets: list, charA: str, charB: str) -> str:
    if not context_snippets:
        return "neutral"

    votes = []
    for snippet in context_snippets:
        text = f"{charA} et {charB}: {snippet[:400]}"
        tokens = _tokenizer(text, return_tensors="pt", truncation=True)
        output = _model(**tokens)
        scores = softmax(output.logits.detach().numpy()[0])
        sentiment_score = scores[2] - scores[0]  # positif - négatif
        if sentiment_score > 0.1:
            votes.append(("friendly", abs(sentiment_score)))
        elif sentiment_score < -0.1:
            votes.append(("hostile", abs(sentiment_score)))
        else:
            votes.append(("neutral", abs(sentiment_score)))

    totals = {"friendly": 0, "hostile": 0, "neutral": 0}
    for label, weight in votes:
        totals[label] += weight
    winner = max(totals, key=totals.get)
    return winner
```

Deux choix de conception :

### Préfixe `f"{charA} et {charB}: "`

Ajoute les noms des personnages à l'entrée pour que le modèle ancre le sentiment sur leur interaction plutôt que de noter l'humeur de tout l'extrait. Un extrait décrivant un festival joyeux où deux ennemis se rencontrent par hasard ne devrait *pas* se lire comme « friendly » — le préfixe pousse le modèle à juger la **paire**, pas la scène.

### Seuil ±0,1 sur `pos - neg`

Sous magnitude 0,1 → neutral. Au-dessus → friendly/hostile. Cela capture la certitude du modèle : un positif fort (`scores=[0.05, 0.1, 0.85]`) donne `score=0.80`, définitivement friendly. Un signal faible (`scores=[0.3, 0.4, 0.3]`) donne `score=0.0`, neutral.

### Troncature d'extrait `[:400]`

Plafond strict. Les modèles de sentiment se dégradent au-delà de leur longueur de fine-tuning (~512 tokens). La plupart des extraits sont bien sous 400 caractères de toute façon.

### Majorité pondérée

Chaque vote pondéré par `abs(sentiment_score)`. Un hostile confiant (poids 0,8) l'emporte sur trois neutres faibles (poids 0,05 chacun). Le gagnant prend le label qui accumule le plus de poids.

## Orchestrateur de haut niveau — `label_relationships`

```python
def label_relationships(text, cooccurrences, alias_map,
                        distance_max=100, chapter_id="", cache=None):
    edge_labels: Dict[tuple, str] = {}
    new_pairs = 0
    for (charA, charB) in cooccurrences:
        canon_pair = tuple(sorted([charA, charB]))
        cache_key = (chapter_id,) + canon_pair

        if cache is not None and cache_key in cache:
            edge_labels[(charA, charB)] = cache[cache_key]
            continue

        snippets = extract_cooccurrence_contexts(text, charA, charB, alias_map, distance_max)
        label = classify_relationship(snippets, charA, charB)
        edge_labels[(charA, charB)] = label
        new_pairs += 1
        if cache is not None:
            cache[cache_key] = label

    if new_pairs > 0:
        print(f"   🏷️  Labeled {new_pairs} new pairs", end="  ")
    return edge_labels
```

### Clé de cache

`(chapter_id, charA_trié, charB_trié)`. La portée par chapitre compte car la *même* paire dans différents chapitres a souvent des dynamiques de relation différentes (Cléon-Demerzel évolue à travers le livre). Le tri garantit que `(A,B)` et `(B,A)` se ramènent à une entrée.

### Invalidation du cache

La cellule `9844e056` du notebook documente :

> Changer `distance_max` ne nécessite PAS de vider ce cache.
> Vider seulement si vous changez le modèle de sentiment ou les seuils de classification.

Le cache stocke des labels finaux, pas des scores intermédiaires. Des fenêtres plus grandes signifient des extraits différents, mais le cache est indexé avant l'extraction d'extraits, donc il court-circuite.

## Rapport de validation — `print_validation_report`

Vérification ponctuelle de la qualité des labels sur un seul chapitre :

```python
print_validation_report(
    text=ner_cache["paf0"]["text"],
    edge_labels=edge_labels_per_chapter["paf0"],
    alias_map=alias_map_per_chapter["paf0"],
    distance_max=150,
    chapter_id="paf0",
    n=5,
)
```

Sortie (depuis la cellule `e142e187` du notebook) :
```
== VALIDATION REPORT — chapter paf0 ==
Total edges: 6  |  friendly: 1  hostile: 5  neutral: 0
── HOSTILE ──
  Cléon ↔ Demerzel
  « Cléon était empereur depuis dix ans à peine ... »
── FRIENDLY ──
  Demerzel ↔ Hummin
  « Hummin esquissa un haussement d'épaules. « Eto Demerzel... »
```

Utile pour détecter les biais systématiques. Les résultats du notebook montrent un **biais hostile lourd** (239 hostiles vs 58 friendly à travers 37 chapitres) — le sentiment de la prose dramatique française tend à enregistrer du négatif même pour des personnages amicaux car le *texte* décrit conflit, peur, anxiété peu importe qui est impliqué.

## Problèmes connus

- **Biais hostile** ci-dessus. Options de mitigation : ajouter une calibration par chapitre, élever le seuil ±0,1, réintroduire un seuil de confiance en repli vers `neutral`, ou basculer en NLI avec des prompts spécifiques friendly.
- **Paires à extrait unique** obtiennent le label que l'extrait isolé implique — fragile.
- **Préfixe de texte `et`** spécifique au français. Pour textes anglais, changer en `"and"`.
- Le modèle **ne peut détecter sarcasme ou ironie**. Une insulte amicale entre alliés se lira comme hostile.

## Câblage dans le notebook

```python
edge_labels = label_relationships(
    text, cooccurrences, alias_map,
    distance_max=distance_max,
    chapter_id=chapter_id,
    cache=relation_cache,
)
```

Cache persisté via `pickle.dump(relation_cache, f)` après chaque exécution réussie. Les `edge_labels` de chaque chapitre stockés séparément dans `edge_labels_per_chapter[chapter_id]` pour inspection ultérieure.

Performance : l'exécution des 37 chapitres a pris **~470 secondes** dans le log du notebook (`Time: 470.57s`). Avec hits de cache aux ré-exécutions, descend à quelques secondes.

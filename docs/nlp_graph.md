# `nlp_graph.py` — Construction de graphe NetworkX

## Objectif

Prendre les sorties de chaque étape précédente — comptes de personnages, paires de co-occurrence, carte d'alias, labels d'arêtes — et les assembler en un `networkx.Graph` qui satisfait le **format de soumission** : GraphML avec attributs de nœud `names` et attributs d'arête `edge_type` optionnels.

Trois fonctions : `generate_graph` (construction), `remove_isolated_nodes` (élagage), `save_graphml` (écriture). Plus une aide de visualisation matplotlib non utilisée dans le pipeline de production.

## Contrat de sortie

La soumission attend que chaque nœud ait un attribut `names` = formes de surface jointes par point-virgule (canonique en premier), et chaque arête ait un `weight` (compte de co-occurrence) plus optionnellement un `edge_type`.

Échantillon de nœud exporté depuis la validation du notebook :
```
Demerzel: Demerzel;Eto Demerzel
Seldon:   Seldon;Hari Seldon
Cléon:    Cléon;Sire;Empereur;l'Empereur;L'Empereur;Cléon Ier
```

## `generate_graph` — Constructeur principal

```python
def generate_graph(cooccurrences, character_counts,
                   alias_map=None, edge_labels=None):
    G = nx.Graph()

    canonical_to_surfaces: dict[str, list[str]] = {}
    if alias_map:
        for surface, canonical in alias_map.items():
            canonical_to_surfaces.setdefault(canonical, []).append(surface)

    for character, count in character_counts.items():
        G.add_node(character, count=count)
        surfaces = canonical_to_surfaces.get(character, [])
        all_names = [character] + [s for s in surfaces if s != character]
        G.nodes[character]["names"] = ";".join(all_names)

    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            G.add_edge(char1, char2, weight=weight)
            if edge_labels:
                etype = (
                    edge_labels.get((char1, char2))
                    or edge_labels.get((char2, char1))
                    or "neutral"
                )
                G[char1][char2]["edge_type"] = etype

    return G
```

### Structure en trois passes

1. **Carte d'alias inverse** : construire `canonique → [surface, surface, ...]` pour recherche rapide. La carte d'alias va dans une seule direction (`surface → canonique`), mais les nœuds du graphe doivent connaître tous leurs alias.
2. **Ajouter les nœuds** : chaque entrée de `character_counts` devient un nœud avec un attribut `count` et un attribut `names`.
3. **Ajouter les arêtes** : parcourir `cooccurrences`, ajouter seulement les arêtes où **les deux extrémités** sont dans le graphe. Les paires filtrées par `min_occurrences` sont éliminées ici.

### Construction de l'attribut `names`

```python
all_names = [character] + [s for s in surfaces if s != character]
G.nodes[character]["names"] = ";".join(all_names)
```

Le nom canonique est toujours en premier. Doublons exclus (le canonique peut apparaître redondamment dans la liste `surfaces`). Résultat : la chaîne déterministe séparée par point-virgule attendue par la soumission.

### Recherche bidirectionnelle de label d'arête

```python
etype = (
    edge_labels.get((char1, char2))
    or edge_labels.get((char2, char1))
    or "neutral"
)
```

`label_relationships` retourne les labels indexés dans l'ordre où `cooccurrences` a été itéré. Les clés de co-occurrence sortent dans l'ordre `tuple(sorted(...))` de `nlp_cooccurrence`, mais `cooccurrences.items()` ne garantit pas cet ordre au moment de l'itération. La chaîne de repli gère les deux directions. `"neutral"` par défaut si le label manque entièrement (ne devrait pas arriver, mais sûr).

### Pourquoi filtrer les arêtes par appartenance des nœuds

`if char1 in G.nodes and char2 in G.nodes:` — c'est le gardien qui applique le filtrage par fréquence. Le notebook appelle :

```python
LP_merged = filter_by_frequency(LP_merged, min_occurrences)  # élimine les noms à compte faible
cooccurrences = detect_cooccurrences(text, LP_merged, distance_max)
G = generate_graph(cooccurrences, LP_merged, ...)
```

`detect_cooccurrences` ne voit que `LP_merged`, donc par construction aucune co-occurrence ne référence un personnage filtré. Le contrôle d'appartenance est défensif — si jamais vous passez un `cooccurrences` Counter d'un autre `LP`, ça ne crashe pas, ça abandonne silencieusement les non-correspondances.

## `remove_isolated_nodes` — Élagage

```python
def remove_isolated_nodes(G):
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    return G
```

Supprime les nœuds de degré 0 (sans arêtes). Ce sont les personnages qui ont passé NER et filtres de fréquence mais ne co-apparaissent jamais avec personne — généralement mentionnés dans la narration/récap plutôt qu'en présence de scène.

Modification en place + retour pour chaînage. Le notebook rapporte le compte :

```python
nodes_before = G.number_of_nodes()
remove_isolated_nodes(G)
nodes_removed = nodes_before - G.number_of_nodes()
```

## `save_graphml` — Écriture sur disque

```python
def save_graphml(G, filename):
    nx.write_graphml(G, filename)
    print(f"✓ Graph saved to {filename}")
```

Wrapper léger. **Non utilisé par le notebook** — le notebook construit la chaîne GraphML en mémoire :

```python
graphml_str = "".join(nx.generate_graphml(G))
graphml_str = html.unescape(graphml_str)
```

Puis la stocke comme cellule CSV. `html.unescape` est critique : NetworkX échappe en HTML les `'` et autres caractères dans les valeurs d'attributs, mais le validateur de soumission attend de l'Unicode brut. Sans unescape, `"l'Empereur"` devient `"l&apos;Empereur"` dans la sortie et casse le parsing en aval.

## `visualize_graph` — Matplotlib (non utilisé dans le pipeline)

Implémentation de référence, conservée pour inspection ad hoc :

```python
def visualize_graph(G, title="Character Network", top_n=30):
    degrees = dict(G.degree())
    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:top_n]
    G_sub = G.subgraph(top_nodes)
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G_sub, k=0.5, iterations=50)
    node_sizes = [300 + 50 * degrees[node] for node in G_sub.nodes()]
    edge_widths = [0.5 + G_sub[u][v]['weight'] * 0.2 for u, v in G_sub.edges()]
    nx.draw_networkx_nodes(G_sub, pos, node_size=node_sizes,
                           node_color='lightblue', alpha=0.9)
    nx.draw_networkx_edges(G_sub, pos, width=edge_widths,
                           alpha=0.5, edge_color='gray')
    nx.draw_networkx_labels(G_sub, pos, font_size=9, font_weight='bold')
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
```

Le filtre `top_n` empêche matplotlib de s'étouffer sur des graphes denses. Le layout par ressorts (force-dirigé) donne des clusters lisibles. Taille de nœud proportionnelle au degré, largeur d'arête proportionnelle au poids. Le notebook préfère PyVis (HTML interactif) donc ceci n'est jamais appelé là — utile pour développer en Python pur.

## Pipeline du notebook

```python
# Construire les labels d'arêtes
edge_labels = label_relationships(
    text, cooccurrences, alias_map,
    distance_max=distance_max,
    chapter_id=chapter_id,
    cache=relation_cache,
)

# Construire le graphe
G = generate_graph(
    cooccurrences,
    LP_merged,
    alias_map=alias_map,
    edge_labels=edge_labels,
)

# Élaguer
nodes_before = G.number_of_nodes()
remove_isolated_nodes(G)
nodes_removed = nodes_before - G.number_of_nodes()

# Sérialiser
graphml_str = "".join(nx.generate_graphml(G))
graphml_str = html.unescape(graphml_str)
submission_data.append({'ID': chapter_id, 'graphml': graphml_str})
```

Par chapitre, sortie stockée dans un CSV avec lignes `(chapter_id, graphml_string)`. Écriture finale :

```python
df_submission = pd.DataFrame(submission_data)
df_submission.set_index('ID', inplace=True)
df_submission.to_csv(output_csv, encoding='utf-8')
```

Forme typique : 37 entrées, chacune avec une chaîne XML graphml entre ~1 et 5 Ko.

## Échantillon de sortie GraphML

Pour le chapitre `paf0` (4 nœuds, 6 arêtes) :

```xml
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="count"     attr.type="long"/>
  <key id="d1" for="node" attr.name="names"     attr.type="string"/>
  <key id="d2" for="edge" attr.name="weight"    attr.type="long"/>
  <key id="d3" for="edge" attr.name="edge_type" attr.type="string"/>
  <graph edgedefault="undirected">
    <node id="Demerzel">
      <data key="d0">23</data>
      <data key="d1">Demerzel;Eto Demerzel</data>
    </node>
    <node id="Cléon">
      <data key="d0">31</data>
      <data key="d1">Cléon;Sire;Empereur;l'Empereur;Cléon Ier</data>
    </node>
    ...
    <edge source="Cléon" target="Demerzel">
      <data key="d2">47</data>
      <data key="d3">hostile</data>
    </edge>
    ...
  </graph>
</graphml>
```

## Modes d'échec

- **`alias_map` obsolète** référençant des canoniques absents de `character_counts` — produit silencieusement des listes `surfaces` vides, pas de crash.
- **Arête vers nœud inexistant** — silencieusement sautée par le contrôle d'appartenance ; déboguer en comparant `cooccurrences.keys()` à `G.nodes()`.
- **Boucles sur soi** — `cooccurrences` ne devrait pas contenir `(a, a)` car `nlp_cooccurrence` utilise `combinations` (sans répétitions), mais s'il en contenait, NetworkX ajouterait joyeusement une arête sur soi.
- **Échappement HTML** — toujours `html.unescape` après `nx.generate_graphml` pour le texte non-ASCII.

## Ajustements

Pour des graphes orientés, changer `G = nx.Graph()` en `G = nx.DiGraph()` — mais la co-occurrence est symétrique par construction, donc non orienté est correct.

Pour ajouter plus d'attributs de nœuds (par ex. degré, centralité d'intermédiarité), les calculer après `remove_isolated_nodes` et assigner :

```python
for node, val in nx.betweenness_centrality(G).items():
    G.nodes[node]["betweenness"] = val
```

L'export GraphML reprend automatiquement les nouveaux attributs.

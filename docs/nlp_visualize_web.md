# `nlp_visualize_web.py` — Visualisation HTML interactive

## Objectif

Rendre les réseaux de personnages comme pages HTML interactives en utilisant PyVis (un wrapper Python de `vis.js`). Deux modes de sortie :

1. **Chapitre unique** : un HTML par graphe, s'ouvre dans le navigateur immédiatement.
2. **Combiné** : tous les chapitres dans un HTML avec une barre latérale pour naviguer entre eux.

Arêtes colorées par `edge_type` : vert (friendly), rouge (hostile), gris (neutral). La taille de nœud croît avec le nombre de mentions. Tout simulé par physique pour layout auto-organisé.

## Palette de couleurs

```python
_EDGE_COLORS = {
    "friendly": "#27ae60",   # vert
    "hostile":  "#e74c3c",   # rouge
    "neutral":  "#95a5a6",   # gris
}
```

Les mêmes trois teintes utilisées dans la documentation/légende de `nlp_relation.py`. Les valeurs hex correspondent aux pastilles de légende dans la barre supérieure du HTML combiné.

## `create_interactive_graph` — Mode fichier unique

```python
def create_interactive_graph(G, cooccurrences, output_file="graph.html"):
    net = Network(height="750px", width="100%",
                  notebook=False, directed=False)

    for node in G.nodes():
        count = G.nodes[node].get('count', 1)
        net.add_node(
            node,
            label=node,
            size=10 + count * 0.5,
            title=f"{node}: {count} mentions"
        )

    for (char1, char2), weight in cooccurrences.items():
        if char1 in G.nodes and char2 in G.nodes:
            edge_data = G.get_edge_data(char1, char2, default={})
            edge_type = edge_data.get("edge_type", "neutral")
            color     = _EDGE_COLORS.get(edge_type, _EDGE_COLORS["neutral"])
            net.add_edge(
                char1, char2,
                value=weight,
                title=f"{weight} co-occurrences | {edge_type}",
                color=color,
            )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": { "iterations": 200 }
      }
    }
    """)
    net.write_html(output_file)
    print(f"✓ Interactive graph saved to {output_file}")
    webbrowser.open(output_file)
```

### Dimensionnement de nœud

`size=10 + count * 0.5` — un personnage avec 50 mentions obtient taille 35, le protagoniste avec 200 mentions obtient taille 110. Échelle linéaire, plafonnée seulement par lisibilité (PyVis rend les tailles >150 comme encombrées).

### Tooltips au survol

`title=` peuple le tooltip de survol :
- Nœuds : `"Cléon: 47 mentions"`
- Arêtes : `"23 co-occurrences | hostile"`

PyVis échappe en HTML pour la sécurité, pas besoin de pré-échapper.

### Stabilisation physique

200 itérations est le sweet spot :
- 50 : nœuds dérivent encore à la première vue.
- 200 : layout stable, démarrage ~1 seconde.
- 500 : indistinguable de 200, chargement plus lent.

Après stabilisation, la physique reste *activée* — glissez un nœud et le layout répond. Mettre `"enabled": false` pour positions statiques.

### Effet de bord `webbrowser.open`

Ouvre le fichier dans le navigateur par défaut. Utile en scripts, **agaçant** dans les notebooks (chaque appel ouvre un onglet). La fonction de mode combiné ne fait délibérément pas cela.

## `_build_network_html` — Aide interne

Même logique que la fonction publique mais retourne la chaîne HTML au lieu d'écrire sur disque :

```python
def _build_network_html(G, cooccurrences):
    net = Network(height="100vh", width="100%", notebook=False, directed=False)
    # ... même construction de nœuds/arêtes ...
    net.set_options(_PHYSICS_OPTIONS)
    return net.generate_html()
```

Deux différences clés par rapport à `create_interactive_graph` :

- `height="100vh"` (viewport complet) au lieu d'un `750px` fixe — la vue combinée remplit l'iframe.
- Retourne la chaîne via `net.generate_html()` au lieu de `net.write_html()`.

C'est la brique de construction pour la vue combinée.

## Vue combinée — `create_combined_html`

La fonction phare. Produit un HTML avec une barre latérale listant tous les chapitres, groupés par livre. Cliquez un chapitre, son réseau apparaît dans la zone principale.

### Format d'entrée

```python
chapters_data = [
    (chapter_id, G, cooccurrences),                  # 3-tuple
    (chapter_id, G, cooccurrences, label_counts),    # 4-tuple avec stats
]
```

Le 4ᵉ élément (`Counter` de label → compte) alimente l'affichage de stats de la barre supérieure. Optionnel.

### Regroupement par préfixe d'ID de livre

```python
m = re.match(r"([a-zA-Z_]+)", chapter_id)
book_key = m.group(1) if m else "other"
```

`"paf0"` → `"paf"`, `"lca12"` → `"lca"`. Utilisé comme en-têtes de section dans la barre latérale :

```
PAF
  paf0
  paf1
  ...
LCA
  lca0
  lca1
```

Si vos IDs de chapitres ne suivent pas cette convention (par ex. nombres purs `"1"`, `"2"`), tous les chapitres se retrouvent sous `"other"`.

### Chargement paresseux des iframes

Le réseau de chaque chapitre est intégré comme iframe séparé :

```python
inner_html = _build_network_html(G, cooccurrences)
escaped    = inner_html.replace("&", "&amp;").replace('"', "&quot;")
frames_parts.append(
    f'<div class="frame-wrap" id="frame-{chapter_id}">'
    f'<iframe data-srcdoc="{escaped}"></iframe>'
    f'</div>'
)
```

Notez `data-srcdoc` (pas `srcdoc`). Le JavaScript le promeut à `srcdoc` seulement au premier visionnage :

```javascript
function showTab(id) {
  document.querySelectorAll('.frame-wrap').forEach(f => f.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  var fw  = document.getElementById('frame-' + id);
  var btn = document.getElementById('btn-' + id);
  if (!fw || !btn) return;
  var iframe = fw.querySelector('iframe');
  if (iframe && !iframe.hasAttribute('srcdoc') && iframe.dataset.srcdoc) {
    iframe.srcdoc = iframe.dataset.srcdoc;
  }
  fw.classList.add('active');
  btn.classList.add('active');
  ...
}
```

Pourquoi ça compte : `vis.js` mesure les dimensions du conteneur pour disposer le graphe. Si 37 iframes s'initialisent au chargement de la page alors qu'un seul est visible, les autres voient des conteneurs `display:none` et se rendent à 0×0. Le chargement paresseux diffère l'initialisation jusqu'à ce que l'iframe devienne visible.

### Stats de la barre supérieure

```javascript
var META = {meta_json};   // injecté au moment du rendu
...
document.getElementById('stats').textContent =
  m.nodes + ' nodes · ' + m.edges + ' edges'
  + (m.friendly !== undefined
     ? '   |   friendly: ' + m.friendly + '  hostile: ' + m.hostile + '  neutral: ' + m.neutral
     : '');
```

Lit depuis un objet JSON généré côté serveur :

```python
mc: dict = {"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}
if label_counts is not None:
    mc["friendly"] = label_counts.get("friendly", 0)
    mc["hostile"]  = label_counts.get("hostile",  0)
    mc["neutral"]  = label_counts.get("neutral",  0)
meta[chapter_id] = mc
```

### Mise en page CSS

```css
body { display: flex; height: 100vh; }
#sidebar { width: 200px; min-width: 160px; overflow-y: auto; }
#main    { flex: 1; display: flex; flex-direction: column; }
.frame-wrap { display: none; flex: 1; }
.frame-wrap.active { display: flex; }
iframe { flex: 1; border: none; width: 100%; min-height: 0; }
```

Mise en page flexbox remplit le viewport. Barre latérale largeur fixe (200px), zone principale s'étend en flex. Le frame actif utilise `display: flex` (pas `block`) pour que l'iframe à l'intérieur remplisse la colonne.

Le `min-height: 0` sur iframe est une correction de quirk flexbox — sans, les iframes ignorent la hauteur du parent et s'étendent à la taille du contenu.

## Template HTML

`_COMBINED_HTML_TEMPLATE` est une f-string Python à chaîne unique avec placeholders `{title}`, `{sidebar_html}`, `{frames_html}`, `{meta_json}`. Le template utilise des accolades doublées (`{{ }}`) pour les accolades CSS/JS littérales — convention de f-string Python.

Rempli via :

```python
combined = _COMBINED_HTML_TEMPLATE.format(
    title        = _html.escape(title),
    sidebar_html = "\n  ".join(sidebar_parts),
    frames_html  = "\n  ".join(frames_parts),
    meta_json    = json.dumps(meta),
)
```

`_html.escape(title)` est le seul endroit où l'échappement explicite est fait — sidebar/frames sont pré-construits avec leur propre échappement.

## Utilisation dans le notebook

Depuis la cellule `FhBuxiQadwvQ` :

```python
chapters_data = []
for chapter_id in df_submission.index:
    graphml_str = df_submission.loc[chapter_id, "graphml"]
    G_vis = nx.read_graphml(io.StringIO(graphml_str))

    cooccurrences_vis = Counter()
    for u, v, data in G_vis.edges(data=True):
        weight = int(float(data.get("weight", 1)))
        cooccurrences_vis[(u, v)] = weight

    label_counts = None
    if chapter_id in edge_labels_per_chapter:
        label_counts = Counter(edge_labels_per_chapter[chapter_id].values())

    chapters_data.append((chapter_id, G_vis, cooccurrences_vis, label_counts))

abs_path = create_combined_html(
    chapters_data,
    output_file=f"all_networks_{distance_max}_min{min_occurrences}.html",
    title=f"Character Networks  (window={distance_max}, min={min_occurrences})",
)
```

Notez l'aller-retour : graphes reconstruits depuis la chaîne GraphML produite plus tôt. Cela garantit que la visualisation correspond **exactement** à ce qui a été soumis — mêmes nœuds, mêmes arêtes, mêmes labels.

## Fichier de sortie

Pour `distance_max=150`, `min_occurrences=2` le notebook produit `all_networks_150_min2.html`. HTML auto-contenu unique, pas de dépendances externes — `vis.js` est groupé en ligne par PyVis. Taille de fichier ~1-3 Mo selon le nombre de chapitres.

Ouvrir dans tout navigateur moderne. Cliquer entrée de barre latérale → graphe apparaît. Glisser les nœuds pour explorer. Survoler pour tooltips.

## Ajustements

### Couleurs personnalisées

```python
_EDGE_COLORS["friendly"] = "#3498db"  # bleu au lieu de vert
```

### Nœuds plus grands

Ajuster la formule à la fois dans `create_interactive_graph` et `_build_network_html` :
```python
size=20 + count * 1.0,  # plus gros et plus pentu
```

### Layout hiérarchique

Remplacer les options de physique :
```python
net.set_options("""
{ "layout": { "hierarchical": { "enabled": true, "direction": "UD" } } }
""")
```

### Layout statique (sans physique)

Mettre `"enabled": false`. Glisser les nœuds pour réarranger, mais ils ne se repoussent pas.

## Modes d'échec

- **`chapters_data` vide** — produit une barre latérale sans boutons, zone principale vide. Pas une erreur, juste inutile.
- **ID de chapitre sans préfixe alphabétique** (par ex. `"42"`) — tombe sous la section livre `"other"`.
- **Collisions d'échappement d'iframe** — le remplacement `&` → `&amp;` puis `"` → `&quot;` est sensible à l'ordre (`&` d'abord !). Ne pas réordonner.
- **CORS de navigateur pour fichiers locaux** — l'ouverture depuis `file://` fonctionne dans tous les navigateurs car le contenu de l'iframe est `srcdoc`, pas une URL distante. Pas de problèmes CORS.
- **Grands graphes (>50 nœuds)** — la simulation physique devient lente. Envisager d'élever `min_occurrences` ou de pré-tronquer aux top-N par degré.

# Cahier des Charges - Projet Extraction automatique de réseaux de personnages

## 1. Contexte et Objectifs du Projet

### 1.1. Contexte

L'extraction automatique de réseaux de personnages à partir de textes narratifs est une tâche complexe qui combine des techniques de traitement du langage naturel (NLP) et la modélisation graphique.
Ce projet vise à développer un système capable d'identifier les personnages dans un texte, de détecter leurs interactions, et de construire un réseau représentatif des relations entre ces personnages.

### 1.2. Objectifs

- Développer un algorithme d'extraction de personnages à partir de textes narratifs.
- Construire des listes L (toutes entités), LP (personnages), LL (lieux).
- Détecter les cooccurrences de personnages en utilisant la proximité.
- Construire un réseau de personnages basé sur les interactions détectées.

## 2. Périmètre du Projet

### 2.1. Fonctionnalités attendues

- Extraction des entités nommées.
- Filtrage des personnes ( LP )
- Filtrage des lieux ( LL )
- Regroupement d’alias pour chaque personnage.
- Génération du graphe avec NetworkX pour chaque chapitre.
- Détection des interactions entre les personnages.
- Construction et visualisation du réseau de personnages.
- Export CSV des résultats pour plusieurs chapitres

### 2.2. Technologies utilisées

- Langages de programmation : Python.
- Bibliothèques NLP : spaCy, Stanza, Flair.
- Outils de visualisation : NetworkX, Matplotlib.
- antidict.txt pour le filtrage des entités non pertinentes.

## 3. Public Cible

### 3.1. Profil des utilisateurs

- Étudiants en informatique.
- Chercheurs en linguistique computationnelle.
- Développeurs en traitement du langage naturel.

### 3.2. Besoins des utilisateurs

- Outils efficaces pour l'extraction de réseaux de personnages.
- Visualisation claire des réseaux de personnages.

## 4. Scénarios de Tests Utilisateurs

### 4.1. Objectifs des tests

- Valider que les outils d’extraction identifient correctement les personnages importants
- Vérifier la pertinence du regroupement d’alias
- Évaluer la cohérence des co-occurrences détectées

### 4.2. Méthodologie

1 - Sélectionner un ensemble de textes narratifs variés.
2 - Appliquer les outils d’extraction développés.
3 - Comparer les résultats obtenus avec des annotations manuelles.

## 5. Critères de Réussite et Évaluations

### 5.1. Indicateurs de performance (KPI)

- Taux de précision de l'extraction des personnages.
- Score de précision du graphe de personnages par chapitre sur le classement Kaggle.
- Temps de génération du graphe pour chaque chapitre.

### 5.2. Feedback des utilisateurs/professeurs

## 5.2. Feedback des utilisateurs/professeurs

- Utilisation de plusieurs modèles NLP pour extraire les personnages.
- Méthode de vote pour identifier les personnages corrects, plutôt que d'utiliser l'intersection ou l'union.

## 6. Contraintes et Risques

### 6.1. Contraintes techniques

- Limites des modèles NLP pour la reconnaissance des entités nommées.
- Gestion des ambiguïtés dans les noms des personnages.
- Performance et scalabilité pour traiter de grands textes narratifs.
- Fusion des résultats de plusieurs modèles NLP pour améliorer la précision.

### 6.2. Risques potentiels

- Mauvaise détection d’entités à cause du style littéraire
- Difficulté à atteindre un taux de précision élevé.
- Problèmes de performance avec de grands volumes de texte.

## 7. Planning Prévisionnel

### 7.1. Phases du projet

| Phase                                         | Durée      |
| --------------------------------------------- | ---------- |
| Analyse et traitement du corpus               | 2 semaines |
| Développement extraction NER & listes L/LP/LL | 3 semaines |
| Détection des co-occurrences                  | 2 semaines |
| Génération des graphes                        | 2 semaines |
| Ajustements finaux + rapport                  | 1 semaines |

### 7.2. Livrables

- Liste L, LP, LL.
- Graphes de personnages par chapitre.
- CSV des résultats.
- Cahier des charges finalisé.

## 8. Équipe du Projet

- Lotfi ABDALLAH - Développement NLP, extraction NER, listes L/LP/LL
- Wael MANSOURA - Développement détection co-occurrences, génération graphes

## 9. Annexes

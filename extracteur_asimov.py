#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extracteur d'Entités Nommées pour les romans d'Asimov
Master 1 AMS1 - Université d'Avignon
"""

import re
from collections import Counter, defaultdict
from typing import List, Tuple, Set, Dict
import unicodedata

class AsimovNER:
    """Classe principale pour l'extraction d'entités nommées"""
    
    def __init__(self, texte_nettoye: str):
        """
        Initialisation avec le texte nettoyé
        
        Args:
            texte_nettoye: Le texte déjà nettoyé (sans ponctuation excessive, etc.)
        """
        self.texte = texte_nettoye
        self.phrases = self._segmenter_phrases()
        
        # Dictionnaires pour stocker les résultats
        self.unigrammes = Counter()
        self.bigrammes = Counter()
        self.trigrammes = Counter()
        
        # Listes finales
        self.liste_L = []  # Toutes les entités candidates
        self.liste_LP = []  # Personnes
        self.liste_LL = []  # Lieux
        
        # Mots-outils français à exclure
        self.stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'ce', 'cette',
            'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses',
            'notre', 'votre', 'leur', 'leurs', 'il', 'elle', 'on', 'ils', 'elles',
            'je', 'tu', 'nous', 'vous', 'et', 'ou', 'mais', 'donc', 'or', 'ni',
            'car', 'que', 'qui', 'dont', 'où', 'si', 'pour', 'par', 'dans',
            'sur', 'avec', 'sans', 'sous', 'vers', 'chez', 'à', 'en'
        }
        
        # Titres et marqueurs de personnes
        self.titres_personnes = {
            'dr', 'doctor', 'captain', 'general', 'lord', 'lady', 'sir',
            'mr', 'mrs', 'miss', 'ms', 'professor', 'prof', 'mayor',
            'emperor', 'king', 'queen', 'prince', 'princess', 'duke',
            'comte', 'baron', 'ambassadeur', 'ministre', 'président', 'Monsieur'
        }
        
        # Marqueurs de lieux
        self.marqueurs_lieux = {
            'planet', 'planète', 'city', 'ville', 'star', 'étoile',
            'galaxy', 'galaxie', 'system', 'système', 'world', 'monde',
            'foundation', 'empire', 'sector', 'secteur', 'region', 'région',
            'university', 'université', 'library', 'bibliothèque',
            'terminal', 'port', 'station', 'base'
        }
    
    def _segmenter_phrases(self) -> List[str]:
        """Segmente le texte en phrases"""
        # Découpe sur les points, points d'interrogation, exclamation
        phrases = re.split(r'[.!?]+', self.texte)
        return [p.strip() for p in phrases if p.strip()]
    
    def _tokeniser(self, texte: str) -> List[str]:
        """Tokenise un texte en mots"""
        # Garde les mots avec lettres, chiffres et traits d'union
        tokens = re.findall(r'\b[\w\-]+\b', texte)
        return tokens
    
    # ============================================
    # ÉTAPE 1 : CONSTRUCTION DU MODÈLE DE LANGUE
    # ============================================
    
    def construire_modele_langue(self):
        """
        Construit les n-grammes (n=1,2,3) et leurs fréquences
        """
        print("=== Construction du modèle de langue ===")
        
        for phrase in self.phrases:
            tokens = self._tokeniser(phrase)
            
            # Unigrammes (1 mot)
            for token in tokens:
                self.unigrammes[token] += 1
            
            # Bigrammes (2 mots consécutifs)
            for i in range(len(tokens) - 1):
                bigram = f"{tokens[i]} {tokens[i+1]}"
                self.bigrammes[bigram] += 1
            
            # Trigrammes (3 mots consécutifs)
            for i in range(len(tokens) - 2):
                trigram = f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}"
                self.trigrammes[trigram] += 1
        
        print(f"✓ Unigrammes : {len(self.unigrammes)}")
        print(f"✓ Bigrammes : {len(self.bigrammes)}")
        print(f"✓ Trigrammes : {len(self.trigrammes)}")
    
    # ============================================
    # ÉTAPE 2 : EXTRACTION LISTE L (BRUTE)
    # ============================================
    
    def extraire_liste_L(self, freq_min: int = 2):
        """
        Extrait TOUTES les entités candidates sans filtrage sophistiqué
        Critère principal : commence par une majuscule + fréquence minimale
        
        Args:
            freq_min: Fréquence minimale pour considérer un candidat
        """
        print("\n=== Extraction Liste L (entités candidates) ===")
        
        candidats = Counter()
        
        # Extraire depuis les trigrammes
        for trigram, freq in self.trigrammes.items():
            if freq >= freq_min:
                mots = trigram.split()
                # Si le premier mot commence par majuscule
                if mots[0][0].isupper() and len(mots[0]) > 1:
                    # Vérifier que ce n'est pas en début de phrase
                    if not self._est_debut_phrase(trigram):
                        candidats[trigram] = freq
        
        # Extraire depuis les bigrammes
        for bigram, freq in self.bigrammes.items():
            if freq >= freq_min:
                mots = bigram.split()
                if mots[0][0].isupper() and len(mots[0]) > 1:
                    if not self._est_debut_phrase(bigram):
                        candidats[bigram] = freq
        
        # Extraire depuis les unigrammes
        for word, freq in self.unigrammes.items():
            if freq >= freq_min and len(word) > 1:
                if word[0].isupper():
                    # Exclure les mots-outils en majuscule
                    if word.lower() not in self.stopwords:
                        candidats[word] = freq
        
        # Trier par fréquence décroissante
        self.liste_L = sorted(candidats.items(), key=lambda x: x[1], reverse=True)
        
        print(f"✓ {len(self.liste_L)} entités candidates extraites")
        print(f"✓ Top 10: {[e[0] for e in self.liste_L[:10]]}")
    
    def _est_debut_phrase(self, ngram: str) -> bool:
        """Vérifie si un n-gramme apparaît souvent en début de phrase"""
        pattern = r'\.\s+' + re.escape(ngram)
        matches = len(re.findall(pattern, self.texte))
        total = self.texte.count(ngram)
        
        # Si plus de 70% des occurrences sont en début de phrase
        return matches / total > 0.7 if total > 0 else False
    
    # ============================================
    # ÉTAPE 3 : FILTRAGE LISTE LP (PERSONNES)
    # ============================================
    
    def extraire_liste_LP(self):
        """
        Extrait les entités de PERSONNES depuis la liste L
        Utilise des heuristiques basées sur :
        - Titres (Dr., Captain, etc.)
        - Structure des noms (Prénom Nom)
        - Contexte (verbes d'action, pronoms)
        """
        print("\n=== Extraction Liste LP (personnes) ===")
        
        personnes = Counter()
        
        for entite, freq in self.liste_L:
            score = 0
            mots = entite.split()
            
            # HEURISTIQUE 1 : Présence d'un titre
            for mot in mots:
                if mot.lower().rstrip('.') in self.titres_personnes:
                    score += 3
            
            # HEURISTIQUE 2 : Structure Prénom Nom (2 mots avec majuscules)
            if len(mots) == 2:
                if mots[0][0].isupper() and mots[1][0].isupper():
                    if len(mots[0]) > 2 and len(mots[1]) > 2:
                        score += 2
            
            # HEURISTIQUE 3 : Contexte - vérifier si associé à des verbes d'action
            if self._contexte_personne(entite):
                score += 2
            
            # HEURISTIQUE 4 : Ne doit pas être un marqueur de lieu
            if any(marqueur in entite.lower() for marqueur in self.marqueurs_lieux):
                score -= 3
            
            # HEURISTIQUE 5 : Préférer les noms courts (1-3 mots)
            if 1 <= len(mots) <= 3:
                score += 1
            
            # Si le score est positif, c'est probablement une personne
            if score > 0:
                personnes[entite] = freq
        
        self.liste_LP = sorted(personnes.items(), key=lambda x: x[1], reverse=True)
        
        print(f"✓ {len(self.liste_LP)} personnes extraites")
        print(f"✓ Top 10: {[p[0] for p in self.liste_LP[:10]]}")
    
    def _contexte_personne(self, entite: str) -> bool:
        """
        Vérifie si l'entité apparaît dans un contexte de personne
        (suivi de verbes d'action, de pronoms personnels, etc.)
        """
        # Verbes d'action courants associés aux personnes
        verbes_action = ['said', 'dit', 'asked', 'demanda', 'thought', 'pensa',
                        'went', 'alla', 'looked', 'regarda', 'knew', 'savait',
                        'wanted', 'voulait', 'replied', 'répondit']
        
        # Chercher dans le texte les occurrences
        pattern = re.escape(entite) + r'\s+(\w+)'
        matches = re.findall(pattern, self.texte, re.IGNORECASE)
        
        if not matches:
            return False
        
        # Compter combien de fois suivi d'un verbe d'action
        action_count = sum(1 for match in matches if match.lower() in verbes_action)
        
        return action_count / len(matches) > 0.2 if matches else False
    
    # ============================================
    # ÉTAPE 4 : FILTRAGE LISTE LL (LIEUX)
    # ============================================
    
    def extraire_liste_LL(self):
        """
        Extrait les entités de LIEUX depuis la liste L
        Utilise des heuristiques basées sur :
        - Marqueurs de lieux (planet, city, Foundation, etc.)
        - Contexte spatial
        - Exclusion des personnes déjà identifiées
        """
        print("\n=== Extraction Liste LL (lieux) ===")
        
        lieux = Counter()
        personnes_set = {p[0] for p in self.liste_LP}
        
        for entite, freq in self.liste_L:
            # Exclure si déjà identifié comme personne
            if entite in personnes_set:
                continue
            
            score = 0
            
            # HEURISTIQUE 1 : Contient un marqueur de lieu explicite
            if any(marqueur in entite.lower() for marqueur in self.marqueurs_lieux):
                score += 4
            
            # HEURISTIQUE 2 : Contexte spatial (prépositions de lieu)
            if self._contexte_lieu(entite):
                score += 3
            
            # HEURISTIQUE 3 : Noms longs (organisations, institutions)
            mots = entite.split()
            if len(mots) >= 3:
                score += 1
            
            # HEURISTIQUE 4 : Contient des mots comme "of", "de" (ex: "City of Terminus")
            if ' of ' in entite.lower() or ' de ' in entite.lower():
                score += 2
            
            # HEURISTIQUE 5 : Éviter les noms de personnes typiques
            if not self._ressemble_personne(entite):
                score += 1
            
            if score >= 2:
                lieux[entite] = freq
        
        self.liste_LL = sorted(lieux.items(), key=lambda x: x[1], reverse=True)
        
        print(f"✓ {len(self.liste_LL)} lieux extraits")
        print(f"✓ Top 10: {[l[0] for l in self.liste_LL[:10]]}")
    
    def _contexte_lieu(self, entite: str) -> bool:
        """Vérifie si l'entité apparaît dans un contexte spatial"""
        prepositions_lieu = ['in', 'on', 'at', 'to', 'from', 'near', 'around',
                            'dans', 'sur', 'à', 'de', 'vers', 'près']
        
        # Chercher avant et après l'entité
        pattern_avant = r'(\w+)\s+' + re.escape(entite)
        pattern_apres = re.escape(entite) + r'\s+(\w+)'
        
        matches_avant = re.findall(pattern_avant, self.texte, re.IGNORECASE)
        matches_apres = re.findall(pattern_apres, self.texte, re.IGNORECASE)
        
        total = len(matches_avant) + len(matches_apres)
        if total == 0:
            return False
        
        lieu_count = sum(1 for m in matches_avant if m.lower() in prepositions_lieu)
        lieu_count += sum(1 for m in matches_apres if m.lower() in prepositions_lieu)
        
        return lieu_count / total > 0.15
    
    def _ressemble_personne(self, entite: str) -> bool:
        """Vérifie si l'entité ressemble à un nom de personne"""
        mots = entite.split()
        
        # Structure typique : 2 mots courts avec majuscules
        if len(mots) == 2:
            if all(len(m) < 15 and m[0].isupper() for m in mots):
                return True
        
        # Contient un titre de personne
        if any(titre in entite.lower() for titre in self.titres_personnes):
            return True
        
        return False
    
    # ============================================
    # SAUVEGARDE ET STATISTIQUES
    # ============================================
    
    def sauvegarder_resultats(self, prefix="asimov"):
        """Sauvegarde les listes dans des fichiers"""
        print("\n=== Sauvegarde des résultats ===")
        
        # Liste L
        with open(f"{prefix}_liste_L.txt", 'w', encoding='utf-8') as f:
            f.write("# Liste L - Toutes les entités candidates\n")
            f.write(f"# Total: {len(self.liste_L)} entités\n\n")
            for entite, freq in self.liste_L:
                f.write(f"{entite}\t{freq}\n")
        
        # Liste LP (Personnes)
        with open(f"{prefix}_liste_LP.txt", 'w', encoding='utf-8') as f:
            f.write("# Liste LP - Entités de personnes\n")
            f.write(f"# Total: {len(self.liste_LP)} personnes\n\n")
            for entite, freq in self.liste_LP:
                f.write(f"{entite}\t{freq}\n")
        
        # Liste LL (Lieux)
        with open(f"{prefix}_liste_LL.txt", 'w', encoding='utf-8') as f:
            f.write("# Liste LL - Entités de lieux\n")
            f.write(f"# Total: {len(self.liste_LL)} lieux\n\n")
            for entite, freq in self.liste_LL:
                f.write(f"{entite}\t{freq}\n")
        
        print(f"✓ Fichiers sauvegardés : {prefix}_liste_*.txt")
    
    def afficher_statistiques(self):
        """Affiche les statistiques du corpus et des résultats"""
        print("\n" + "="*50)
        print("STATISTIQUES FINALES")
        print("="*50)
        
        nb_mots = sum(self.unigrammes.values())
        nb_phrases = len(self.phrases)
        
        print(f"\nCorpus:")
        print(f"  - Nombre de phrases: {nb_phrases}")
        print(f"  - Nombre total de mots: {nb_mots}")
        print(f"  - Vocabulaire (mots uniques): {len(self.unigrammes)}")
        
        print(f"\nModèle de langue:")
        print(f"  - Unigrammes: {len(self.unigrammes)}")
        print(f"  - Bigrammes: {len(self.bigrammes)}")
        print(f"  - Trigrammes: {len(self.trigrammes)}")
        
        print(f"\nEntités extraites:")
        print(f"  - Liste L (candidats): {len(self.liste_L)}")
        print(f"  - Liste LP (personnes): {len(self.liste_LP)}")
        print(f"  - Liste LL (lieux): {len(self.liste_LL)}")
        
        print(f"\nTop 5 personnes:")
        for i, (nom, freq) in enumerate(self.liste_LP[:5], 1):
            print(f"  {i}. {nom} ({freq} occurrences)")
        
        print(f"\nTop 5 lieux:")
        for i, (lieu, freq) in enumerate(self.liste_LL[:5], 1):
            print(f"  {i}. {lieu} ({freq} occurrences)")


# ============================================
# FONCTION PRINCIPALE D'UTILISATION
# ============================================

def main():
    """
    Fonction principale pour exécuter l'extraction
    """
    print("="*50)
    print("EXTRACTEUR D'ENTITÉS NOMMÉES - ASIMOV")
    print("="*50)
    
    # ÉTAPE 0 : Charger ton texte nettoyé
    print("\nChargement du texte...")
    with open('asimov_nettoye.txt', 'r', encoding='utf-8') as f:
        texte = f.read()
    
    print(f"✓ Texte chargé : {len(texte)} caractères")
    
    # Créer l'extracteur
    extracteur = AsimovNER(texte)
    
    # ÉTAPE 1 : Construire le modèle de langue
    extracteur.construire_modele_langue()
    
    # ÉTAPE 2 : Extraire liste L (brute)
    extracteur.extraire_liste_L(freq_min=3)  # Ajuste freq_min selon tes besoins
    
    # ÉTAPE 3 : Extraire liste LP (personnes)
    extracteur.extraire_liste_LP()
    
    # ÉTAPE 4 : Extraire liste LL (lieux)
    extracteur.extraire_liste_LL()
    
    # Sauvegarder les résultats
    extracteur.sauvegarder_resultats()
    
    # Afficher les statistiques
    extracteur.afficher_statistiques()
    
    print("\n✓ Traitement terminé avec succès!")


if __name__ == "__main__":
    main()
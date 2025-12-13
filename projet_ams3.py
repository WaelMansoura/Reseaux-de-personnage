# -*- coding: utf-8 -*-
"""PROJET AMS3


# Install & Import Packages
"""


# pip install --upgrade pymupdf

import pymupdf
import unicodedata
import re #pour les expressions régulieres

"""# Useful functions

Supprimons dans un premier temps tout les caracteres de contrôle (Code ascii < 32)
"""

OCTETS_A_SUPPRIMER = bytes(
    list(i for i in range(32))  # contrôle à supprimer
    + list(range(48, 58))  # chiffres '0' à '9'
)

def nettoyer_bytes_rapide(data_brute: bytes) -> bytes:
    """
    Nettoie un objet bytes en supprimant :
    - les caractères de contrôle < 32
    - les chiffres 0-9
    - l'expression "TERRE ET FONDATION" (insensible à la casse)
    - les espaces multiples
    """

    # Suppression des octets indésirables
    data = data_brute.translate(None, OCTETS_A_SUPPRIMER)

    # Décodage en texte
    txt = data.decode("utf-8", errors="ignore")

    # Suppression de l'expression "TERRE ET FONDATION"
    txt = re.sub(r"TERRE\s+et\s+FONDATION", "", txt)
    txt = txt.replace("Isaac Asimov", "")
    txt = txt.replace("Fondation (Foundation)", "")
    # Réduction des espaces multiples → 1 seul espace
    txt = re.sub(r"\s{2,}", " ", txt)

    # Retour en bytes
    return txt.encode("utf-8")

"""# Open Documents"""



# Mes chemins d'accees
pdf_files = [
    "Books/Fondation_sample.pdf",
    "Books/Fondation_et_empire_sample.pdf",
    "Books/Fondation_foudroyée_sample.pdf",
    "Books/Seconde_Fondation_sample.pdf",
    "Books/Terre_et_Fondation_sample.pdf"
]

out = open("output.txt", "wb") # Crée un fichier de sortie en mode binaire
texte = str() # Variable de type string (str) qui accumulera TOUT le texte décodé

# Ouverture des fichiers DOCS
docs = [pymupdf.open(pdf_file) for pdf_file in pdf_files]

for doc in docs:
  for page in doc:
      text_bytes = page.get_text().encode("utf8")
      text_bytes = nettoyer_bytes_rapide(text_bytes)
      texte += text_bytes.decode('utf-8', errors='ignore')

      # print(text_bytes[:200])
      out.write(text_bytes) # Écrit le texte de la page
out.close()

print(texte[0:100])
if "chapitre" in texte :
    print("Le mot est présent")


# Crée le fichier texte à partir de la variable texte
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(texte)




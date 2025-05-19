"""
Module utils - Fonctions utilitaires pour l'application de gestion des notes circulaires et procédures.

Ce package fournit les fonctionnalités communes et les utilitaires utilisés dans l'ensemble de l'application.
"""

# Import des modules pour les rendre disponibles via utils.*
from utils.chatbot import CirculaireQABot
from models.config import *  

# Définition des modules à exposer lors d'un import *
__all__ = [
    'CirculaireQABot',
    'pdf_parser',
    'procedure_gen',
    'diagram_gen',
    'chatbot',
    'config'
]

# Version du package
__version__ = '1.0.0'

# Métadonnées
__author__ = 'Auteur de l\'application'
__email__ = 'email@example.com'
__description__ = 'Utilitaires pour la gestion des notes circulaires et procédures'

# Fonction d'initialisation qui peut être utilisée pour configurer le module
def init():
    """
    Initialise le module utils et prépare l'environnement nécessaire.
    
    Cette fonction crée les répertoires nécessaires s'ils n'existent pas déjà
    et configure les paramètres de base du module.
    
    Returns:
        bool: True si l'initialisation est réussie, False sinon
    """
    try:
        from pathlib import Path
        import os
        
        # Création des répertoires nécessaires
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / "data"
        temp_dir = base_dir / "temp"
        
        data_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)
        (temp_dir / "pdf").mkdir(exist_ok=True)
        
        # Création du fichier de données s'il n'existe pas
        data_file = data_dir / "donnees.json"
        if not data_file.exists():
            with open(data_file, 'w', encoding='utf-8') as f:
                import json
                json.dump({"circulaires": [], "procedures": []}, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation du module utils: {e}")
        return False
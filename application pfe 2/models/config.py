"""
Configuration centrale pour l'application Streamlit de gestion des notes circulaires et procédures.
Ce fichier contient les paramètres globaux et les constantes utilisés dans l'ensemble de l'application.
"""

import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"

# Fichiers de données
DATA_FILE = DATA_DIR / "donnees.json"
TEMP_PDF_DIR = TEMP_DIR / "pdf"

# Assurez-vous que les répertoires existent
DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
TEMP_PDF_DIR.mkdir(exist_ok=True)

# Configuration de l'application
APP_TITLE = "Gestionnaire de Notes Circulaires et Procédures"
APP_ICON = "📄"

# Structure des pages
PAGES = {
    "Page d'accueil": "Introduction et saisie de note circulaire",
    "Procédure": "Génération et affichage de procédure",
    "Logigramme": "Visualisation du logigramme",
    "Chatbot": "Questions-réponses sur les documents"
}

# Configuration des couleurs et du style
COLORS = {
    "primary": "#1E88E5",
    "secondary": "#FFC107",
    "success": "#4CAF50",
    "danger": "#F44336",
    "warning": "#FF9800",
    "info": "#2196F3",
    "light": "#F5F5F5",
    "dark": "#212121"
}

# Configuration du chatbot
CHATBOT_CONFIG = {
    "max_history": 50,  # Nombre maximum de messages dans l'historique
    "min_keywords": 2,  # Nombre minimum de mots-clés pour une recherche
    "min_keyword_length": 3  # Longueur minimale des mots-clés
}

# Configuration du parser PDF
PDF_CONFIG = {
    "timeout": 30,  # Délai d'attente maximum pour le traitement d'un PDF (en secondes)
    "max_size": 10 * 1024 * 1024  # Taille maximale de fichier PDF (10 Mo)
}

# Configuration du générateur de logigramme
DIAGRAM_CONFIG = {
    "node_distance": "1.5",
    "rankdir": "TB",  # Top to Bottom
    "fontname": "Arial",
    "fontsize": "12"
}

# Modèles pour les structures de données
CIRCULAIRE_TEMPLATE = {
    "id": "",
    "titre": "",
    "date": "",
    "contenu": "",
    "mots_cles": []
}

PROCEDURE_TEMPLATE = {
    "id": "",
    "titre": "",
    "description": "",
    "circulaire_id": "",  # ID de la note circulaire source
    "date_creation": "",
    "etapes": []  # Liste des étapes de la procédure
}

ETAPE_TEMPLATE = {
    "numero": 0,
    "titre": "",
    "description": "",
    "responsable": "",
    "delai": "",
    "documents": []
}

# Messages d'aide et info-bulles
HELP_TEXTS = {
    "circulaire_input": "Saisissez le texte de la note circulaire, en structurant clairement les étapes et les responsabilités.",
    "circulaire_upload": "Téléversez un fichier PDF contenant la note circulaire. Le système extraira automatiquement le texte.",
    "procedure_view": "Cette page affiche la procédure générée à partir de la note circulaire sélectionnée.",
    "diagram_view": "Ce logigramme représente visuellement les étapes de la procédure.",
    "chatbot": "Posez des questions sur les notes circulaires ou les procédures pour obtenir des réponses précises."
}
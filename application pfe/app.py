import streamlit as st
import os
import sys
import json
from pathlib import Path

# Configuration de la page - PLACEZ CECI AU DÉBUT AVANT TOUT AUTRE CODE ST
st.set_page_config(
    page_title="Gestionnaire de Notes Circulaires",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des variables de session si elles n'existent pas
if 'note_circulaire' not in st.session_state:
    st.session_state.note_circulaire = ""
if 'note_title' not in st.session_state:
    st.session_state.note_title = ""
if 'procedure_generee' not in st.session_state:
    st.session_state.procedure_generee = ""
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None

# Création des répertoires nécessaires s'ils n'existent pas
data_dir = Path("data")
if not data_dir.exists():
    data_dir.mkdir(parents=True)

# Vérification ou création du fichier de données
data_file = data_dir / "donnees.json"
if not data_file.exists():
    with open(data_file, 'w') as f:
        json.dump({"notes_circulaires": [], "procedures": []}, f)

def main():
    # Titre principal
    st.title("Gestionnaire de Notes Circulaires et Procédures")
    
    # Description de l'application
    st.write("""
    Cette application vous permet de gérer des notes circulaires, de générer des procédures,
    de visualiser des logigrammes et d'utiliser un chatbot pour des questions-réponses.
    """)
    
    # Instructions
    st.info("""
    **Instructions :**
    1. Commencez par saisir ou téléverser une note circulaire dans la page "Entrée de Note Circulaire".
    2. Générez une procédure basée sur cette note.
    3. Visualisez le logigramme correspondant.
    4. Utilisez le chatbot pour poser des questions sur la note ou la procédure.
    """)
    
    # Affichage d'informations sur l'état actuel
    st.sidebar.subheader("État actuel")
    if st.session_state.note_circulaire:
        st.sidebar.success(f"✅ Note circulaire présente: {st.session_state.note_title}")
    else:
        st.sidebar.warning("❌ Aucune note circulaire")
        
    if st.session_state.procedure_generee:
        st.sidebar.success("✅ Procédure générée")
    else:
        st.sidebar.warning("❌ Aucune procédure générée")

if __name__ == "__main__":
    main()
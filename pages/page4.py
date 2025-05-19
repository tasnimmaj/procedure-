# -*- coding: utf-8 -*-
"""
Page 4: Chatbot Questions-Réponses

Cette page permet d'interagir avec un chatbot spécialisé dans les notes circulaires et procédures générées.
"""

import streamlit as st
import json
import sys
from pathlib import Path

# AJOUTER LE RÉPERTOIRE PARENT AU PATH POUR IMPORTER LES MODULES UTILS
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# IMPORT DES FONCTIONS UTILITAIRES
try:
    from utils.chatbot import answer_question, initialize_chatbot
except ImportError as e:
    st.error(f"Erreur d'importation des modules utilitaires: {e}")
    st.warning("Assurez-vous que les modules dans le dossier 'utils' sont correctement installés.")

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Chatbot Q&R",
    page_icon="💬",
    layout="wide"
)

# CHARGEMENT DES DONNÉES DE CONTEXTE

def load_context_data():
    data_path = parent_dir / "data" / "donnees.json"
    context = {"note_circulaire": "", "procedure": ""}
    try:
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get("notes_circulaires"):
                context["note_circulaires"] = data["notes_circulaires"][-1].get("contenu", "")
            if data.get("procedures"):
                context["procedure"] = data["procedures"][-1].get("contenu", "")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
    return context

# INITIALISATION DE LA SESSION
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'context' not in st.session_state:
    st.session_state['context'] = load_context_data()
    initialize_chatbot(st.session_state['context'])

# AFFICHAGE DE LA PAGE

def main():
    st.title("Chatbot Questions-Réponses sur les Procédures")
    st.write("Posez vos questions sur les notes circulaires et procédures générées.")

    # Contexte modifiable
    with st.expander("Voir/Modifier le contexte du chatbot"):
        col1, col2 = st.columns(2)
        with col1:
            note_text = st.text_area(
                "Note Circulaire", 
                value=st.session_state['context'].get('note_circulaires', ''), 
                height=200
            )
        with col2:
            proc_text = st.text_area(
                "Procédure Générée", 
                value=st.session_state['context'].get('procedure', ''), 
                height=200
            )
        if st.button("Mettre à jour le contexte"):
            st.session_state['context']['note_circulaires'] = note_text
            st.session_state['context']['procedure'] = proc_text
            initialize_chatbot(st.session_state['context'])
            st.success("Contexte mis à jour avec succès!")

    # Affichage de la conversation
    st.subheader("Conversation")
    chat_container = st.container()
    for msg in st.session_state['chat_history']:
        role = "Vous" if msg['role'] == 'user' else "Assistant"
        st.markdown(f"**{role}**: {msg['content']}")

    # Entrée utilisateur
    st.subheader("Poser une question")
    user_question = st.text_input("Votre question:", key="input_question")
    if st.button("Envoyer") and user_question.strip():
        st.session_state['chat_history'].append({"role": "user", "content": user_question})
        with st.spinner("Recherche d'une réponse..."):
            response = answer_question(user_question, st.session_state['chat_history'])
        st.session_state['chat_history'].append({"role": "assistant", "content": response})
        st.experimental_rerun()

    # Effacer l'historique
    if st.button("Effacer la conversation"):
        st.session_state['chat_history'] = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()
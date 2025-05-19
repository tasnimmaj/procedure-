# -*- coding: utf-8 -*-
"""
Page 1: Entrée de Note Circulaire

Cette page permet à l'utilisateur de saisir manuellement une note circulaire ou de téléverser un fichier PDF contenant une note circulaire.
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path

# AJOUTER LE RÉPERTOIRE PARENT AU PATH POUR IMPORTER LES MODULES UTILITAIRES
try:
    parent_dir = os.path.dirname(os.getcwd())
    if (parent_dir not in sys.path):
        sys.path.append(parent_dir)
except Exception as e:
    st.warning(f"Impossible de définir le répertoire parent : {e}")

# IMPORT DES MODULES UTILITAIRES
try:
    from utils.pdf_parser import extract_text_from_pdf
    from utils.procedure_gen import generate_procedure_with_model, MODELS
except ImportError as e:
    st.error(f"Erreur d'importation des modules utilitaires: {e}")
    st.warning("Assurez-vous que les modules dans le dossier 'utils' sont correctement installés.")

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Entrée de Note Circulaire",
    page_icon="📄",
    layout="wide"
)

# FONCTION PRINCIPALE

def main():
    st.title("Entrée de Note Circulaire")
    st.write(
        """
        Veuillez saisir manuellement votre note circulaire ou téléverser un fichier PDF contenant la note.
        Vous pouvez choisir l'une ou l'autre méthode selon votre préférence.
        """
    )

    tab1, tab2 = st.tabs(["Saisie Manuelle", "Téléverser un PDF"])

    # Onglet Saisie Manuelle
    with tab1:
        st.subheader("Saisie Manuelle de la Note Circulaire")
        note_title = st.text_input("Titre de la Note Circulaire", key="note_title_input")
        note_content = st.text_area(
            "Contenu de la Note Circulaire",
            height=300,
            placeholder="Saisissez ici le contenu complet de votre note circulaire...",
            key="note_content_input"
        )
        if st.button("Enregistrer la Note Circulaire", key="save_manual_note"):
            if note_title and note_content:
                st.session_state.note_circulaire = note_content
                st.session_state.note_title = note_title
                # Sauvegarde
                data_file = Path("data/donnees.json")
                if data_file.exists():
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {"notes_circulaires": [], "procedures": []}
                data["notes_circulaires"].append({
                    "titre": note_title,
                    "contenu": note_content,
                    "methode": "saisie_manuelle",
                    "date_creation": st.session_state.get("date_creation", "")
                })
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                st.success("La note circulaire a été enregistrée avec succès!")
            else:
                st.warning("Veuillez remplir le titre et le contenu de la note circulaire.")

    # Onglet Téléverser PDF
    with tab2:
        st.subheader("Téléversement d'une Note Circulaire en PDF")
        pdf_title = st.text_input("Titre de la Note Circulaire", key="pdf_title_input")
        uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")
        if uploaded_file:
            pdf_dir = Path("data/pdf_temp")
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / uploaded_file.name
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            try:
                st.write("Traitement du PDF en cours...")
                pdf_text = extract_text_from_pdf(pdf_path)
                with st.expander("Aperçu du contenu extrait"):
                    st.text_area("Contenu extrait du PDF", value=pdf_text, height=200, disabled=True)
                if st.button("Confirmer et Enregistrer", key="save_pdf_note"):
                    if pdf_title:
                        st.session_state.note_circulaire = pdf_text
                        st.session_state.note_title = pdf_title
                        data_file = Path("data/donnees.json")
                        if data_file.exists():
                            with open(data_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        else:
                            data = {"notes_circulaires": [], "procedures": []}
                        data["notes_circulaires"].append({
                            "titre": pdf_title,
                            "contenu": pdf_text,
                            "methode": "telechargement_pdf",
                            "chemin_pdf": str(pdf_path),
                            "date_creation": st.session_state.get("date_creation", "")
                        })
                        with open(data_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        st.success("La note circulaire du PDF a été enregistrée avec succès!")
                    else:
                        st.warning("Veuillez spécifier un titre pour la note circulaire.")
            except Exception as e:
                st.error(f"Erreur lors du traitement du PDF: {e}")

    # Bouton Générer Procédure
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.get("note_circulaire"):
            # Sélection du modèle
            model_id = st.selectbox(
                "🤖 Sélectionnez le modèle à utiliser",
                options=list(MODELS.keys()),
                format_func=lambda x: MODELS[x]["name"],
                help="Choisissez le modèle qui générera la procédure"
            )
            st.info(MODELS[model_id]["description"])
            
            if st.button("Générer la Procédure", type="primary", use_container_width=True):
                try:
                    # Stocker le modèle sélectionné dans la session
                    st.session_state.model_selected = model_id
                    procedure = generate_procedure_with_model(st.session_state.note_circulaire, model_id)
                    st.session_state.procedure_generee = procedure
                    # Sauvegarde procédure
                    data_file = Path("data/donnees.json")
                    if data_file.exists():
                        with open(data_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        data = {"notes_circulaires": [], "procedures": []}
                    data["procedures"].append({
                        "titre": f"Procédure pour {st.session_state.get('note_title', 'Note sans titre')}",
                        "contenu": procedure,
                        "note_source": st.session_state.get('note_title', ''),
                        "date_creation": st.session_state.get("date_creation", "")
                    })
                    with open(data_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    st.success("La procédure a été générée et enregistrée avec succès!")
                    st.markdown("[Voir la Procédure Générée](/pages/page2)")
                except Exception as e:
                    st.error(f"Erreur lors de la génération de la procédure: {e}")
        else:
            st.button("Générer la Procédure", disabled=True, use_container_width=True)
            st.info("Veuillez d'abord saisir ou téléverser une note circulaire.")

if __name__ == "__main__":
    main()

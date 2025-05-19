# -*- coding: utf-8 -*-
"""
Page 3: Génération de Logigramme

Cette page génère un logigramme basé sur la procédure générée précédemment.
"""

import streamlit as st
import json
import sys
from pathlib import Path
import graphviz

# AJOUTER LE RÉPERTOIRE PARENT AU PATH POUR IMPORTER LES MODULES UTILS
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# IMPORT DES FONCTIONS UTILITAIRES
try:
    from utils.diagram_gen import extract_steps_from_procedure, generate_flowchart
except ImportError as e:
    st.error(f"Erreur d'importation des modules utilitaires: {e}")
    st.warning("Assurez-vous que les modules dans le dossier 'utils' sont correctement installés.")

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Logigramme",
    page_icon="📊",
    layout="wide"
)

# FONCTION CHARGEMENT DE LA DERNIÈRE PROCÉDURE

def load_last_procedure():
    data_path = parent_dir / "data" / "donnees.json"
    if data_path.exists():
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get("procedures"):
                # On récupère le dernier contenu
                return data["procedures"][-1].get("contenu", "")
        except Exception as e:
            st.error(f"Erreur lors du chargement des données: {e}")
    return ""

# MAIN

def main():
    st.title("Visualisation du Logigramme")
    st.write("Cette page affiche un logigramme généré à partir de la procédure.")

    # Initialisation de la procédure dans la session
    if 'procedure_text' not in st.session_state:
        st.session_state['procedure_text'] = load_last_procedure()

    # Édition manuelle si nécessaire
    with st.expander("Modifier ou entrer manuellement la procédure"):
        proc = st.text_area(
            "Texte de la procédure",
            value=st.session_state['procedure_text'],
            height=300
        )
        if st.button("Mettre à jour la procédure"):
            st.session_state['procedure_text'] = proc
            st.success("Procédure mise à jour avec succès!")

    procedure_text = st.session_state.get('procedure_text', '')
    if procedure_text:
        try:
            # Extraction des étapes (Graphviz)
            steps = extract_steps_from_procedure(procedure_text)
            if steps:
                # Génération du logigramme Graphviz
                graph = generate_flowchart(steps)
                st.graphviz_chart(graph)

                # Génération du logigramme matplotlib inspiré du code fourni
                from utils.diagram_gen import extract_activities_and_actors, draw_flowchart_matplotlib
                activities, actors = extract_activities_and_actors(procedure_text)
                if activities and actors:
                    st.subheader("Logigramme (vue alternative)")
                    fig = draw_flowchart_matplotlib(activities, actors)
                    st.pyplot(fig)

                # Bouton de téléchargement
                dot_source = graph.source
                st.download_button(
                    label="Télécharger le logigramme (DOT)",
                    data=dot_source,
                    file_name="logigramme.dot",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("Aucune étape n'a pu être extraite de la procédure. Veuillez vérifier le format.")
        except Exception as e:
            st.error(f"Erreur lors de la génération du logigramme: {e}")
    else:
        st.info("Veuillez d'abord générer une procédure dans la page précédente ou entrer manuellement une procédure ci-dessus.")

if __name__ == "__main__":
    main()

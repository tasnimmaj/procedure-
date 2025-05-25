""" Page 3: Génération de Logigramme avec styles partagés
Cette page génère un logigramme basé sur le tableau Markdown créé dans la page 2.
Elle utilise Graphviz pour transformer le tableau en représentation visuelle.
"""

import streamlit as st
from utils.logigramme_advanced import generate_flowchart
from utils.styles import apply_green_theme, set_page_config  # Import du fichier de styles
import base64

# Configuration de la page avec fonction partagée
set_page_config("Logigramme", "📊")

# Application du thème vert
apply_green_theme()

def main():
    st.title("📊 Générateur de Logigramme")
    
    # Récupérer le nom de la procédure de la session
    procedure_name = st.session_state.get('procedure_name', "Nouvelle procédure")
    
    # Interface utilisateur
    procedure_name = st.text_input("Nom de la procédure:", procedure_name)
    st.session_state.procedure_name = procedure_name 
    
    # Récupérer le tableau source
    if 'procedure_generee' in st.session_state:
        markdown_text = st.session_state.get('procedure_generee', '')
        
        # Extraire uniquement le tableau des étapes
        tableau_etapes = ""
        capture = False
        for line in markdown_text.split("\n"):
            if "| N°" in line or "| No" in line:
                capture = True
            if capture and line.strip():
                if "Entrées/Sorties" in line or "# " in line:
                    break
                tableau_etapes += line + "\n"
        
        markdown_text = tableau_etapes
    else:
        markdown_text = ""
 
    # Afficher le tableau Markdown source si nécessaire
    if st.checkbox("📋 Afficher le tableau source de la procédure"):
        st.text_area("Tableau Markdown", markdown_text, height=200)
    
    # Générer le logigramme
    try:
        if markdown_text:
            st.subheader("Logigramme généré")
            
            # Générer le diagramme
            flowchart_base64, error = generate_flowchart(markdown_text, procedure_name)
            
            if flowchart_base64 and not error:
                # Afficher l'image
                st.image(f"data:image/png;base64,{flowchart_base64}")
                
                # Option de téléchargement en PNG
                st.download_button(
                    label="📥 Télécharger en PNG",
                    data=base64.b64decode(flowchart_base64),
                    file_name="logigramme.png",
                    mime="image/png"
                )
            else:
                st.warning(f"⚠️ {error or 'Impossible de générer le logigramme. Vérifiez le format du tableau.'}")
        else:
            st.info("ℹ️ Aucun tableau de procédure n'a été fourni. Veuillez d'abord créer une procédure dans l'onglet précédent.")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du logigramme: {str(e)}")
        st.exception(e)
    
    # Informations supplémentaires
    with st.expander("ℹ️ Informations sur les logigrammes"):
        st.markdown("""
        ### Qu'est-ce qu'un logigramme?
        
        Un logigramme est une représentation graphique d'un processus ou d'une procédure, qui montre la séquence des activités et les acteurs impliqués.
        
        ### Caractéristiques des logigrammes générés:
        
        * Début et fin représentés par des ovales colorés
        * Actions représentées par des rectangles verts
        * Décisions représentées par des losanges jaunes
        * Identification claire des acteurs pour chaque étape
        * Numérotation des étapes pour suivre facilement le processus
        """)

if __name__ == "__main__":
    main()
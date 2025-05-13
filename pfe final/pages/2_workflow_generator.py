import streamlit as st
import os
import tempfile
import base64

# Import des modules utils personnalisés
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_utils import get_llm, generate_workflow_diagram

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Logigrammes",
    page_icon="📊",
    layout="wide",
)

# Style CSS personnalisé
st.markdown("""
<style>
    .title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #EFF6FF;
        border-left: 5px solid #1E3A8A;
        padding: 1rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser les variables de session si elles n'existent pas
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'workflow_generated' not in st.session_state:
    st.session_state.workflow_generated = False
if 'current_workflow' not in st.session_state:
    st.session_state.current_workflow = ""

# En-tête de la page
st.markdown('<p class="title">📊 Générateur de Logigrammes</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Visualisez vos procédures sous forme de diagrammes</p>', unsafe_allow_html=True)

# Sidebar pour les configurations
with st.sidebar:
    st.header("Configuration")
    
    # Clé API pour Groq
    api_key = st.text_input(
        "Clé API Groq",
        value=st.session_state.api_key,
        type="password",
        help="Clé API pour accéder au service Groq"
    )
    st.session_state.api_key = api_key
    
    model_name = st.selectbox(
        "Modèle LLM",
        options=["mistral-saba-24b", "llama3-70b-8192", "mixtral-8x7b"],
        index=0,
        help="Modèle de langage à utiliser pour la génération"
    )
    
    # Initialiser le modèle LLM
    if st.button("Initialiser le LLM"):
        if api_key:
            with st.spinner("Initialisation du modèle..."):
                llm = get_llm(api_key, model_name)
                st.session_state.llm = llm
                if llm:
                    st.success("Modèle initialisé avec succès!")
                else:
                    st.error("Erreur lors de l'initialisation du LLM. Vérifiez votre clé API.")
        else:
            st.warning("Veuillez entrer une clé API pour Groq.")
    
    # Séparateur
    st.markdown("---")
    
    # Orientation du diagramme
    st.subheader("Options du diagramme")
    diagram_orientation = st.radio(
        "Orientation",
        options=["De haut en bas (TD)", "De gauche à droite (LR)"],
        index=0
    )
    st.session_state.diagram_orientation = "TD" if diagram_orientation == "De haut en bas (TD)" else "LR"
    
    # Section d'information
    st.info(
        "Ce générateur de logigrammes transforme les procédures textuelles en diagrammes visuels "
        "pour une meilleure compréhension des flux de travail."
    )

# Corps principal
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="section-header">Entrée: Procédure</p>', unsafe_allow_html=True)
    
    # Charge la procédure précédemment générée si disponible
    if 'current_procedure' in st.session_state and st.session_state.current_procedure:
        st.info("Une procédure a été trouvée dans la session précédente.")
        if st.button("Utiliser la procédure générée précédemment"):
            procedure_text = st.session_state.current_procedure
            st.markdown("**Procédure chargée:**")
            st.markdown(procedure_text)
    
    # Ou permet de saisir une nouvelle procédure
    procedure_text = st.text_area(
        "Entrez la procédure sous forme de tableau Markdown",
        height=300,
        placeholder="| N° | Activités | Description | Acteurs | Documents | Applications |\n| --- | --- | --- | --- | --- | --- |\n| 1 | Réception de la demande | Vérifier la complétude du dossier | Chargé de clientèle | Formulaire | Système GED |"
    )
    
    # Options pour le logigramme
    st.markdown('<p class="section-header">Options</p>', unsafe_allow_html=True)
    max_nodes = st.slider("Nombre maximum de nœuds", min_value=5, max_value=20, value=15)
    
    # Générer le logigramme
    if st.button("Générer le logigramme") and procedure_text:
        if hasattr(st.session_state, 'llm') and st.session_state.llm:
            with st.spinner("Génération du logigramme en cours..."):
                # Ajuster le texte Mermaid selon l'orientation choisie
                orientation = st.session_state.diagram_orientation
                
                mermaid_diagram = generate_workflow_diagram(st.session_state.llm, procedure_text)
                
                # Remplacer l'orientation si nécessaire
                if orientation == "LR" and "graph TD" in mermaid_diagram:
                    mermaid_diagram = mermaid_diagram.replace("graph TD", "graph LR")
                elif orientation == "TD" and "graph LR" in mermaid_diagram:
                    mermaid_diagram = mermaid_diagram.replace("graph LR", "graph TD")
                
                # Si aucune orientation n'est spécifiée, ajouter-la
                if "graph" not in mermaid_diagram:
                    mermaid_diagram = f"graph {orientation}\n{mermaid_diagram}"
                
                st.session_state.current_workflow = mermaid_diagram
                st.session_state.workflow_generated = True
        else:
            st.error("Le modèle LLM n'est pas initialisé. Veuillez configurer l'API et initialiser le modèle.")

with col2:
    st.markdown('<p class="section-header">Résultat: Logigramme</p>', unsafe_allow_html=True)
    
    if st.session_state.workflow_generated and st.session_state.current_workflow:
        # Afficher le diagramme Mermaid
        st.markdown(f"```mermaid\n{st.session_state.current_workflow}\n```")
        
        # Afficher le code source Mermaid
        with st.expander("Voir le code Mermaid"):
            st.code(st.session_state.current_workflow, language="mermaid")
        
        # Options pour enregistrer le logigramme
        col_save1, col_save2 = st.columns([1, 1])
        with col_save1:
            if st.button("Enregistrer en Markdown"):
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, "logigramme.md")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"```mermaid\n{st.session_state.current_workflow}\n```")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Télécharger le fichier MD",
                        data=f,
                        file_name="logigramme.md",
                        mime="text/markdown"
                    )
                
                st.success(f"Logigramme enregistré: {file_path}")
        
        with col_save2:
            if st.button("Copier le code Mermaid"):
                st.code(st.session_state.current_workflow)
                st.success("Code copié! Utilisez Ctrl+C pour le copier dans votre presse-papiers.")
    else:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **Le logigramme généré apparaîtra ici.**
        
        Le système analysera la procédure fournie et générera un logigramme représentant:
        - Les étapes clés du processus
        - Les points de décision
        - Les flux entre les différentes étapes
        - La séquence logique des opérations
        
        Pour une meilleure visualisation, limitez le nombre d'étapes et utilisez l'orientation qui convient le mieux à votre procédure.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
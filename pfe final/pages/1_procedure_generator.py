import streamlit as st
import os
import json
import tempfile
from pathlib import Path

# Import des modules utils personnalisés
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.text_extraction import extract_text_from_pdf_with_tesseract, extract_articles_from_text
from utils.vectorstore import load_data, initialize_vectorstore, find_similar_notes
from utils.llm_utils import get_llm, generate_procedure

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Procédures Bancaires",
    page_icon="🧩",
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
    .note-box {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser les variables de session si elles n'existent pas
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'procedure_generated' not in st.session_state:
    st.session_state.procedure_generated = False
if 'current_procedure' not in st.session_state:
    st.session_state.current_procedure = ""
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'articles' not in st.session_state:
    st.session_state.articles = {}

# En-tête de la page
st.markdown('<p class="title">🧩 Générateur de Procédures Bancaires</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Transformez vos notes circulaires en procédures structurées</p>', unsafe_allow_html=True)

# Sidebar pour les configurations
with st.sidebar:
    st.header("Configuration")
    
    # Configuration du chemin des données
    data_path = st.text_input(
        "Chemin du fichier JSON de données",
        value="donnee.json",
        help="Chemin vers le fichier JSON contenant les données des procédures"
    )
    
    vs_dir = st.text_input(
        "Répertoire de la base vectorielle",
        value="chroma_store",
        help="Répertoire où stocker/charger la base vectorielle"
    )
    
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
    
    # Boutton pour charger les données
    if st.button("Initialiser le système"):
        with st.spinner("Chargement des données..."):
            # Vérifier si les fichiers existent
            if not os.path.exists(data_path):
                st.error(f"Le fichier de données {data_path} n'existe pas.")
            else:
                # Charger les données
                docs, notes_map, procs_map = load_data(data_path)
                st.session_state.docs = docs
                st.session_state.notes_map = notes_map
                st.session_state.procs_map = procs_map
                
                # Initialiser la base vectorielle
                vs = initialize_vectorstore(docs, vs_dir)
                st.session_state.vectorstore = vs
                
                # Initialiser le modèle LLM
                if api_key:
                    llm = get_llm(api_key, model_name)
                    st.session_state.llm = llm
                    if llm:
                        st.success("Système initialisé avec succès!")
                    else:
                        st.error("Erreur lors de l'initialisation du LLM. Vérifiez votre clé API.")
                else:
                    st.warning("Veuillez entrer une clé API pour Groq.")
    
    # Séparateur
    st.markdown("---")
    
    # Section d'information
    st.info(
        "Ce générateur de procédures utilise le RAG (Retrieval Augmented Generation) "
        "pour créer des procédures structurées à partir de notes circulaires. "
        "Il recherche des exemples similaires dans la base de données pour améliorer la qualité des résultats."
    )

# Corps principal
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="section-header">Entrée: Note Circulaire</p>', unsafe_allow_html=True)
    
    # Options d'entrée
    input_option = st.radio(
        "Source de la note circulaire",
        options=["Saisie manuelle", "Fichier PDF"],
        horizontal=True
    )
    
    if input_option == "Saisie manuelle":
        note_text = st.text_area(
            "Entrez le texte de la note circulaire",
            height=300,
            placeholder="Exemple: Article 1 : Une ligne de crédit de 50 millions d'euros est mise à disposition des PME tunisiennes..."
        )
        if note_text:
            st.session_state.extracted_text = note_text
            st.session_state.articles = extract_articles_from_text(note_text)
    else:
        uploaded_file = st.file_uploader("Téléchargez une note circulaire en PDF", type=["pdf"])
        if uploaded_file:
            with st.spinner("Extraction du texte en cours..."):
                extracted_text = extract_text_from_pdf_with_tesseract(uploaded_file)
                if extracted_text:
                    st.session_state.extracted_text = extracted_text
                    st.session_state.articles = extract_articles_from_text(extracted_text)
                    st.success("Texte extrait avec succès!")
                else:
                    st.error("Erreur lors de l'extraction du texte.")
    
    # Afficher les articles extraits
    if st.session_state.articles:
        st.markdown('<div class="note-box">', unsafe_allow_html=True)
        st.markdown("**Articles extraits:**")
        for article_num, article_text in st.session_state.articles.items():
            st.markdown(f"**{article_num}:** {article_text}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Générer la procédure
    if st.button("Générer la procédure") and st.session_state.extracted_text:
        if hasattr(st.session_state, 'llm') and st.session_state.llm:
            with st.spinner("Recherche de notes similaires..."):
                similar_notes = find_similar_notes(
                    st.session_state.vectorstore,
                    st.session_state.extracted_text,
                    k=2
                )
            
            if similar_notes:
                st.info(f"{len(similar_notes)} notes similaires trouvées pour référence.")
            else:
                st.info("Aucune note similaire trouvée. Une procédure originale sera générée.")
            
            with st.spinner("Génération de la procédure en cours..."):
                generated_procedure = generate_procedure(
                    st.session_state.llm,
                    st.session_state.extracted_text,
                    similar_notes,
                    getattr(st.session_state, 'notes_map', {}),
                    getattr(st.session_state, 'procs_map', {})
                )
                
                st.session_state.current_procedure = generated_procedure
                st.session_state.procedure_generated = True
        else:
            st.error("Le modèle LLM n'est pas initialisé. Veuillez configurer l'API et initialiser le système.")

with col2:
    st.markdown('<p class="section-header">Résultat: Procédure Générée</p>', unsafe_allow_html=True)
    
    if st.session_state.procedure_generated and st.session_state.current_procedure:
        st.markdown(st.session_state.current_procedure)
        
        # Options pour enregistrer la procédure
        col_save1, col_save2 = st.columns([1, 1])
        with col_save1:
            if st.button("Enregistrer en Markdown"):
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, "procedure_generee.md")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(st.session_state.current_procedure)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Télécharger le fichier MD",
                        data=f,
                        file_name="procedure_generee.md",
                        mime="text/markdown"
                    )
                
                st.success(f"Procédure enregistrée: {file_path}")
        
        with col_save2:
            if st.button("Copier dans le presse-papiers"):
                st.code(st.session_state.current_procedure)
                st.success("Code copié! Utilisez Ctrl+C pour le copier dans votre presse-papiers.")
    else:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **La procédure générée apparaîtra ici.**
        
        Le système analysera la note circulaire fournie et générera une procédure structurée comprenant:
        - Les étapes numérotées séquentiellement
        - Les activités à réaliser
        - Les descriptions détaillées
        - Les acteurs concernés
        - Les documents nécessaires
        - Les applications à utiliser
        """)
        st.markdown('</div>', unsafe_allow_html=True)
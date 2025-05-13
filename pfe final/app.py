import streamlit as st
import os
import base64

# Configuration de la page
st.set_page_config(
    page_title="Système de Gestion des Procédures Bancaires",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour afficher une image en base64 (pour l'icône)
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Style CSS personnalisé
st.markdown("""
<style>
    .main-title {
        font-size: 3rem !important;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 3rem;
    }
    .feature-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E3A8A;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# En-tête de l'application
st.markdown('<p class="main-title">Système de Gestion des Procédures Bancaires</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Automatisez la création et la gestion de procédures bancaires</p>', unsafe_allow_html=True)

# Présentation des fonctionnalités principales
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown('<p class="feature-title">🧩 Générateur de Procédures</p>', unsafe_allow_html=True)
    st.write(
        "Générez automatiquement des procédures bancaires détaillées à partir de notes circulaires. "
        "Notre système analyse le contenu, identifie les similitudes avec des procédures existantes et "
        "produit une procédure structurée et complète."
    )
    st.page_link("pages/1_procedure_generator.py", label="Accéder au générateur de procédures")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown('<p class="feature-title">🤖 Chatbot Questions-Réponses</p>', unsafe_allow_html=True)
    st.write(
        "Posez des questions sur les procédures bancaires et obtenez des réponses précises. "
        "Notre chatbot s'appuie sur la base de données pour fournir des informations fiables et contextualisées."
    )
    st.page_link("pages/3_qa_chatbot.py", label="Accéder au chatbot")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown('<p class="feature-title">📊 Générateur de Logigrammes</p>', unsafe_allow_html=True)
    st.write(
        "Créez des représentations visuelles des procédures sous forme de logigrammes. "
        "Visualisez les étapes, les décisions et les flux pour mieux comprendre et communiquer les processus."
    )
    st.page_link("pages/2_workflow_generator.py", label="Accéder au générateur de logigrammes")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown('<p class="feature-title">🔍 Explorateur de Données</p>', unsafe_allow_html=True)
    st.write(
        "Explorez les données des procédures, notes circulaires, et autres documents bancaires. "
        "Visualisez les statistiques, recherchez des informations spécifiques, et analysez les tendances."
    )
    st.page_link("pages/4_data_explorer.py", label="Accéder à l'explorateur de données")
    st.markdown('</div>', unsafe_allow_html=True)

# Informations supplémentaires
st.markdown("---")
st.markdown("### Comment utiliser cette application")
st.write(
    "Naviguez entre les différentes fonctionnalités à l'aide du menu de navigation situé dans la barre latérale. "
    "Chaque page offre des outils spécifiques pour gérer, analyser et générer des procédures bancaires."
)

# Sidebar pour des informations supplémentaires
with st.sidebar:
    st.header("À propos")
    st.info(
        "Cette application a été développée pour automatiser et optimiser la gestion des procédures bancaires. "
        "Elle utilise des technologies avancées de traitement du langage naturel et d'intelligence artificielle "
        "pour générer des procédures, des logigrammes et fournir des informations contextualisées."
    )
import streamlit as st 
import os
import sys
import json
from pathlib import Path

# Configuration de la page - PLACEZ CECI AU DÉBUT AVANT TOUT AUTRE CODE ST
st.set_page_config(
    page_title="Gestionnaire de Procédures Internes",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le thème vert complet
st.markdown("""<style>
    /* Import de la police pour un look plus professionnel */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables de couleurs vertes */
    :root {
        --primary-green: #2E7D32;
        --secondary-green: #4CAF50;
        --light-green: #7ba431;
        --accent-green: #66BB6A;
        --bg-green: #E8F5E8;
        --dark-green: #1B5E20;
        --success-green: #4CAF50;
    }
    
    /* Style général de l'application */
    .stApp {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, #f8fff8 0%, #e8f5e8 100%) !important;
    }
    
    /* Header avec logo */
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: linear-gradient(90deg, var(--primary-green), var(--secondary-green));
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }
    
    .logo-container {
        width: 80px;
        height: 80px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Couleurs principales pour tous les éléments */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: var(--primary-green) !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    
    .main h1 {
        font-size: 2.5rem !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
    }
    
    /* Boutons avec style vert amélioré */
    .stButton > button {
        background: linear-gradient(45deg, var(--primary-green), var(--secondary-green)) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(46, 125, 50, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, var(--dark-green), var(--primary-green)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4) !important;
    }
    
    /* Barre latérale avec thème vert permanent */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary-green), var(--secondary-green)) !important;
        border-right: 3px solid var(--accent-green) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stTextArea label {
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* Navigation de la barre latérale */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        background-color: transparent !important;
        padding: 1rem !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        color: white !important;
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important;
        margin: 0.25rem 0 !important;
        padding: 0.75rem 1rem !important;
        text-decoration: none !important;
        transition: all 0.3s ease !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(5px) !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
        background: rgba(255, 255, 255, 0.25) !important;
        font-weight: 600 !important;
        border-left: 4px solid white !important;
    }
    
    /* Widgets de la barre latérale */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: white !important;
    }
    
    /* Champs de saisie avec thème vert */
    div[data-baseweb="select"] {
        border: 2px solid var(--secondary-green) !important;
        border-radius: 8px !important;
        background: white !important;
    }
    
    div[data-baseweb="input"] {
        border: 2px solid var(--secondary-green) !important;
        border-radius: 8px !important;
        background: white !important;
    }
    
    .stTextArea textarea {
        border: 2px solid var(--secondary-green) !important;
        border-radius: 8px !important;
        background: white !important;
    }
    
    /* Focus states */
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="input"]:focus-within,
    .stTextArea textarea:focus {
        border-color: var(--primary-green) !important;
        box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.2) !important;
    }
    
    /* Alertes et notifications */
    .stAlert {
        background: var(--bg-green) !important;
        border: 2px solid var(--secondary-green) !important;
        border-radius: 8px !important;
        color: var(--dark-green) !important;
    }
    
    .stSuccess {
        background: rgba(76, 175, 80, 0.1) !important;
        border: 2px solid var(--success-green) !important;
        color: var(--dark-green) !important;
    }
    
    .stInfo {
        background: rgba(123, 164, 49, 0.1) !important;
        border: 2px solid var(--light-green) !important;
        color: var(--dark-green) !important;
    }
    
    /* Conteneurs et cartes */
    .stContainer {
        background: white !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.1) !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(76, 175, 80, 0.2) !important;
    }
    
    /* Métriques */
    div[data-testid="metric-container"] {
        background: var(--bg-green) !important;
        border: 2px solid var(--secondary-green) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--primary-green) !important;
        font-weight: 700 !important;
    }
    
    /* Tableaux */
    .stDataFrame {
        border: 2px solid var(--secondary-green) !important;
        border-radius: 8px !important;
    }
    
    /* Liens */
    a {
        color: var(--primary-green) !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    
    a:hover {
        color: var(--dark-green) !important;
        text-decoration: none !important;
    }
    
    /* Sélection de texte */
    ::selection {
        background-color: rgba(76, 175, 80, 0.3) !important;
        color: var(--dark-green) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-green) !important;
        border-radius: 8px !important;
        padding: 0.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--primary-green) !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: var(--dark-green) !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-green) !important;
        color: var(--primary-green) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    
    /* Colonnes avec espacement */
    .row-widget.stRadio > div {
        background: var(--bg-green) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid var(--secondary-green) !important;
    }
    
    /* Style pour les checkbox */
    .stCheckbox {
        background: var(--bg-green) !important;
        padding: 0.5rem !important;
        border-radius: 6px !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background: var(--bg-green) !important;
        border: 2px dashed var(--secondary-green) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Progress bar */
    .stProgress .st-bo {
        background-color: var(--secondary-green) !important;
    }
    
    /* Spinner */
    .stSpinner {
        color: var(--primary-green) !important;
    }
    
    /* Divider */
    hr {
        border-color: var(--secondary-green) !important;
        margin: 2rem 0 !important;
    }
    
    /* Footer */
    .main-footer {
        background: var(--bg-green) !important;
        color: var(--dark-green) !important;
        text-align: center !important;
        padding: 1rem !important;
        margin-top: 3rem !important;
        border-radius: 8px !important;
        border-top: 3px solid var(--secondary-green) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialisation des variables de session si elles n'existent pas
if 'note_circulaire' not in st.session_state:
    st.session_state.note_circulaire = ""
if 'note_title' not in st.session_state:
    st.session_state.note_title = ""
if 'procedure_generee' not in st.session_state:
    st.session_state.procedure_generee = ""

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
    # Affichage de l'état dans la sidebar
    if st.session_state.get("note_circulaire") and st.session_state.get("note_title"):
        st.sidebar.success(f"✅ Note circulaire présente: {st.session_state.note_title}")
    else:
        st.sidebar.warning("❌ Aucune note circulaire")
        
    if st.session_state.get("procedure_generee"):
        st.sidebar.success("✅ Procédure générée")
    else:
        st.sidebar.warning("❌ Aucune procédure générée")

    # Header avec logo
    st.markdown("""
        <div class="app-header">
            <div>
                <h1 style="margin: 0; color: white; font-size: 1.8rem;">Gestionnaire de Procédures Internes</h1>
                <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 1rem;">Banque Centrale - Transformation des Notes Circulaires</p>
            </div>
            <div class="logo-container">
                <img src="logo.png" alt="Logo" style="max-width: 60px; max-height: 60px; object-fit: contain;" onerror="this.style.display='none'">
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Titre principal (masqué car dans le header)
    # st.title("Gestionnaire de Procédures Internes")
    
    # Description professionnelle de l'application
    st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(46, 125, 50, 0.1); border: 1px solid rgba(76, 175, 80, 0.2); margin: 2rem 0;'>
            <h3 style='color: #2E7D32; margin-top: 0; text-align: center;'>🏦 Plateforme de Gestion des Procédures</h3>
            <p style='color: #1B5E20; font-size: 1.1rem; line-height: 1.6; text-align: center; margin-bottom: 1.5rem;'>
                Outil professionnel destiné aux agents de procédures internes pour transformer 
                les notes circulaires de la Banque Centrale en procédures opérationnelles structurées.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Instructions détaillées
    st.info("""
    **📋 Guide d'utilisation :**
    
    **Étape 1** - Saisie de la Note Circulaire  
    Accédez à la page "Entrée de Note Circulaire" pour saisir ou téléverser votre note circulaire officielle.
    
    **Étape 2** - Génération de Procédure  
    Le système analysera automatiquement la note et générera une procédure structurée adaptée aux standards internes.
    
    **Étape 3** - Visualisation du Logigramme  
    Consultez le logigramme généré pour valider le flux de la procédure avant publication.
    
    **Étape 4** - Finalisation  
    Exportez la procédure finalisée dans le format requis par votre service.
    """)
    
    # Ajout d'une séparation visuelle
    st.markdown("---")
    
    # Statistiques/Métriques (exemple)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📄 Notes Traitées",
            value="--",
            help="Nombre total de notes circulaires traitées"
        )
    
    with col2:
        st.metric(
            label="⚙️ Procédures Générées", 
            value="--",
            help="Nombre de procédures créées"
        )
    
    with col3:
        st.metric(
            label="✅ Validations",
            value="--",
            help="Procédures validées et publiées"
        )
    
    with col4:
        st.metric(
            label="⏱️ Temps Moyen",
            value="--",
            help="Temps moyen de traitement"
        )
    
    # Section d'aide rapide
    with st.expander("💡 Aide Rapide", expanded=False):
        st.markdown("""
        **Questions fréquentes :**
        
        - **Comment importer une note ?** Utilisez le bouton "Parcourir" dans la section d'entrée ou collez directement le texte.
        - **Formats supportés :** PDF, DOCX, TXT pour l'import de fichiers.
        - **Modification de procédure :** Toutes les procédures générées peuvent être éditées avant finalisation.
        - **Sauvegarde :** Les données sont automatiquement sauvegardées lors de chaque étape.
        
        **Support technique :** Contactez l'équipe IT pour toute assistance technique.
        """)
    
    # Footer professionnel
    st.markdown("""
        <div class="main-footer">
            <p><strong>Banque Centrale</strong> | Système de Gestion des Procédures Internes</p>
            <p style="font-size: 0.9rem; margin-top: 0.5rem;">Version 2.0 | Développé pour optimiser la transformation des directives réglementaires</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
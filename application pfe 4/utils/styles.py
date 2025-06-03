"""
Fichier de styles partagé pour maintenir une cohérence visuelle 
sur toutes les pages de l'application Streamlit.
"""

import streamlit as st

def apply_green_theme():
    """
    Applique le thème vert complet à la page Streamlit.
    À appeler au début de chaque page pour maintenir la cohérence visuelle.
    """
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
        }          /* Barre latérale avec thème vert permanent */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--primary-green), var(--secondary-green)) !important;
            border-right: 3px solid var(--accent-green) !important;
            padding: 1rem !important;
        }

        /* Style général pour la sidebar */
        section[data-testid="stSidebar"] {
            color: white !important;
        }

        /* Style pour les éléments de navigation */
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stTextInput label,
        section[data-testid="stSidebar"] a {
            color: white !important;
        }
        
        /* Style spécifique pour les messages de succès et d'avertissement dans la sidebar */
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            margin: 8px 0 !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] > div > p {
            color: black !important;
            font-weight: 500 !important;
            background-color: rgba(255, 255, 255, 0.95) !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            margin: 0 !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
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

def set_page_config(page_title, page_icon="📄"):
    """
    Configuration standard pour toutes les pages avec les mêmes paramètres.
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
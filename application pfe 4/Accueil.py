import streamlit as st 
import os
import sys
import json
from pathlib import Path

# Ajout du répertoire utils au chemin Python
sys.path.append(str(Path(__file__).parent / "utils"))

# Import des styles avec logo
from utils.styles import apply_green_theme, set_page_config

# Configuration de la page - PLACEZ CECI AU DÉBUT AVANT TOUT AUTRE CODE ST
set_page_config("Gestionnaire de Procédures Internes", "🏦")

# Application du thème vert avec logo
apply_green_theme()

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

    # Description professionnelle de l'application
    st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(46, 125, 50, 0.1); border: 1px solid rgba(76, 175, 80, 0.2); margin: 2rem 0;'>
            <h3 style='color: #2E7D32; margin-top: 0; text-align: center;'>🏦 Plateforme de Gestion des Procédures</h3>
            <p style='color: #1B5E20; font-size: 1.1rem; line-height: 1.6; text-align: center; margin-bottom: 1.5rem;'>
                Outil professionnel destiné aux agents de procédures internes pour transformer 
                les notes circulaires de la Banque Zitouna en procédures opérationnelles structurées.
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
    
    **Étape 4** - Liste des Acteurs  
    Identifiez les acteurs impliqués dans la procédure et leurs activités respectives. 
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
            <p><strong>Banque Zitouna</strong> | Système de Gestion des Procédures Internes</p>
            <p style="font-size: 0.9rem; margin-top: 0.5rem;">Version 2.0 | Développé pour optimiser la transformation des directives réglementaires</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
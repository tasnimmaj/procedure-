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
from utils.styles import apply_green_theme



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
    page_title="Entrée de Note Circulaire | Banque Centrale",
    page_icon="🏦",
    layout="wide"
)

# Appliquer le thème
apply_green_theme()

# FONCTION PRINCIPALE
def main():
    
    # Header personnalisé
    st.markdown("""
    <div class="custom-header fade-in">
        <div class="logo-placeholder">🏦</div>
        <h1>📄 Saisie de Note Circulaire</h1>
        <div class="subtitle">Banque Centrale - Système de Gestion des Procédures Internes</div>
        <p style="margin: 0; font-size: 1rem; opacity: 0.8;">
            Interface de saisie et traitement des notes circulaires pour génération automatique de procédures
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Instructions d'utilisation
    with st.expander("📋 Guide d'utilisation", expanded=False):
        st.markdown("""
        **Étapes pour créer une procédure :**
        
        1. **Choisissez votre méthode** : Saisie manuelle ou téléversement PDF
        2. **Entrez le contenu** : Saisissez ou importez votre note circulaire
        3. **Configurez la génération** : Sélectionnez le modèle et le nombre d'étapes
        4. **Générez** : Lancez la création automatique de la procédure
        
        💡 **Conseil** : Pour de meilleurs résultats, utilisez des notes circulaires complètes et structurées.
        """)

    tab1, tab2 = st.tabs(["✍️ Saisie Manuelle", "📁 Téléverser un PDF"])

    # Onglet Saisie Manuelle
    with tab1:
        st.markdown('<div class="tab-content fade-in">', unsafe_allow_html=True)
        
        st.markdown("### 📝 Saisie Manuelle de la Note Circulaire")
        st.markdown("*Saisissez directement le contenu de votre note circulaire dans les champs ci-dessous.*")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            note_title = st.text_input(
                "🏷️ Titre de la Note Circulaire", 
                key="note_title_input",
                placeholder="Ex: Procédure de gestion des dossiers clients..."
            )
        with col2:
            st.metric("📊 Caractères titre", len(note_title) if note_title else 0, delta=None)
        
        note_content = st.text_area(
            "📄 Contenu de la Note Circulaire",
            height=300,
            placeholder="Saisissez ici le contenu complet de votre note circulaire...\n\nExemple:\n- Objectif de la procédure\n- Étapes détaillées\n- Responsabilités\n- Documents requis\n- Points de contrôle",
            key="note_content_input"
        )
        
        # Statistiques en temps réel
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Caractères", len(note_content) if note_content else 0)
        with col2:
            st.metric("📏 Mots", len(note_content.split()) if note_content else 0)
        with col3:
            st.metric("📋 Lignes", len(note_content.split('\n')) if note_content else 0)
        
        if st.button("💾 Enregistrer la Note Circulaire", key="save_manual_note", type="primary"):
            if note_title and note_content:
                st.session_state.note_circulaire = note_content
                st.session_state.note_title = note_title
                # Sauvegarde
                data_file = Path("data/donnees.json")
                data_file.parent.mkdir(exist_ok=True)
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
                st.success("✅ La note circulaire a été enregistrée avec succès!")
            else:
                st.warning("⚠️ Veuillez remplir le titre et le contenu de la note circulaire.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Onglet Téléverser PDF
    with tab2:
        st.markdown('<div class="tab-content fade-in">', unsafe_allow_html=True)
        
        st.markdown("### 📁 Téléversement d'une Note Circulaire en PDF")
        st.markdown("*Importez un fichier PDF contenant votre note circulaire pour extraction automatique du texte.*")
        
        pdf_title = st.text_input(
            "🏷️ Titre de la Note Circulaire", 
            key="pdf_title_input",
            placeholder="Ex: Procédure d'audit interne..."
        )
        
        uploaded_file = st.file_uploader(
            "📄 Choisissez un fichier PDF", 
            type="pdf",
            help="Formats acceptés : PDF uniquement. Taille maximale : 200MB"
        )
        
        if uploaded_file:
            # Informations sur le fichier
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📋 Nom du fichier", value="", delta=uploaded_file.name)
            with col2:
                file_size = len(uploaded_file.getbuffer()) / 1024 / 1024  # MB
                st.metric("💾 Taille", f"{file_size:.2f} MB")
            with col3:
                st.metric("📄 Type", "PDF")
            
            pdf_dir = Path("data/pdf_temp")
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / uploaded_file.name
            
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                with st.spinner("🔄 Traitement du PDF en cours..."):
                    pdf_text = extract_text_from_pdf(pdf_path)
                
                st.success("✅ PDF traité avec succès!")
                
                with st.expander("👁️ Aperçu du contenu extrait", expanded=True):
                    st.text_area(
                        "Contenu extrait du PDF", 
                        value=pdf_text, 
                        height=200, 
                        disabled=True
                    )
                    
                    # Statistiques du contenu extrait
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📝 Caractères", len(pdf_text))
                    with col2:
                        st.metric("📏 Mots", len(pdf_text.split()))
                    with col3:
                        st.metric("📋 Lignes", len(pdf_text.split('\n')))
                
                if st.button("✅ Confirmer et Enregistrer", key="save_pdf_note", type="primary"):
                    if pdf_title:
                        st.session_state.note_circulaire = pdf_text
                        st.session_state.note_title = pdf_title
                        data_file = Path("data/donnees.json")
                        data_file.parent.mkdir(exist_ok=True)
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
                        st.success("✅ La note circulaire du PDF a été enregistrée avec succès!")
                    else:
                        st.warning("⚠️ Veuillez spécifier un titre pour la note circulaire.")
                        
            except Exception as e:
                st.error(f"❌ Erreur lors du traitement du PDF: {e}")
                st.info("💡 Vérifiez que le PDF n'est pas protégé par mot de passe et contient du texte extractible.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Section Génération de Procédure
    st.markdown('<div class="procedure-section fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="procedure-title">🚀 Génération Automatique de Procédure</div>', unsafe_allow_html=True)
    
    if st.session_state.get("note_circulaire"):
        st.success(f"📋 Note circulaire chargée : **{st.session_state.get('note_title', 'Sans titre')}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sélection du modèle
            model_id = st.selectbox(
                "🤖 Modèle de génération",
                options=list(MODELS.keys()),
                format_func=lambda x: MODELS[x]["name"],
                help="Choisissez le modèle d'IA qui générera la procédure"
            )
            
            # Description du modèle sélectionné
            st.info(f"ℹ️ {MODELS[model_id]['description']}")
            
        with col2:
            # Sélection du nombre d'étapes
            num_steps = st.number_input(
                "📋 Nombre d'étapes de la procédure",
                min_value=3,
                max_value=60,
                value=7,
                step=1,
                help="Définissez le niveau de détail souhaité pour votre procédure"
            )
            
            # Estimation de la complexité
            if num_steps <= 5:
                complexity = "🟢 Simple"
            elif num_steps <= 15:
                complexity = "🟡 Modérée"
            else:
                complexity = "🔴 Complexe"
            
            st.metric("📊 Complexité estimée", complexity)
        
        # Bouton de génération centré
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Générer la Procédure", type="primary", use_container_width=True):
                try:
                    # Stocker les paramètres dans la session
                    st.session_state.model_selected = model_id
                    st.session_state.num_steps = num_steps
                    
                    # Barre de progression
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔄 Initialisation de la génération...")
                    progress_bar.progress(25)
                    
                    status_text.text("🤖 Traitement par le modèle d'IA...")
                    progress_bar.progress(50)
                    
                    # Générer la procédure
                    procedure = generate_procedure_with_model(
                        query=st.session_state.note_circulaire,
                        model_id=model_id,
                        num_steps=num_steps
                    )
                    
                    progress_bar.progress(75)
                    status_text.text("💾 Sauvegarde de la procédure...")
                    
                    st.session_state.procedure_generee = procedure
                    
                    # Sauvegarder la procédure
                    data_file = Path("data/donnees.json")
                    data_file.parent.mkdir(exist_ok=True)
                    if data_file.exists():
                        with open(data_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        data = {"notes_circulaires": [], "procedures": []}
                    
                    data["procedures"].append({
                        "titre": f"Procédure pour {st.session_state.get('note_title', 'Note sans titre')}",
                        "contenu": procedure,
                        "note_source": st.session_state.get('note_title', ''),
                        "modele": model_id,
                        "nombre_etapes": num_steps,
                        "date_creation": st.session_state.get("date_creation", "")
                    })
                    
                    with open(data_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Génération terminée avec succès!")
                    
                    st.success("🎉 Procédure générée et sauvegardée avec succès!")
                    st.balloons()
                    
                    st.session_state.redirect_to_page2 = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération : {str(e)}")
                    st.info("💡 Vérifiez votre connexion et réessayez.")
                    
    else:
        st.warning("⚠️ Veuillez d'abord saisir une note circulaire avant de générer une procédure.")
        st.info("💡 Utilisez l'un des onglets ci-dessus pour entrer votre note circulaire.")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer fade-in">
        <strong>🏦 Banque Centrale - Système de Gestion des Procédures</strong><br>
        Interface de saisie et génération automatique | Version 2.0
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
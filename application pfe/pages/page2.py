"""
Page 2: Procédure Générée avec RAG

Cette page affiche la procédure générée à partir de la note circulaire saisie ou téléversée sur la page 1.
Elle utilise un système de RAG pour trouver des notes similaires et générer une procédure plus pertinente.
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path
import time

# AJOUTER LE RÉPERTOIRE PARENT AU PATH POUR IMPORTER LES MODULES UTILITAIRES
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# IMPORT DES MODULES UTILITAIRES
try:
    from utils.procedure_gen import generate_procedure_with_model, init_vector_store, load_data, find_similar_notes
except ImportError as e:
    st.error(f"Erreur d'importation des modules utilitaires: {e}")
    st.warning("Assurez-vous que les modules dans le dossier 'utils' sont correctement installés.")

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Procédure Générée avec RAG",
    page_icon="📋",
    layout="wide"
)

# CONSTANTES DES MODÈLES DISPONIBLES
MODELS = {
    "mistral-saba-24b": {
        "name": "Mistral Saba 24B",
        "description": "Modèle équilibré pour une génération de qualité avec un bon rapport précision/vitesse",
        "provider": "Groq",
        "temperature": 0.3,
        "max_tokens": 4096
    },
    "llama-3.3-70b-versatile": {
        "name": "LLama 3.3 70B Versatile",
        "description": "Modèle de grande taille avec des capacités avancées de raisonnement et d'analyse",
        "provider": "Groq",
        "temperature": 0.25,
        "max_tokens": 4096
    },
    "qwen-qwq-32b": {
        "name": "Qwen QWQ 32B",
        "description": "Modèle performant avec une bonne compréhension contextuelle",
        "provider": "Groq",
        "temperature": 0.35,
        "max_tokens": 4096
    }
}

# FONCTION POUR SAUVEGARDER LES PROCÉDURES GÉNÉRÉES
def save_procedure(procedure, model_id, note_title, similar_notes=None):
    data_file = Path("data/donnees.json")
    try:
        # Charger les données existantes
        data = {}
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Si la structure est un dictionnaire avec "dossiers"
        if "dossiers" in data:
            # Trouver le prochain numéro de dossier
            next_num = max([d.get("numero", 0) for d in data["dossiers"]], default=0) + 1
            
            # Extraire les étapes de la procédure (conversion du tableau markdown)
            procedure_lines = procedure.strip().split('\n')
            etapes = []
            
            # Ignorer les lignes d'en-tête et de séparation du tableau markdown
            start_parsing = False
            for line in procedure_lines:
                line = line.strip()
                if line.startswith('| ---'):
                    start_parsing = True
                    continue
                
                if start_parsing and line.startswith('|'):
                    # Extraire les données de chaque colonne
                    cols = [col.strip() for col in line.split('|')[1:-1]]
                    if len(cols) >= 6:  # N°, Activités, Description, Acteurs, Documents, Applications
                        etape = {
                            "N°": cols[0], 
                            "Activités": cols[1],
                            "Description": cols[2],
                            "Acteurs": cols[3],
                            "Documents": cols[4],
                            "Applications": cols[5]
                        }
                        etapes.append(etape)
            
            # Créer un nouveau dossier avec la note et sa procédure
            nouveau_dossier = {
                "numero": next_num,
                "nom": f"Procédure pour {note_title}",
                "note_circulaire": {
                    "texte": st.session_state.get("note_circulaire", "")
                },
                "procedures": [
                    {
                        "numero": f"{next_num}.1",
                        "modele": model_id,
                        "etapes": etapes,
                        "notes_similaires": similar_notes if similar_notes else []  # Ajouter les notes similaires utilisées
                    }
                ]
            }
            
            data["dossiers"].append(nouveau_dossier)
        else:
            # Structure alternative (pour rétrocompatibilité)
            if "procedures" not in data:
                data["procedures"] = []
            
            data["procedures"].append({
                "titre": f"Procédure pour {note_title}",
                "contenu": procedure,
                "modele": model_id,
                "note_source": note_title,
                "notes_similaires": similar_notes if similar_notes else []  # Ajouter les notes similaires utilisées
            })
        
        # Sauvegarder les données
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde de la procédure: {e}")
        return False

# FONCTION POUR GÉNÉRER LA PROCÉDURE AVEC RAG
def generate_procedure_rag(note_circulaire, model_id, api_key=None):
    """Génère une procédure en utilisant le RAG pour trouver des notes similaires"""
    
    similar_notes_found = []
    similar_notes_info = []
    
    with st.spinner("Recherche de notes circulaires similaires..."):
        # Charger toutes les données
        all_data = load_data()
        
        # Préparer les documents pour la recherche sémantique
        docs = []
        notes_map = {}
        procs_map = {}
        
        # Vérifier si la structure est celle attendue (dossiers)
        if isinstance(all_data, dict) and "docs" in all_data:
            # Format déjà traité par la fonction load_data
            docs = all_data.get("docs", [])
            notes_map = all_data.get("notes_map", {})
            procs_map = all_data.get("procedures_map", {})
            
            # Debug information
            st.write(f"Données chargées: {len(docs)} documents, {len(notes_map)} notes, {len(procs_map)} procédures")
        
        # Si docs est vide, essayer d'extraire les données d'une autre structure
        if not docs and isinstance(all_data, dict) and "dossiers" in all_data:
            for dossier in all_data.get("dossiers", []):
                num = dossier.get("numero")
                note = dossier.get("note_circulaire", {})
                texte = note.get("texte", "") if isinstance(note, dict) else ""
                
                if texte and num:
                    from langchain.schema import Document
                    docs.append(Document(
                        page_content=texte, 
                        metadata={
                            'numero': num, 
                            'nom': dossier.get('nom', '')
                        }
                    ))
                    notes_map[num] = texte
                    procs_map[num] = dossier.get("procedures", [])
        
        # Vérifier qu'on a des données à traiter
        if not docs:
            st.warning("⚠️ Aucun document trouvé dans la base de données pour la recherche RAG.")
            return generate_procedure_with_model(note_circulaire, model_id=model_id, api_key=api_key), []
                
        # Initialiser la base vectorielle
        vectorstore = init_vector_store(docs)
        
        if not vectorstore:
            st.error("❌ Erreur lors de l'initialisation de la base vectorielle.")
            return generate_procedure_with_model(note_circulaire, model_id=model_id, api_key=api_key), []
        
        # Rechercher des notes similaires
        similar_notes_found = find_similar_notes(vectorstore, note_circulaire)
        
        # Créer une liste d'infos sur les notes similaires pour la sauvegarde
        for note in similar_notes_found:
            similar_notes_info.append({
                "id": note['id'],
                "titre": note['titre'],
                "score": note.get('score', 0)
            })
        
        # Afficher les résultats de la recherche avec message explicite
        if similar_notes_found and len(similar_notes_found) > 0:
            st.success(f"✅ {len(similar_notes_found)} note(s) circulaire(s) similaire(s) trouvée(s) ! Ces notes serviront d'inspiration pour la génération.")
            
            # Afficher un message spécifique pour la première note la plus similaire
            if len(similar_notes_found) > 0:
                most_similar = similar_notes_found[0]
                score_percent = f"{most_similar.get('score', 0) * 100:.1f}%" if most_similar.get('score') else "N/A"
                
                # Message en évidence pour la note la plus similaire
                st.markdown(f"""
                <div style="padding: 15px; background-color: #e6f7ff; border-radius: 5px; border-left: 5px solid #1890ff; margin-bottom: 20px;">
                    <h4 style="margin-top: 0">🔍 Note circulaire la plus similaire détectée</h4>
                    <p><strong>ID de la note:</strong> {most_similar['id']}</p>
                    <p><strong>Titre:</strong> {most_similar['titre']}</p>
                    <p><strong>Similarité:</strong> {score_percent}</p>
                    <p>Cette note sera utilisée comme principale source d'inspiration pour la génération de la procédure.</p>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("🔍 Voir toutes les notes circulaires similaires"):
                for i, note in enumerate(similar_notes_found, 1):
                    score = note.get('score', 0)
                    score_percent = f"{score * 100:.1f}%" if score else "N/A"
                    st.markdown(f"**Note #{i} - ID: {note['id']} - Similarité: {score_percent}**")
                    st.markdown(f"**Titre:** {note['titre']}")
                    st.markdown("**Extrait:**")
                    st.text(note['content'][:200] + "..." if len(note['content']) > 200 else note['content'])
                    st.markdown("---")
                    
            st.info("⚙️ Le modèle va s'inspirer de ces notes pour générer une procédure plus pertinente.")
        else:
            # Message en évidence quand aucune note similaire n'est trouvée
            st.warning("""
            ⚠️ Aucune note circulaire similaire n'a été trouvée dans la base de données.
            
            La procédure sera générée sans exemple spécifique, uniquement à partir de la note fournie et des connaissances générales du modèle.
            """)
        
        # Générer la procédure avec le modèle et RAG
        with st.spinner(f"Génération de la procédure avec {MODELS[model_id]['name']}..."):
            try:
                # Appeler la fonction de génération de procédure avec les paramètres appropriés
                procedure = generate_procedure_with_model(query=note_circulaire, model_id=model_id, api_key=api_key)
                
                # Enregistrer les infos sur les notes similaires dans l'état de session
                st.session_state.similar_notes = similar_notes_found
                st.session_state.similar_notes_info = similar_notes_info
                
                # Retourner la procédure et les infos des notes similaires
                return procedure, similar_notes_info
            except Exception as e:
                st.error(f"Erreur lors de la génération: {e}")
                return None, []

def split_procedure_tables(procedure_text):
    """Sépare les tableaux de la procédure générée en tableau des étapes et tableau I/O"""
    if not procedure_text:
        return "", ""
    
    # Récupérer les deux sections principales
    parts = procedure_text.split("2. **")
    if len(parts) < 2:
        parts = procedure_text.split("Tableau des Entrées/Sorties")
        if len(parts) < 2:
            parts = procedure_text.split("Tableau I/O")
            if len(parts) < 2:
                return procedure_text, ""
    
    etapes_section = parts[0]
    io_section = "Tableau des Entrées/Sorties" + parts[1] if len(parts) > 1 else ""
    
    # Extraire le tableau des étapes
    etapes_lines = []
    capture_etapes = False
    for line in etapes_section.split("\n"):
        if "|" in line:
            if "N°" in line or "---" in line or any(char.isdigit() for char in line):
                capture_etapes = True
            if capture_etapes:
                etapes_lines.append(line.strip())
    
    # Extraire le tableau I/O s'il existe
    io_lines = []
    capture_io = False
    for line in io_section.split("\n"):
        if "|" in line:
            if "Evènement" in line or "Entrée" in line or "Sortie" in line:
                capture_io = True
            if capture_io:
                io_lines.append(line.strip())
    
    # Si on n'a pas trouvé de tableau I/O, utiliser le format standard
    if not io_lines:
        io_text = """| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | … | … |
| Sortie | … | … |"""
    else:
        io_text = "\n".join(io_lines)
    
    # Ajouter la ligne de séparation si nécessaire pour le tableau des étapes
    if len(etapes_lines) > 0 and not any("---" in line for line in etapes_lines):
        etapes_lines.insert(1, "| --- | --- | --- | --- | --- | --- |")
    
    return "\n".join(etapes_lines), io_text

# AFFICHAGE DE LA PAGE
def main():
    st.title("🔄 Procédure Générée avec RAG")
    
    # Récupérer la clé API Groq si définie dans les variables d'environnement
    api_key = os.getenv("GROQ_API_KEY")
    
    # Vérifier la présence de la note circulaire
    if not st.session_state.get("note_circulaire"):
        st.warning(
            "⚠️ Aucune note circulaire n'est disponible. Veuillez d'abord saisir ou téléverser une note dans la page 1."
        )
        st.markdown("[Retour à la page d'entrée de note circulaire](/)")
        return

    # Affichage du contenu de la note
    note_content = st.session_state.get("note_circulaire", "")
    note_title = st.session_state.get("note_title", "Note sans titre")
    with st.expander("📄 Voir la note circulaire source"):
        st.subheader(note_title)
        st.write(note_content)
    
    # Interface de génération
    st.subheader("🤖 Procédure générée")
    
    # Affichage de la procédure générée
    if st.session_state.get("procedure_generee"):
        st.markdown(st.session_state.procedure_generee)
        
        # Afficher les détails du modèle utilisé
        if st.session_state.get("model_selected"):
            with st.expander("ℹ️ Détails du modèle utilisé"):
                model_id = st.session_state.model_selected
                st.write(f"**Modèle**: {MODELS[model_id]['name']}")
                st.write(f"**Description**: {MODELS[model_id]['description']}")
                st.write(f"**Fournisseur**: {MODELS[model_id]['provider']}")
    
    # Interface de génération
    st.subheader("🤖 Générer une procédure avec aide de RAG")
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_model = st.selectbox(
            "Sélectionnez un modèle d'IA:",
            options=list(MODELS.keys()),
            format_func=lambda x: MODELS[x]["name"],
            index=0
        )
        st.info(f"ℹ️ **{MODELS[selected_model]['name']}** : {MODELS[selected_model]['description']}")
    with col2:
        st.markdown("### Système RAG")
        if not api_key:
            api_key = st.text_input("Clé API Groq (optionnelle):", type="password")
    
    # Bouton pour générer la procédure
    if st.button("🚀 Générer la procédure", use_container_width=True):
        procedure, similar_notes_info = generate_procedure_rag(note_content, selected_model, api_key)
        if procedure:
            st.session_state.procedure_generee = procedure
            st.session_state.procedure_model = selected_model
            st.session_state.similar_notes_info = similar_notes_info
            
            # Sauvegarder la procédure générée
            success = save_procedure(procedure, selected_model, note_title, similar_notes_info)
            if success:
                st.success("✅ Procédure générée et sauvegardée avec succès!")
            
            # Forcer le rafraîchissement de la page pour afficher les résultats
            st.rerun()

    # Affichage de la procédure générée
    if st.session_state.get("procedure_generee"):
        st.subheader("📋 Procédure Générée")
        model_used = st.session_state.get("procedure_model", selected_model)
        
        # Afficher les informations sur la méthode de génération
        similar_notes = st.session_state.get("similar_notes", [])
        similar_notes_info = st.session_state.get("similar_notes_info", [])
        
        if similar_notes and len(similar_notes) > 0:
            st.success(f"✅ Procédure générée avec l'aide de {len(similar_notes)} note(s) similaire(s)")
            st.caption(f"Générée avec le modèle: {MODELS[model_used]['name']} assisté par RAG")
            
            # Afficher la liste des IDs des notes similaires utilisées
            if similar_notes_info and len(similar_notes_info) > 0:
                ids_list = ", ".join([f"ID {note['id']}" for note in similar_notes_info])
                st.markdown(f"**Notes utilisées comme inspiration:** {ids_list}")
            
            # Badge pour indiquer le mode de génération
            st.markdown("""
            <div style="background-color:#0066cc; color:white; padding:8px; border-radius:5px; display:inline-block; margin-bottom:15px">
            <span style="font-weight:bold">🔄 Génération assistée par RAG</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption(f"Générée avec le modèle: {MODELS[model_used]['name']} sans exemples similaires")
            
            # Badge pour indiquer le mode de génération
            st.markdown("""
            <div style="background-color:#f39c12; color:white; padding:8px; border-radius:5px; display:inline-block; margin-bottom:15px">
            <span style="font-weight:bold">🤔 Génération sans exemples similaires</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Séparer et afficher les deux tableaux
        etapes_table, io_table = split_procedure_tables(st.session_state.procedure_generee)
        
        # Afficher le tableau des étapes
        st.subheader("📋 Tableau des Étapes")
        st.markdown(etapes_table)
        
        # Afficher le tableau I/O
        st.subheader("🔄 Tableau des Entrées/Sorties")
        st.markdown(io_table)

        # Options de navigation et téléchargement
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊 Voir le Logigramme", use_container_width=True):
                st.session_state.redirect_to_page3 = True
                st.query_params.update({"page": "3"})
        with c2:
            if st.button("💬 Poser des Questions", use_container_width=True):
                st.session_state.redirect_to_page4 = True
                st.query_params.update({"page": "4"})
        with c3:
            procedure_md = st.session_state.procedure_generee
            st.download_button(
                label="⬇️ Télécharger (MD)",
                data=procedure_md,
                file_name=f"procedure_{note_title.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )

    # Détails techniques du modèle et du RAG
    if st.session_state.get("procedure_generee"):
        with st.expander("🔍 Détails techniques du système RAG"):
            # Information sur les notes similaires utilisées
            similar_notes = st.session_state.get("similar_notes", [])
            if similar_notes and len(similar_notes) > 0:
                st.markdown("### 📑 Notes circulaires similaires utilisées")
                for i, note in enumerate(similar_notes, 1):
                    score = note.get('score', 0)
                    score_percent = f"{score * 100:.1f}%" if score else "N/A"
                    st.markdown(f"**Note #{i} - ID: {note['id']} - Similarité: {score_percent}**")
                    st.markdown(f"**Titre:** {note['titre']}")
                    with st.expander(f"Voir le contenu de la note #{i}"):
                        st.text(note['content'])
            else:
                st.warning("⚠️ Aucune note circulaire similaire n'a été utilisée pour cette génération.")
            
            st.markdown("""
            ### 🧠 Système de RAG (Retrieval-Augmented Generation)
            
            Le processus de génération de procédure utilise le système RAG pour:
            1. **Recherche sémantique** - Trouver des notes circulaires similaires dans la base de données
            2. **Sélection des exemples** - Choisir les procédures associées les plus pertinentes
            3. **Contexte enrichi** - Fournir ces exemples au modèle pour guider la génération
            4. **Génération améliorée** - Produire une procédure en s'inspirant des exemples tout en respectant le contenu spécifique de la note circulaire
            
            Ce processus permet d'obtenir des procédures plus pertinentes et cohérentes avec les standards existants.
            """)
            
            model_used = st.session_state.get("procedure_model", selected_model)
            st.markdown(f"**Modèle**: {MODELS[model_used]['name']}")
            st.markdown(f"**Fournisseur**: {MODELS[model_used]['provider']}")
            st.markdown(f"**Température**: {MODELS[model_used]['temperature']}")
            
            # Exemple de prompt utilisé
            st.markdown("### Structure du prompt utilisé")
            st.code("""
# MISSION
Expert en conformité bancaire, créer une procédure détaillée et complète à partir d'une note circulaire.

# CONTEXTE
Voici des exemples similaires identifiés dans notre base de données que vous pouvez utiliser comme inspiration:
{examples_context}

# NOUVELLE NOTE CIRCULAIRE À TRAITER
{query}

# INSTRUCTIONS PRÉCISES
1. Analysez en profondeur la note circulaire fournie
2. Générez une procédure bancaire complète...
...
            """)

if __name__ == "__main__":
    main()
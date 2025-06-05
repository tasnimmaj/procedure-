"""
Page 2: Procédure Générée avec RAG
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path

# CONFIGURATION DE LA PAGE - DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="Procédure Générée avec RAG",
    page_icon="📋",
    layout="wide"
)

# Maintenant on peut importer et appliquer le thème
from utils.styles import apply_green_theme

# Appliquer le thème après set_page_config
apply_green_theme()

# AJOUTER LE RÉPERTOIRE PARENT AU PATH POUR IMPORTER LES MODULES UTILITAIRES
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# IMPORT DES MODULES UTILITAIRES
try:
    from utils.procedure_gen import generate_procedure_with_model, init_vector_store, load_data, find_similar_notes, MODELS
except ImportError as e:
    st.error(f"Erreur d'importation des modules utilitaires: {e}")
    st.warning("Assurez-vous que les modules dans le dossier 'utils' sont correctement installés.")

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
def generate_procedure_rag(note_circulaire, model_id, api_key=None, num_io_rows=3):
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
            docs = all_data.get("docs", [])
            notes_map = all_data.get("notes_map", {})
            procs_map = all_data.get("procedures_map", {})
            
            st.write(f"Données chargées: {len(docs)} documents, {len(notes_map)} notes, {len(procs_map)} procédures")
        
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
        
        if not docs:
            st.warning("⚠️ Aucun document trouvé dans la base de données pour la recherche RAG.")
            result = generate_procedure_with_model(note_circulaire, model_id=model_id, api_key=api_key, num_io_rows=num_io_rows)
            return result, []
                
        vectorstore = init_vector_store(docs)
        
        if not vectorstore:
            st.error("❌ Erreur lors de l'initialisation de la base vectorielle.")
            result = generate_procedure_with_model(note_circulaire, model_id=model_id, api_key=api_key, num_io_rows=num_io_rows)
            return result, []
        
        similar_notes_found = find_similar_notes(vectorstore, note_circulaire)
        
        for note in similar_notes_found:
            similar_notes_info.append({
                "id": note['id'],
                "titre": note['titre'],
                "score": note.get('score', 0)
            })
        
        if similar_notes_found and len(similar_notes_found) > 0:
            st.success(f"✅ {len(similar_notes_found)} note(s) circulaire(s) similaire(s) trouvée(s) !")
            
            if len(similar_notes_found) > 0:
                most_similar = similar_notes_found[0]
                score_percent = f"{most_similar.get('score', 0) * 100:.1f}%" if most_similar.get('score') else "N/A"
                
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
            st.warning("""
            ⚠️ Aucune note circulaire similaire n'a été trouvée dans la base de données.
            
            La procédure sera générée sans exemple spécifique, uniquement à partir de la note fournie et des connaissances générales du modèle.
            """)
        
        with st.spinner(f"Génération de la procédure avec {MODELS[model_id]['name']}..."):
            try:
                result = generate_procedure_with_model(
                    query=note_circulaire, 
                    model_id=model_id, 
                    api_key=api_key,
                    vectorstore=vectorstore,
                    notes_map=notes_map,
                    procedures_map=procs_map,
                    num_io_rows=num_io_rows
                )
                
                st.session_state.similar_notes = similar_notes_found
                st.session_state.similar_notes_info = similar_notes_info
                
                return result, similar_notes_info
            except Exception as e:
                st.error(f"Erreur lors de la génération: {e}")
                return None, []

def extract_procedure_components(procedure_result):
    """Extrait les composants de la procédure avec validation du format Markdown"""
    
    # Si procedure_result est un dictionnaire (nouveau format)
    if isinstance(procedure_result, dict):
        procedure_text = procedure_result.get('procedure', '')
        io_table = procedure_result.get('io_table', '')
    else:
        # Ancien format (rétrocompatibilité) 
        procedure_text = procedure_result
        io_table = ""

    # Initialiser les composants
    components = {
        "etapes": "",
        "io": ""
    }

    # Fonction helper pour valider/formater une table markdown
    def format_markdown_table(content, headers):
        if not content:
            # Créer une table vide avec les en-têtes
            separator = "|" + "|".join([" --- " for _ in headers]) + "|"
            return "\n".join([
                "|" + "|".join(headers) + "|",
                separator
            ])
        
        lines = content.strip().split("\n")
        formatted_lines = []
        
        # Vérifier si la première ligne est un en-tête markdown valide
        if not lines[0].startswith("|") or not lines[0].endswith("|"):
            # Si non, créer un nouvel en-tête
            formatted_lines.append("|" + "|".join(headers) + "|")
            formatted_lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
            
            # Formater les données existantes
            for line in lines:
                if line.strip():
                    cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                    if len(cells) >= len(headers):
                        formatted_lines.append("|" + "|".join(cells[:len(headers)]) + "|")
        else:
            # Si le format est déjà correct, garder tel quel
            formatted_lines = lines
            
            # S'assurer qu'il y a une ligne de séparation
            if len(formatted_lines) > 1 and not "---" in formatted_lines[1]:
                formatted_lines.insert(1, "|" + "|".join([" --- " for _ in headers]) + "|")
        
        return "\n".join(formatted_lines)

    # Formater le tableau I/O
    io_headers = ["Evènement", "Processus en interface", "Description du processus en interface"]
    components["io"] = format_markdown_table(io_table, io_headers)
    
    # Extraire et formater le tableau des étapes
    if procedure_text:
        etapes_lines = []
        step_headers = ["N°", "Activités", "Description", "Acteurs", "Documents", "Applications"]
        
        # Parcourir les lignes pour trouver le tableau des étapes
        lines = procedure_text.split("\n")
        in_table = False
        for line in lines:
            if "| N°" in line or "| No." in line or "| Numéro" in line:
                in_table = True
                etapes_lines = [line]
            elif in_table and line.strip().startswith("|"):
                etapes_lines.append(line)
            elif in_table and not line.strip().startswith("|"):
                break
                
        if etapes_lines:
            components["etapes"] = format_markdown_table("\n".join(etapes_lines), step_headers)
    
    # Sauvegarder pour la page 3
    if components["etapes"]:
        st.session_state.generated_markdown_table = components["etapes"]
        st.session_state.has_generated_table = True

    return components

# FONCTION PRINCIPALE
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

    st.title("🔄 Procédure Générée avec RAG")
    
    api_key = os.getenv("GROQ_API_KEY")
    
    if not st.session_state.get("note_circulaire"):
        st.warning(
            "⚠️ Aucune note circulaire n'est disponible. Veuillez d'abord saisir ou téléverser une note dans la page 1."
        )
        st.markdown("[Retour à la page d'entrée de note circulaire](/)")
        return

    model_selected = st.session_state.get("model_selected", "mistral-saba-24b")

    note_content = st.session_state.get("note_circulaire", "")
    note_title = st.session_state.get("note_title", "Note sans titre")
    
    with st.expander("📄 Voir la note circulaire source"):
        st.subheader(note_title)
        st.write(note_content)
    
    if not st.session_state.get("procedure_generee"):
        st.subheader("🤖 Génération de la procédure")
        st.info(f"""
        Le modèle sélectionné est: **{MODELS[model_selected]['name']}**  
        Description: {MODELS[model_selected]['description']}
        """)
        
        # Contrôle du nombre de lignes pour le tableau I/O
        col1, col2 = st.columns(2)
        with col1:
            num_io_rows = st.number_input(
                "Nombre de lignes pour le tableau Entrées/Sorties", 
                min_value=2, 
                max_value=10, 
                value=3, 
                help="Nombre d'événements à générer dans le tableau I/O"
            )
        
        if not api_key:
            api_key = st.text_input("Clé API Groq (optionnelle):", type="password")
        
        if st.button("🚀 Générer la procédure avec RAG", use_container_width=True):
            procedure_result, similar_notes_info = generate_procedure_rag(
                note_content, 
                model_selected, 
                api_key, 
                num_io_rows=num_io_rows
            )
            
            if procedure_result:
                st.session_state.procedure_generee = procedure_result
                st.session_state.procedure_model = model_selected
                st.session_state.similar_notes_info = similar_notes_info
                
                # Pour la sauvegarde, utiliser le texte de la procédure
                procedure_text = procedure_result.get('procedure', '') if isinstance(procedure_result, dict) else procedure_result
                success = save_procedure(procedure_text, model_selected, note_title, similar_notes_info)
                
                if success:
                    st.success("✅ Procédure générée et sauvegardée avec succès!")
                
                st.rerun()

    # Affichage de la procédure générée
    if st.session_state.get("procedure_generee"):
        st.subheader("📋 Procédure Générée")
        model_used = st.session_state.get("procedure_model", model_selected)
        
        # Afficher les informations sur la méthode de génération
        similar_notes = st.session_state.get("similar_notes", [])
        similar_notes_info = st.session_state.get("similar_notes_info", [])
        
        if similar_notes and len(similar_notes) > 0:
            st.success(f"✅ Procédure générée avec l'aide de {len(similar_notes)} note(s) similaire(s)")
            st.caption(f"Générée avec le modèle: {MODELS[model_used]['name']} assisté par RAG")
            
            if similar_notes_info and len(similar_notes_info) > 0:
                ids_list = ", ".join([f"ID {note['id']}" for note in similar_notes_info])
                st.markdown(f"**Notes utilisées comme inspiration:** {ids_list}")
            
            st.markdown("""
            <div style="background-color:#0066cc; color:white; padding:8px; border-radius:5px; display:inline-block; margin-bottom:15px">
            <span style="font-weight:bold">🔄 Génération assistée par RAG</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption(f"Générée avec le modèle: {MODELS[model_used]['name']} sans exemples similaires")
            
            st.markdown("""
            <div style="background-color:#f39c12; color:white; padding:8px; border-radius:5px; display:inline-block; margin-bottom:15px">
            <span style="font-weight:bold">🤔 Génération sans exemples similaires</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Extraire les composants
        procedure_components = extract_procedure_components(st.session_state.procedure_generee)
        
        # Afficher le tableau des étapes
        st.subheader("📋 Tableau des Étapes")
        if procedure_components["etapes"]:
            st.markdown(procedure_components["etapes"])
        else:
            st.info("Aucun tableau des étapes détecté dans la procédure générée.")
        
        # Afficher le tableau I/O 
        st.subheader("🔄 Tableau des Entrées/Sorties")
        if procedure_components["io"]:
            st.markdown(procedure_components["io"])
            st.caption("🤖 Tableau généré automatiquement par le modèle")
        else:
            st.info("Aucun tableau entrées/sorties généré.")
            # DEBUG: Afficher le contenu brut pour vérifier
            if isinstance(st.session_state.procedure_generee, dict):
                st.write("DEBUG - Clés disponibles:", list(st.session_state.procedure_generee.keys()))
                st.write("DEBUG - io_table:", st.session_state.procedure_generee.get('io_table', 'VIDE'))

if __name__ == "__main__":
    main()
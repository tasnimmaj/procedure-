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
    from utils.procedure_gen import generate_procedure_with_model, init_vector_store, load_data, find_similar_notes, MODELS
except ImportError as e:
    st.error(f"Erreur d'importation des modules utilitaires: {e}")
    st.warning("Assurez-vous que les modules dans le dossier 'utils' sont correctement installés.")

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Procédure Générée avec RAG",
    page_icon="📋",
    layout="wide"
)

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

def extract_procedure_components(procedure_text):
    """Extrait le tableau des étapes, le tableau I/O et les scénarios de la procédure"""
    if not procedure_text:
        return {"etapes": "", "io": "", "scenarios": "", "scenarios_ok": "", "scenarios_ko": ""}
    
    # Initialiser les composants
    components = {
        "etapes": "",
        "io": "",
        "scenarios": "",
        "scenarios_ok": "",
        "scenarios_ko": ""
    }
    
    # Extraire les sections par analyse ligne par ligne
    current_section = []
    current_section_type = None
    
    lines = procedure_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Détecter le début du tableau des étapes
        if "| N°" in line or "| No." in line or "| Numéro" in line:
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "etapes"
            i += 1
            continue
            
        # Détecter le début du tableau I/O
        if ("| Evènement" in line or "| Événement" in line or "| Entrée" in line) and "| Sortie" in line:
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "io"
            i += 1
            continue
            
        # Détecter le début des scénarios généraux
        if ("# Scénarios" in line or "## Scénarios" in line) and not "OK" in line and not "KO" in line:
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios"
            i += 1
            continue
            
        # Détecter le début des scénarios OK
        if ("# Scénario OK" in line or "## Scénario OK" in line or 
            "# Scénarios OK" in line or "## Scénarios OK" in line or
            "# Scénario nominal" in line or "## Scénario nominal" in line):
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios_ok"
            i += 1
            continue
            
        # Détecter le début des scénarios KO
        if ("# Scénario KO" in line or "## Scénario KO" in line or 
            "# Scénarios KO" in line or "## Scénarios KO" in line or
            "# Scénario alternatif" in line or "## Scénario alternatif" in line):
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios_ko"
            i += 1
            continue
        
        # Si on est dans une section identifiée, ajouter la ligne
        if current_section_type:
            # Si on trouve un titre qui pourrait indiquer le début d'une nouvelle section
            if (line.startswith("## ") or line.startswith("# ")) and len(current_section) > 0:
                # Vérifier si c'est une section que nous traitons spécifiquement
                if "Entrées/Sorties" in line or "I/O" in line:
                    # Sauvegarder la section précédente
                    if current_section_type and current_section:
                        components[current_section_type] = "\n".join(current_section)
                    # Commencer la nouvelle section I/O
                    current_section = [line]
                    current_section_type = "io"
                elif "Scénario" in line and "OK" in line or "nominal" in line:
                    # Sauvegarder la section précédente
                    if current_section_type and current_section:
                        components[current_section_type] = "\n".join(current_section)
                    # Commencer la nouvelle section scénarios OK
                    current_section = [line]
                    current_section_type = "scenarios_ok"
                elif "Scénario" in line and "KO" in line or "alternatif" in line:
                    # Sauvegarder la section précédente
                    if current_section_type and current_section:
                        components[current_section_type] = "\n".join(current_section)
                    # Commencer la nouvelle section scénarios KO
                    current_section = [line]
                    current_section_type = "scenarios_ko"
                elif "Scénarios" in line and not "OK" in line and not "KO" in line:
                    # Sauvegarder la section précédente
                    if current_section_type and current_section:
                        components[current_section_type] = "\n".join(current_section)
                    # Commencer la nouvelle section scénarios généraux
                    current_section = [line]
                    current_section_type = "scenarios"
                else:
                    # C'est un autre type de titre dans la section courante
                    current_section.append(line)
            else:
                # Ajouter la ligne à la section courante
                current_section.append(line)
        else:
            # Si on n'est pas encore dans une section identifiée mais qu'on trouve un titre pertinent
            if line.startswith("# ") or line.startswith("## "):
                if "Étapes" in line or "Etapes" in line or "Procédure" in line:
                    current_section = [line]
                    current_section_type = "etapes"
                elif "Entrées/Sorties" in line or "I/O" in line:
                    current_section = [line]
                    current_section_type = "io"
                elif "Scénario" in line and "OK" in line:
                    current_section = [line]
                    current_section_type = "scenarios_ok"
                elif "Scénario" in line and "KO" in line:
                    current_section = [line]
                    current_section_type = "scenarios_ko"
                elif "Scénarios" in line:
                    current_section = [line]
                    current_section_type = "scenarios"
        
        i += 1
    
    # Sauvegarder la dernière section
    if current_section_type and current_section:
        components[current_section_type] = "\n".join(current_section)
    
    # S'assurer que le tableau des étapes a un format cohérent
    if components["etapes"] and "| " in components["etapes"] and not "| ---" in components["etapes"]:
        lines = components["etapes"].split("\n")
        header_line_index = -1
        
        # Trouver la ligne d'en-tête du tableau
        for idx, line in enumerate(lines):
            if "| N°" in line or "| No." in line or "| Numéro" in line:
                header_line_index = idx
                break
        
        if header_line_index >= 0:
            header_line = lines[header_line_index]
            # Compter le nombre de colonnes
            num_columns = header_line.count("|") - 1
            separator_line = "| " + " --- |" * num_columns
            
            # Insérer la ligne de séparation après l'en-tête
            lines.insert(header_line_index + 1, separator_line)
            components["etapes"] = "\n".join(lines)
    
    # S'assurer que le tableau I/O a un format cohérent
    if components["io"] and "| " in components["io"] and not "| ---" in components["io"]:
        lines = components["io"].split("\n")
        header_line_index = -1
        
        # Trouver la ligne d'en-tête du tableau
        for idx, line in enumerate(lines):
            if ("| Evènement" in line or "| Événement" in line or "| Entrée" in line) and "| Sortie" in line:
                header_line_index = idx
                break
        
        if header_line_index >= 0:
            header_line = lines[header_line_index]
            # Compter le nombre de colonnes
            num_columns = header_line.count("|") - 1
            separator_line = "| " + " --- |" * num_columns
            
            # Insérer la ligne de séparation après l'en-tête
            lines.insert(header_line_index + 1, separator_line)
            components["io"] = "\n".join(lines)
    
    return components

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

    # Récupérer le modèle choisi dans la page 1
    model_selected = st.session_state.get("model_selected", "mistral-saba-24b")  # Valeur par défaut

    # Affichage du contenu de la note
    note_content = st.session_state.get("note_circulaire", "")
    note_title = st.session_state.get("note_title", "Note sans titre")
    with st.expander("📄 Voir la note circulaire source"):
        st.subheader(note_title)
        st.write(note_content)
    
    # Si aucune procédure n'a encore été générée, proposer de le faire
    if not st.session_state.get("procedure_generee"):
        st.subheader("🤖 Génération de la procédure")
        st.info(f"""
        Le modèle sélectionné est: **{MODELS[model_selected]['name']}**  
        Description: {MODELS[model_selected]['description']}
        """)
        
        # Optionnellement, permettre de fournir une clé API
        if not api_key:
            api_key = st.text_input("Clé API Groq (optionnelle):", type="password")
        
        # Bouton pour générer la procédure avec le modèle choisi en page 1
        if st.button("🚀 Générer la procédure avec RAG", use_container_width=True):
            procedure, similar_notes_info = generate_procedure_rag(note_content, model_selected, api_key)
            if procedure:
                st.session_state.procedure_generee = procedure
                st.session_state.procedure_model = model_selected
                st.session_state.similar_notes_info = similar_notes_info
                
                # Sauvegarder la procédure générée
                success = save_procedure(procedure, model_selected, note_title, similar_notes_info)
                if success:
                    st.success("✅ Procédure générée et sauvegardée avec succès!")
                
                # Forcer le rafraîchissement de la page pour afficher les résultats
                st.rerun()

    # Affichage de la procédure générée (si disponible)
    if st.session_state.get("procedure_generee"):
        st.subheader("📋 Procédure Générée")
        model_used = st.session_state.get("procedure_model", model_selected)
        
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
        
        # Extraire les composants de la procédure
        procedure_components = extract_procedure_components(st.session_state.procedure_generee)
          # Afficher le tableau des étapes
        st.subheader("📋 Tableau des Étapes")
        if procedure_components["etapes"]:
            st.markdown(procedure_components["etapes"])
        else:
            st.info("Aucun tableau des étapes détecté dans la procédure générée.")
        
        # Afficher le tableau I/O (obligatoire)
        st.subheader("🔄 Tableau des Entrées/Sorties")
        if procedure_components["io"] and "| Entrée |" in procedure_components["io"] and "| Sortie |" in procedure_components["io"]:
            st.markdown(procedure_components["io"])
        else:
            default_io = """| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | Réception de la note circulaire | Déclenchement du processus suite à une nouvelle note circulaire |
| Sortie | Application de la note | Mise en place effective des directives de la note circulaire |"""
            st.markdown(default_io)
              # Section des scénarios (obligatoire)
        st.subheader("📝 Scénarios de validation")
        
        # Afficher les scénarios OK/KO s'ils existent
        if procedure_components["scenarios_ok"] and procedure_components["scenarios_ok"].strip():
            st.markdown("### ✅ Scénario OK / Nominal")
            st.markdown(procedure_components["scenarios_ok"])
        else:
            st.markdown("### ✅ Scénario OK / Nominal")
            st.markdown("""
            1. **Validation complète de la procédure**
               - Tous les critères de la note circulaire sont respectés
               - Les documents requis sont complets et valides
               - Les validations sont obtenues dans les délais impartis
               - Le processus respecte toutes les étapes définies
               - L'archivage est effectué selon les normes""")
        
        if procedure_components["scenarios_ko"] and procedure_components["scenarios_ko"].strip():
            st.markdown("### ❌ Scénario KO / Alternatif")
            st.markdown(procedure_components["scenarios_ko"])
        else:
            st.markdown("### ❌ Scénario KO / Alternatif")
            st.markdown("""
            1. **Non-validation de la procédure**
               - Non-respect d'un ou plusieurs critères essentiels
               - Documents manquants ou non conformes aux exigences
               - Délais de validation dépassés
               - Processus bloqué nécessitant une intervention
               - Non-respect des règles d'archivage""")

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
            
            model_used = st.session_state.get("procedure_model", model_selected)
            st.markdown(f"**Modèle**: {MODELS[model_used]['name']}")
            st.markdown(f"**Fournisseur**: {MODELS[model_used]['provider']}")
            st.markdown(f"**Température**: {MODELS[model_used]['temperature']}")

if __name__ == "__main__":
    main()
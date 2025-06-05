import os
import json
from pathlib import Path
import time
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- Configuration ---
DATA_PATH = "data/donnees.json"
VS_DIR = "data/chroma_store"

# Paramètres optimisés
SIMILARITY_THRESHOLD = 0.2
MAX_NOTE_LENGTH = 500
MAX_EXAMPLES = 2
MIN_PROCEDURE_ROWS = 4
MAX_PROCEDURE_ROWS = 65

# --- Modèles disponibles ---
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

def get_api_key():
    """Récupère la clé API depuis les variables d'environnement"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ ERREUR: Clé API non trouvée!")
        print("🔧 SOLUTION:")
        print("   Windows: set GROQ_API_KEY=votre_clé_api")
        print("   Linux/Mac: export GROQ_API_KEY=\"votre_clé_api\"")
        print("\n📋 Puis redémarrez votre script.")
        raise ValueError("Clé API GROQ_API_KEY manquante dans les variables d'environnement")
    return api_key

def init_llm(model_id="mistral-saba-24b", api_key=None):
    """Initialise le modèle LLM avec les paramètres appropriés"""
    try:
        if not api_key:
            api_key = get_api_key()
            
        model_config = MODELS.get(model_id, MODELS["mistral-saba-24b"])
        
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_id,
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
        )
        
        print(f"✅ LLM initialisé: {model_config['name']}")
        return llm
    except Exception as e:
        raise Exception(f"❌ Erreur lors de l'initialisation du LLM: {e}")

def load_data(json_path=DATA_PATH):
    """Charge les données depuis le fichier JSON avec la structure attendue"""
    try:
        path = Path(json_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dossiers = data.get('dossiers', []) if isinstance(data, dict) else data
            
            docs = []
            notes_map = {}
            procedures_map = {}
            
            for dossier in dossiers:
                num = dossier.get('numero')
                nom = dossier.get('nom', '')
                
                note = dossier.get('note_circulaire', {})
                texte = note.get('texte', '') if isinstance(note, dict) else ''
                
                if texte:
                    docs.append(Document(
                        page_content=texte,
                        metadata={'numero': num, 'nom': nom}
                    ))
                    
                    notes_map[num] = texte
                    procedures_map[num] = dossier.get('procedures', [])
            
            print(f"📊 Données chargées: {len(docs)} documents")
            return {"docs": docs, "notes_map": notes_map, "procedures_map": procedures_map}
        
        print("⚠️ Fichier de données non trouvé, création d'une structure vide")
        return {"docs": [], "notes_map": {}, "procedures_map": {}}
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        return {"docs": [], "notes_map": {}, "procedures_map": {}}

def save_data(data, json_path=DATA_PATH):
    """Sauvegarde les données dans le fichier JSON"""
    try:
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Données sauvegardées dans {json_path}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des données: {e}")
        return False

def init_vector_store(documents=None):
    """Initialise ou charge la base vectorielle"""
    try:
        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        if documents and len(documents) > 0:
            import shutil
            if os.path.exists(VS_DIR):
                shutil.rmtree(VS_DIR, ignore_errors=True)
            
            Path(VS_DIR).mkdir(parents=True, exist_ok=True)
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(documents)
            vs = Chroma(collection_name='notes', persist_directory=VS_DIR, embedding_function=embedder)
            vs.add_documents(chunks)
            vs.persist()
            print(f"🗄️ Base vectorielle créée avec {len(chunks)} chunks")
            return vs
        
        if Path(VS_DIR).exists() and os.listdir(VS_DIR):
            try:
                vs = Chroma(collection_name='notes', persist_directory=VS_DIR, embedding_function=embedder)
                print(f"🗄️ Base vectorielle chargée depuis {VS_DIR}")
                return vs
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de la base vectorielle: {e}")
                import shutil
                shutil.rmtree(VS_DIR, ignore_errors=True)
        
        Path(VS_DIR).mkdir(parents=True, exist_ok=True)
        vs = Chroma(collection_name='notes', persist_directory=VS_DIR, embedding_function=embedder)
        vs.persist()
        print("🗄️ Base vectorielle vide créée")
        return vs
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base vectorielle: {e}")
        return None

def find_similar_notes(vectorstore, query, k=MAX_EXAMPLES):
    """Recherche les notes circulaires similaires à la requête"""
    if not vectorstore:
        print("⚠️ Base vectorielle non initialisée.")
        return []
        
    try:
        results = vectorstore.similarity_search_with_score(query, k=k*2)
        
        similar_notes = []
        for doc, score in results:
            note_id = doc.metadata.get('numero', '')
            note_title = doc.metadata.get('nom', 'Sans titre')
            similarity = 1.0 / (1.0 + score)
            
            if similarity >= 0.4:
                similar_notes.append({
                    'id': note_id,
                    'titre': note_title,
                    'score': similarity,
                    'content': doc.page_content[:300]
                })
        
        similar_notes = similar_notes[:1]
        print(f"🔍 Notes similaires trouvées: {len(similar_notes)}")
        return similar_notes
    except Exception as e:
        print(f"❌ Erreur lors de la recherche de notes similaires: {e}")
        return []

def generate_procedure_from_note_analysis(llm, query, num_steps):
    """Génère une procédure en analysant uniquement le contenu de la note circulaire"""
    
    template = """# MISSION CRITIQUE
Vous devez analyser cette note circulaire UNIQUEMENT et créer une procédure opérationnelle spécifique.

# INTERDICTIONS ABSOLUES
- Ne jamais utiliser d'exemples génériques
- Ne jamais copier des modèles existants
- Chaque étape DOIT découler directement du contenu de la note

# MÉTHODE D'ANALYSE OBLIGATOIRE
1. Lisez ENTIÈREMENT la note circulaire ci-dessous
2. Identifiez l'OBJECTIF principal mentionné dans la note
3. Repérez toutes les EXIGENCES spécifiques énumérées
4. Identifiez les CONTRÔLES requis
5. Déterminez les ACTEURS impliqués selon la note
6. Listez les DOCUMENTS mentionnés dans la note

# NOTE CIRCULAIRE À ANALYSER
{query}

# ANALYSE PRÉALABLE OBLIGATOIRE
Avant de créer les étapes, répondez mentalement à ces questions :
- Quel est le sujet principal de cette note ?
- Quelles sont les obligations spécifiques mentionnées ?
- Qui doit faire quoi selon cette note ?
- Quels documents sont requis d'après la note ?
- Quelles vérifications sont demandées ?

# FORMAT DE SORTIE STRICT
| N° | Activités | Description | Acteurs | Documents | Applications |
|---|---|---|---|---|---|
[EXACTEMENT {num_steps} étapes basées sur l'analyse de la note]

# RÈGLES DE GÉNÉRATION
- Chaque étape = un élément concret de la note commanceant par un verbe 
- Description de 35-80 mots expliquant le POURQUOI selon la note
- Acteurs = ceux mentionnés ou impliqués par la note
- Documents = ceux cités ou requis par la note
- Applications = systèmes logiques pour cette activité

# CONTRAINTES TECHNIQUES
- Remplacez "crédit" par "Financement" si applicable
- Remplacez "leasing" par "Leasing (Ijara)" si applicable
- Soyez PRÉCIS et SPÉCIFIQUE à cette note, pas générique

ANALYSEZ cette note circulaire et créez une procédure UNIQUE qui lui correspond !"""

    prompt = PromptTemplate(
        input_variables=['query', 'num_steps'],
        template=template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        result = chain.run({
            'query': query,
            'num_steps': num_steps
        })
        return result    
    except Exception as e:
        raise Exception(f"❌ Erreur lors de la génération basée sur l'analyse: {e}")

def generate_procedure_with_minimal_context(llm, query, similar_notes, num_steps):
    """Génère une procédure avec un contexte minimal pour éviter la copie"""
    
    domain_context = ""
    if similar_notes:
        note = similar_notes[0]
        content = note['content'][:200]
        
        if any(word in content.lower() for word in ['crédit', 'financement', 'prêt']):
            domain_context = "Domaine identifié: Financement bancaire"
        elif any(word in content.lower() for word in ['conformité', 'réglementation']):
            domain_context = "Domaine identifié: Conformité réglementaire"
        elif any(word in content.lower() for word in ['pme', 'entreprise']):
            domain_context = "Domaine identifié: Services aux entreprises"
        else:
            domain_context = "Domaine identifié: Services bancaires généraux"
    
    template = """# MISSION PRINCIPALE
Créez une procédure ORIGINALE basée UNIQUEMENT sur l'analyse de la note circulaire fournie.

# CONTEXTE MINIMAL (pour orientation générale seulement)
{domain_context}

# INTERDICTION ABSOLUE
- Ne copiez JAMAIS d'exemples existants
- Ne vous basez que sur le CONTENU de la note circulaire
- Chaque étape doit traiter un aspect SPÉCIFIQUE de la note

# NOTE CIRCULAIRE À ANALYSER EN DÉTAIL
{query}

# PROCESSUS D'ANALYSE OBLIGATOIRE
1. Identifiez l'OBJET principal de cette note circulaire
2. Listez toutes les EXIGENCES mentionnées dans le texte
3. Identifiez les ÉTAPES logiques pour appliquer ces exigences
4. Déterminez les ACTEURS nécessaires pour chaque étape
5. Identifiez les DOCUMENTS requis selon la note

# FORMAT DE SORTIE ATTENDU
| N° | Activités | Description | Acteurs | Documents | Applications |
|---|---|---|---|---|---|
[EXACTEMENT {num_steps} lignes basées sur l'analyse de la note]

# CONTRAINTES DE QUALITÉ
- Descriptions de 40-85 mots expliquant le processus spécifique
- Chaque étape doit correspondre à un élément de la note
- Soyez concret et opérationnel
- Adaptez "crédit" en "Mourabaha" et "leasing" en "Leasing (Ijara)"

# INSTRUCTION FINALE
Analysez cette note circulaire et créez des étapes qui reflètent EXACTEMENT ses exigences !"""

    prompt = PromptTemplate(
        input_variables=['query', 'domain_context', 'num_steps'],
        template=template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        result = chain.run({
            'query': query,
            'domain_context': domain_context,
            'num_steps': num_steps
        })
        return result
    except Exception as e:
        raise Exception(f"❌ Erreur lors de la génération avec contexte minimal: {e}")

def generate_io_table_with_model(llm, query, num_io_rows=3):
    """Génère un tableau entrées/sorties basé sur l'analyse de la note circulaire"""
    
    template = """# MISSION
Analysez cette note circulaire et créez EXACTEMENT {num_rows} événements d'entrées/sorties.

# NOTE CIRCULAIRE À ANALYSER
{query}

# ANALYSE REQUISE
1. Identifiez le déclencheur principal de la note
2. Identifiez les processus internes nécessaires
3. Identifiez les sorties/résultats attendus

# FORMAT DE SORTIE STRICT
| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
[EXACTEMENT {num_rows} lignes basées sur l'analyse de la note]

# INSTRUCTIONS
- Première ligne : événement déclencheur de la note
- Lignes intermédiaires : processus de traitement identifiés
- Dernière ligne : résultat/sortie final
- Descriptions détaillées de 25-60 mots
- Basez-vous UNIQUEMENT sur le contenu de la note circulaire

Analysez la note et créez les événements correspondants !"""

    prompt = PromptTemplate(
        input_variables=['query', 'num_rows'],
        template=template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        result = chain.run({
            'query': query[:1000],
            'num_rows': num_io_rows
        })
        
        if "| Evènement | Processus en interface | Description du processus en interface |" not in result:
            header = "| Evènement | Processus en interface | Description du processus en interface |"
            separator = "| --- | --- | --- |"
            result = f"{header}\n{separator}\n{result.strip()}"
        
        return result.strip()
    except Exception as e:
        raise Exception(f"❌ Erreur lors de la génération du tableau I/O: {e}")

def generate_procedure_with_io(llm, query, similar_notes=None, notes_map=None, procedures_map=None, num_steps=None, num_io_rows=3):
    """Génère la procédure ET le tableau I/O basés sur l'analyse de la note"""
    
    procedure_result = generate_procedure(llm, query, similar_notes, notes_map, procedures_map, num_steps)
    io_table = generate_io_table_with_model(llm, query, num_io_rows)
    
    return {
        'procedure': procedure_result,
        'io_table': io_table
    }

def generate_procedure(llm, query, similar_notes=None, notes_map=None, procedures_map=None, num_steps=None):
    """Génère la procédure avec focus sur l'analyse de la note circulaire"""
    
    if num_steps is not None:
        target_steps = num_steps
        print(f"🎯 Génération avec exactement {num_steps} étapes demandées")
    else:
        target_steps = MIN_PROCEDURE_ROWS
        print("🎯 Utilisation du nombre d'étapes par défaut")
    
    query_truncated = query[:1500] if len(query) > 1500 else query
    
    print(f"📝 Génération de procédure pour: {query_truncated[:100]}...")
    
    if not similar_notes or len(similar_notes) == 0:
        print("🔍 Génération basée sur l'analyse pure de la note circulaire")
        return generate_procedure_from_note_analysis(llm, query_truncated, target_steps)
    
    print(f"🔍 Génération avec contexte minimal ({len(similar_notes)} note(s) pour orientation)")
    return generate_procedure_with_minimal_context(llm, query_truncated, similar_notes, target_steps)

def generate_procedure_with_model(query, model_id="mistral-saba-24b", api_key=None, vectorstore=None, notes_map=None, procedures_map=None, num_steps=None, num_io_rows=3):
    """Génère procédure + tableau I/O basés sur l'analyse de la note circulaire"""
    
    print("🚀 Début de la génération basée sur l'analyse de la note circulaire...")
    
    if not api_key:
        api_key = get_api_key()
    
    llm = init_llm(model_id, api_key)
    
    if vectorstore is not None and notes_map is not None and procedures_map is not None:
        print("📊 Paramètres RAG fournis, recherche de contexte minimal...")
        similar_notes = find_similar_notes(vectorstore, query)
        if similar_notes:
            print(f"✅ Contexte minimal trouvé: {len(similar_notes)} note(s) pour orientation")
        else:
            print("ℹ️ Aucun contexte trouvé, génération basée uniquement sur la note")
        result = generate_procedure_with_io(llm, query, similar_notes, notes_map, procedures_map, num_steps, num_io_rows)
        return result
    
    print("📂 Chargement des données pour contexte minimal...")
    
    data = load_data()
    print(f"📊 Données chargées: {len(data['docs'])} documents disponibles")
    
    vectorstore = init_vector_store(data["docs"])
    
    if vectorstore is None:
        print("⚠️ Base vectorielle non disponible, génération basée uniquement sur la note")
        result = generate_procedure_with_io(llm, query, num_steps=num_steps, num_io_rows=num_io_rows)
        return result
    
    similar_notes = find_similar_notes(vectorstore, query)
    
    if similar_notes:
        print(f"✅ Contexte minimal identifié: {len(similar_notes)} note(s) pour orientation générale")
    else:
        print("ℹ️ Aucun contexte similaire, génération basée uniquement sur l'analyse de la note")
    
    result = generate_procedure_with_io(
        llm=llm,
        query=query,
        similar_notes=similar_notes,
        notes_map=data["notes_map"],
        procedures_map=data["procedures_map"],
        num_steps=num_steps,
        num_io_rows=num_io_rows
    )
    
    return result

def main_generate_procedure(query, model_id="mistral-saba-24b", api_key=None, num_steps=None, num_io_rows=3):
    """Point d'entrée principal pour la génération de procédures"""
    result = generate_procedure_with_model(
        query=query,
        model_id=model_id,
        api_key=api_key,
        num_steps=num_steps,
        num_io_rows=num_io_rows
    )
    
    return result

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
        
        # Détecter le début du tableau des étapes - AMÉLIORATION
        if (("| N°" in line or "| No." in line or "| Numéro" in line or "| Étape" in line) and 
            ("Description" in line or "Activités" in line)) or \
           ("| Activités |" in line and "| Description |" in line):
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "etapes"
            i += 1
            continue
            
        # Détecter le début du tableau I/O
        if "| Evènement | Processus en interface | Description du processus en interface |" in line or \
           "| Événement | Processus en interface | Description du processus en interface |" in line:
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "io"
            
            # S'assurer que nous avons la ligne de séparation
            if i + 1 < len(lines) and "| ---" in lines[i + 1]:
                current_section.append(lines[i + 1])
                i += 2
            else:
                current_section.append("| --- | --- | --- |")
                i += 1
            continue
            
        # Détecter le début des scénarios généraux
        if ("# Scénarios" in line or "## Scénarios" in line) and not "OK" in line and not "KO" in line and not "réussi" in line.lower() and not "échec" in line.lower():
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios"
            i += 1
            continue
            
        # Détecter les scénarios OK/réussis
        if ("# Scénarios OK" in line or "## Scénarios OK" in line or 
            "# Scénarios réussis" in line or "## Scénarios réussis" in line or
            "# Scénario de réussite" in line or "## Scénario de réussite" in line):
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios_ok"
            i += 1
            continue
            
        # Détecter les scénarios KO/échec
        if ("# Scénarios KO" in line or "## Scénarios KO" in line or 
            "# Scénarios d'échec" in line or "## Scénarios d'échec" in line or
            "# Scénario d'échec" in line or "## Scénario d'échec" in line):
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios_ko"
            i += 1
            continue
            
        # Si on est dans une section identifiée, ajouter la ligne
        if current_section_type:
            current_section.append(line)
            
        i += 1
    
    # Sauvegarder la dernière section
    if current_section_type and current_section:
        components[current_section_type] = "\n".join(current_section)
    
    # NOUVELLE FONCTION : Extraire le vrai début et fin des étapes
    def get_real_start_end_steps(etapes_text):
        if not etapes_text:
            return None, None
            
        lines = etapes_text.split("\n")
        steps = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("|") and line.endswith("|") and "---" not in line:
                # Extraire le contenu de la ligne du tableau
                cells = [cell.strip() for cell in line.split("|")[1:-1]]  # Enlever les | du début/fin
                if len(cells) >= 2 and cells[0] and cells[1]:  # Au moins numéro et description
                    # Ignorer les en-têtes
                    if not any(header in cells[1].lower() for header in ['description', 'activité', 'étape']):
                        steps.append(cells[1])  # Prendre la description de l'étape
        
        if steps:
            return steps[0], steps[-1]  # Premier et dernier step réels
        return None, None
    
    # Nettoyer et formater le tableau I/O
    if components["io"]:
        lines = components["io"].split("\n")
        if len(lines) >= 1:
            # En-tête standardisé
            header = "| Evènement | Processus en interface | Description du processus en interface |"
            separator = "| --- | --- | --- |"
            data_lines = []
            
            # Extraire uniquement les lignes de données
            data_started = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if "| ---" in line:
                    data_started = True
                    continue
                if data_started and line.startswith("|") and line.endswith("|"):
                    data_lines.append(line)
                elif not data_started and line.startswith("|") and line.endswith("|") and "Evènement" not in line and "Événement" not in line:
                    data_lines.append(line)
                    
            # Reconstruire le tableau avec un format propre
            if data_lines:
                components["io"] = "\n".join([header, separator] + data_lines)
            else:
                # Garder le contenu original si on n'arrive pas à extraire les données
                components["io"] = "\n".join(lines)
    
    # Nettoyer le tableau des étapes ET extraire début/fin réels
    if components["etapes"]:
        lines = components["etapes"].split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        components["etapes"] = "\n".join(cleaned_lines)
        
        # AJOUT : Extraire les vrais points de début et fin
        start_step, end_step = get_real_start_end_steps(components["etapes"])
        components["real_start"] = start_step
        components["real_end"] = end_step
    
    # Nettoyer les sections de scénarios
    for scenario_type in ["scenarios", "scenarios_ok", "scenarios_ko"]:
        if components[scenario_type]:
            lines = components[scenario_type].split("\n")
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
            components[scenario_type] = "\n".join(cleaned_lines)
    
    return components

def test_generation_function(api_key=None):
    """Fonction de test pour vérifier le bon fonctionnement"""
    if not api_key:
        api_key = get_api_key()
    
    test_query = "Note circulaire concernant les procédures de crédit aux PME"
    
    result = main_generate_procedure(
        query=test_query,
        api_key=api_key,
        num_steps=5,
        num_io_rows=3
    )
    
    print("✅ Test réussi!")
    print(f"📄 Procédure générée: {len(result['procedure'])} caractères")
    print(f"📊 Tableau I/O généré: {len(result['io_table'])} caractères")
    
    return result

# === SECTION DE TEST ===
def main():
    """Fonction principale pour tester le générateur"""
    print("🏁 === GÉNÉRATEUR DE PROCÉDURES BANCAIRES ===")
    print("🔑 Vérification de la clé API...")
    
    try:
        # Test avec la clé API depuis les variables d'environnement
        api_key = get_api_key()
        print(f"✅ Clé API trouvée: {api_key[:10]}...")
        
        # Test de génération
        print("\n🧪 Test de génération...")
        test_query = """
        Note circulaire N°2024-001 concernant les nouvelles procédures d'octroi de crédit aux PME.
        
        Cette note définit les modalités de traitement des demandes de financement pour les petites et moyennes entreprises.
        
        Les étapes à suivre sont:
        1. Réception et enregistrement de la demande
        2. Vérification des documents requis
        3. Analyse de la capacité de remboursement
        4. Évaluation des garanties
        5. Décision d'octroi
        
        Documents requis: Bilan comptable, relevés bancaires, business plan, garanties.
        """
        
        result = main_generate_procedure(
            query=test_query,
            model_id="mistral-saba-24b",
            api_key=api_key,
            num_steps=6,
            num_io_rows=3
        )
        
        print("\n" + "="*60)
        print("📋 PROCÉDURE GÉNÉRÉE:")
        print("="*60)
        print(result['procedure'])
        
        print("\n" + "="*60)
        print("📊 TABLEAU ENTRÉES/SORTIES:")
        print("="*60)
        print(result['io_table'])
        
        print("\n✅ GÉNÉRATION RÉUSSIE!")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        print("\n🔧 VÉRIFIEZ:")
        print("1. Que votre variable d'environnement GROQ_API_KEY est définie")
        print("2. Que votre clé API est valide")
        print("3. Que vous avez une connexion internet")

if __name__ == "__main__":
    main()
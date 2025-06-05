import os
import json
from pathlib import Path
import time
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# --- Configuration ---
DATA_PATH = "data/donnees.json"
VS_DIR = "data/chroma_store"

# Réduire le seuil pour augmenter les chances de trouver des notes similaires
SIMILARITY_THRESHOLD = 0.2  # Seuil plus bas pour être plus permissif
MAX_NOTE_LENGTH = 500       # Augmenter la taille des notes de référence
MAX_EXAMPLES = 2            # Limite le nombre d'exemples à utiliser
MIN_PROCEDURE_ROWS = 4      # Nombre minimum de lignes pour la procédure générée
MAX_PROCEDURE_ROWS = 65    # Nombre maximum de lignes pour la procédure générée

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

# --- Chargement des données ---
def load_data(json_path=DATA_PATH):
    """Charge les données depuis le fichier JSON avec la structure attendue"""
    try:
        path = Path(json_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Structure attendue: liste de dossiers
            dossiers = data.get('dossiers', []) if isinstance(data, dict) else data
            
            # Préparation des structures de données pour le RAG
            docs = []
            notes_map = {}
            procedures_map = {}
            
            # Parcourir tous les dossiers
            for dossier in dossiers:
                num = dossier.get('numero')
                nom = dossier.get('nom', '')
                
                # Récupérer la note circulaire
                note = dossier.get('note_circulaire', {})
                texte = note.get('texte', '') if isinstance(note, dict) else ''
                
                # Seulement traiter les dossiers avec une note circulaire
                if texte:
                    # Créer un document pour la recherche vectorielle
                    docs.append(Document(
                        page_content=texte,
                        metadata={'numero': num, 'nom': nom}
                    ))
                    
                    # Stocker la note pour référence rapide
                    notes_map[num] = texte
                    
                    # Stocker les procédures associées
                    procedures_map[num] = dossier.get('procedures', [])
            
            return {"docs": docs, "notes_map": notes_map, "procedures_map": procedures_map}
        
        # Fichier inexistant ou malformé, renvoyer structure vide
        return {"docs": [], "notes_map": {}, "procedures_map": {}}
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        return {"docs": [], "notes_map": {}, "procedures_map": {}}

# --- Sauvegarde des données ---
def save_data(data, json_path=DATA_PATH):
    """Sauvegarde les données dans le fichier JSON"""
    try:
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données: {e}")
        return False

# --- Initialisation de la base vectorielle ---
def init_vector_store(documents=None):
    """Initialise ou charge la base vectorielle"""
    try:
        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # CORRECTION: Toujours recréer la base si des documents sont fournis
        if documents and len(documents) > 0:
            # Supprimer la base existante pour éviter les problèmes d'index
            import shutil
            import os
            if os.path.exists(VS_DIR):
                shutil.rmtree(VS_DIR, ignore_errors=True)
            
            # Créer une nouvelle base
            Path(VS_DIR).mkdir(parents=True, exist_ok=True)
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(documents)
            vs = Chroma(collection_name='notes', persist_directory=VS_DIR, embedding_function=embedder)
            vs.add_documents(chunks)
            vs.persist()
            print(f"Base vectorielle créée avec {len(chunks)} chunks")
            return vs
        
        # Si pas de documents fournis et base existante, charger la base
        if Path(VS_DIR).exists() and os.listdir(VS_DIR):
            try:
                vs = Chroma(collection_name='notes', persist_directory=VS_DIR, embedding_function=embedder)
                print(f"Base vectorielle chargée depuis {VS_DIR}")
                return vs
            except Exception as e:
                print(f"Erreur lors du chargement de la base vectorielle: {e}. Création d'une nouvelle base.")
                # En cas d'erreur de chargement, supprimer et recréer
                import shutil
                shutil.rmtree(VS_DIR, ignore_errors=True)
        
        # Créer une nouvelle base vide
        Path(VS_DIR).mkdir(parents=True, exist_ok=True)
        vs = Chroma(collection_name='notes', persist_directory=VS_DIR, embedding_function=embedder)
        vs.persist()
        print("Base vectorielle vide créée")
        return vs
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base vectorielle: {e}")
        return None

# --- Recherche des notes similaires ---
def find_similar_notes(vectorstore, query, k=MAX_EXAMPLES):
    """Recherche les notes circulaires similaires à la requête"""
    if not vectorstore:
        print("Base vectorielle non initialisée.")
        return []
        
    try:
        # Augmenter k pour avoir plus de résultats potentiels
        results = vectorstore.similarity_search_with_score(
            query, 
            k=k*3  # Chercher plus de résultats pour avoir plus de chances
        )
        
        similar_notes = []
        for doc, score in results:
            note_id = doc.metadata.get('numero', '')
            note_title = doc.metadata.get('nom', 'Sans titre')
            # Amélioration du calcul de similarité
            similarity = 1.0 / (1.0 + score)  # Utiliser une fonction inverse pour la similarité
            
            # Ajuster le score en fonction de la longueur du contenu
            content_length = len(doc.page_content.strip())
            if content_length > 100:  # Bonus pour les documents plus longs
                similarity *= 1.2
            
            # N'ajouter que si au-dessus du seuil de similarité
            if similarity >= SIMILARITY_THRESHOLD:
                similar_notes.append({
                    'id': note_id,
                    'titre': note_title,
                    'score': similarity,
                    'content': doc.page_content
                })
        
        print(f"Notes similaires trouvées: {len(similar_notes)}")
        return similar_notes
    except Exception as e:
        print(f"Erreur lors de la recherche de notes similaires: {e}")
        return []

# --- NOUVELLE FONCTION: Extraction des concepts clés ---
def extract_key_concepts_from_procedures(procedures):
    """Extrait les concepts clés des procédures sans donner les détails exacts"""
    if not procedures:
        return "Aucun concept disponible"
    
    key_concepts = []
    activities_seen = set()
    
    for proc in procedures:
        if isinstance(proc, dict) and 'etapes' in proc:
            for etape in proc.get('etapes', []):
                if isinstance(etape, dict):
                    activite = etape.get('Activités', '').strip()
                    if activite and activite not in activities_seen and len(activite) > 5:
                        # Extraire seulement le concept principal, pas les détails
                        concept = activite.split(':')[0].split('-')[0].strip()
                        if len(concept) > 3:
                            key_concepts.append(concept)
                            activities_seen.add(activite)
    
    return ", ".join(key_concepts[:8])  # Limiter à 8 concepts maximum

# --- Extraction de la procédure depuis les dossiers ---
def extract_procedure_from_dossier_format(procedures):
    """Extrait les étapes de procédure au format attendu par le modèle"""
    if not procedures:
        return "Aucune procédure disponible"
    
    formatted_steps = []
    for proc in procedures:
        if isinstance(proc, dict) and 'etapes' in proc:
            # Pour chaque étape dans les procédures
            for etape in proc.get('etapes', []):
                if isinstance(etape, dict):
                    # Format attendu pour le tableau Markdown
                    row = f"| {etape.get('N°', 'N/A')} | {etape.get('Activités', 'N/A')} | {etape.get('Description', 'N/A')} | {etape.get('Acteurs', 'N/A')} | {etape.get('Documents', 'N/A')} | {etape.get('Applications', 'N/A')} |"
                    formatted_steps.append(row)
    
    if not formatted_steps:
        # Essayer un autre format possible
        for proc in procedures:
            if isinstance(proc, dict):
                num = proc.get('numero', 'N/A')
                activite = proc.get('activite', 'N/A')
                desc = proc.get('description', 'N/A')
                acteurs = proc.get('acteurs', 'N/A')
                docs = proc.get('documents', 'N/A')
                apps = proc.get('applications', 'N/A')
                row = f"| {num} | {activite} | {desc} | {acteurs} | {docs} | {apps} |"
                formatted_steps.append(row)
    
    if not formatted_steps:
        return "Format de procédure non reconnu"
    
    return "\n".join(formatted_steps)

# --- Initialisation du modèle LLM ---
def init_llm(model_id="mistral-saba-24b", api_key=None):
    """Initialise le modèle de langage"""
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Clé API Groq non trouvée. Vérifiez vos variables d'environnement.")
            return None
    
    model_config = MODELS.get(model_id, MODELS["mistral-saba-24b"])
    
    try:
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_id,
            temperature=model_config["temperature"],
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.0,
            max_tokens=model_config["max_tokens"],
            streaming=True
        )
        return llm
    except Exception as e:
        print(f"Erreur lors de l'initialisation du modèle LLM: {e}")
        return None

# --- NOUVELLE FONCTION: Génération sans RAG ---
def generate_procedure_without_rag(llm, query, min_steps, max_steps):
    """Génère une procédure sans exemples RAG"""
    print("Génération sans RAG (analyse pure de la note circulaire)")
    
    template = """# SYSTEM
Vous êtes un expert en conformité bancaire islamique spécialisé dans l'analyse de notes circulaires.

# MISSION
Analysez en profondeur la note circulaire et créez EXACTEMENT {min_rows} étapes procédurales spécifiques.

# MÉTHODE D'ANALYSE OBLIGATOIRE
1. Identifiez l'OBJECTIF principal de la note
2. Listez toutes les EXIGENCES mentionnées
3. Identifiez les CONTRÔLES nécessaires
4. Déterminez les ACTEURS impliqués
5. Listez les DOCUMENTS requis

# SORTIE FORMAT STRICT
| N° | Activités | Description | Acteurs | Documents | Applications |
[EXACTEMENT {min_rows} lignes basées sur l'analyse de la note]

# CONTRAINTES SPÉCIFIQUES
- Chaque description doit contenir 30-70 mots obligatoirement
- Remplacez "crédit" par "Mourabaha" et "leasing" par "Leasing (Ijara)"
- Chaque étape doit traiter un aspect concret de la note circulaire
- Soyez précis et spécifique, évitez les généralités

# NOTE CIRCULAIRE À ANALYSER
{query}

# INSTRUCTIONS
Créez des étapes qui reflètent fidèlement le contenu et les exigences de cette note circulaire spécifique.
Format: |N°|Activité|Description 30-70 mots|Acteurs|Documents|Applications|
"""

    prompt = PromptTemplate(
        input_variables=['query', 'min_rows'],
        template=template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        return chain.run({
            'query': query,
            'min_rows': min_steps
        })
    except Exception as e:
        print(f"Erreur lors de génération sans RAG: {e}")
        return simulate_procedure_generation(query, "mistral-saba-24b")

# --- FONCTION MODIFIÉE: Génération principale de la procédure ---
def generate_procedure(llm, query, similar_notes=None, notes_map=None, procedures_map=None, num_steps=None):
    """Génère la procédure avec le LLM en utilisant des concepts inspirants plutôt que des exemples copiables"""
    
    # Forcer exactement le nombre d'étapes spécifié ou utiliser la valeur par défaut
    if num_steps is not None:
        print(f"Nombre d'étapes demandé par l'utilisateur: {num_steps}")
        min_steps = num_steps
        max_steps = num_steps
        print(f"Génération avec exactement {num_steps} étapes")
    else:
        min_steps = MIN_PROCEDURE_ROWS
        max_steps = MAX_PROCEDURE_ROWS
        print("Utilisation du nombre d'étapes par défaut")
    
    # Tronquer la requête si elle est trop longue
    query_truncated = query[:1200] if len(query) > 1200 else query
    
    # Debug information
    print(f"Génération de procédure pour la requête: {query_truncated[:50]}...")
    print(f"Utilisation du RAG: {'Oui' if similar_notes and len(similar_notes) > 0 else 'Non'}")
    
    # Chemin RAG avec notes similaires - APPROCHE CONCEPTUELLE
    if similar_notes and len(similar_notes) > 0:
        print(f"Utilisation de {len(similar_notes)} exemples similaires pour inspiration conceptuelle")
        
        # Limiter le nombre d'exemples pour économiser des tokens
        similar_notes = similar_notes[:MAX_EXAMPLES]
        
        # NOUVELLE APPROCHE: Extraire seulement les concepts et patterns
        conceptual_context = ""
        domain_keywords = []
        activity_patterns = []
        
        for i, note in enumerate(similar_notes, 1):
            note_id = note['id']
            procs = procedures_map.get(note_id, []) if procedures_map else []
            
            if procs:
                # Extraire les mots-clés du domaine depuis la note similaire
                note_text = notes_map.get(note_id, '')[:200] if notes_map else note['content'][:200]
                
                # Identifier le domaine (secteur d'activité)
                if any(word in note_text.lower() for word in ['crédit', 'financement', 'prêt', 'mourabaha']):
                    domain_keywords.append("financement")
                if any(word in note_text.lower() for word in ['pme', 'entreprise', 'société']):
                    domain_keywords.append("entreprises")
                if any(word in note_text.lower() for word in ['conformité', 'réglementation', 'circulaire']):
                    domain_keywords.append("conformité")
                
                # Extraire les patterns d'activités (concepts généraux)
                key_concepts = extract_key_concepts_from_procedures(procs)
                if key_concepts != "Aucun concept disponible":
                    activity_patterns.append(key_concepts)
        
        # Construire un contexte conceptuel léger
        if domain_keywords or activity_patterns:
            unique_domains = list(set(domain_keywords))
            conceptual_context = f"""
CONTEXTE INSPIRANT (ne pas copier, s'en inspirer) :
- Domaines similaires identifiés : {', '.join(unique_domains)}
- Types d'activités courantes dans ce contexte : {'; '.join(activity_patterns[:2])}
- Approche recommandée : Adapter ces concepts au contenu spécifique de votre note circulaire
"""
        
        # Template avec contexte conceptuel - FOCUS SUR LA CRÉATIVITÉ
        template = """# SYSTEM
Vous êtes un expert en conformité bancaire islamique qui CRÉE des procédures originales.

# MISSION CRITIQUE
Analysez PROFONDÉMENT la note circulaire fournie et créez une procédure ORIGINALE et SPÉCIFIQUE à son contenu.
NE COPIEZ JAMAIS les exemples - INSPIREZ-VOUS uniquement des concepts généraux.

# CONTRAINTE ABSOLUE
- Lisez attentivement CHAQUE détail de la note circulaire
- Identifiez les exigences SPÉCIFIQUES mentionnées
- Créez des étapes qui correspondent EXACTEMENT aux besoins de cette note
- Chaque étape doit traiter un aspect CONCRET de la note circulaire

# CONTEXTE INSPIRANT
{conceptual_context}

# SORTIE ATTENDUE - FORMAT STRICT
| N° | Activités | Description | Acteurs | Documents | Applications |
[EXACTEMENT {min_rows} lignes originales basées sur la note circulaire]

# ANALYSE OBLIGATOIRE DE LA NOTE
Avant de générer les étapes, identifiez dans la note :
1. Quel est l'OBJET principal de cette note ?
2. Quelles sont les EXIGENCES spécifiques ?
3. Qui sont les ACTEURS concernés ?
4. Quels DOCUMENTS sont mentionnés ?
5. Quelles VÉRIFICATIONS sont requises ?

# NOTE CIRCULAIRE À ANALYSER EN DÉTAIL
{query}

# INSTRUCTIONS DE GÉNÉRATION
- Chaque étape DOIT correspondre à un élément de la note circulaire
- Descriptions de 30-70 mots expliquant le POURQUOI et le COMMENT
- Remplacez "crédit" par "Mourabaha" et "leasing" par "Leasing (Ijara)"
- Soyez SPÉCIFIQUE aux exigences de cette note, pas générique
- Format: |N°|Activité spécifique|Description détaillée 30-70 mots|Acteurs concernés|Documents requis|Applications utilisées|

CRÉEZ une procédure UNIQUE pour cette note circulaire spécifique !
"""

        # Création du prompt et exécution
        prompt = PromptTemplate(
            input_variables=['query', 'conceptual_context', 'min_rows'],
            template=template
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        
        try:
            return chain.run({
                'query': query_truncated,
                'conceptual_context': conceptual_context,
                'min_rows': min_steps
            })
        except Exception as e:
            print(f"Erreur lors de l'exécution avec contexte conceptuel: {e}")
            # Repli sur génération sans RAG
            return generate_procedure_without_rag(llm, query_truncated, min_steps, max_steps)
    
    else:
        # Génération sans RAG
        return generate_procedure_without_rag(llm, query_truncated, min_steps, max_steps)

# --- Génération de la procédure avec exemples ---
def generate_procedure_with_model(query, model_id="mistral-saba-24b", api_key=None, vectorstore=None, notes_map=None, procedures_map=None, num_steps=None):
    """Génère une procédure à partir d'une note circulaire et d'un modèle spécifique
    
    Args:
        query: Le texte de la note circulaire
        model_id: L'identifiant du modèle à utiliser
        api_key: La clé API pour le modèle
        vectorstore: Un vectorstore déjà initialisé (optionnel)
        notes_map: Une map des notes déjà chargées (optionnel)
        procedures_map: Une map des procédures déjà chargées (optionnel)
        num_steps: Le nombre d'étapes souhaité par l'utilisateur 
    """
    
    print("Début de la génération de procédure...")
    
    # Initialisation du LLM
    llm = init_llm(model_id, api_key)
    if not llm:
        print("LLM non initialisé, mode simulation activé")
        # Simulation en mode démo si pas de LLM
        return simulate_procedure_generation(query, model_id)
    
    # Vérification si des paramètres RAG sont déjà fournis
    if vectorstore is not None and notes_map is not None and procedures_map is not None:
        print("Paramètres RAG déjà fournis, utilisation directe")
        # On utilise directement les paramètres fournis pour chercher les notes similaires
        similar_notes = find_similar_notes(vectorstore, query)
        return generate_procedure(llm, query, similar_notes, notes_map, procedures_map, num_steps)
    
    print("Paramètres RAG non fournis, chargement des données...")
    
    # Chargement des données
    data = load_data()
    
    print(f"Données chargées: {len(data['docs'])} documents, {len(data['notes_map'])} notes, {len(data['procedures_map'])} procédures")
    
    # Initialisation de la base vectorielle pour le RAG
    vectorstore = init_vector_store(data["docs"])
    
    if vectorstore is None:
        print("Base vectorielle non initialisée, passage en mode sans RAG")
        return generate_procedure(llm, query, num_steps=num_steps)
    
    print("Base vectorielle initialisée. Recherche de notes similaires...")
    print(f"Recherche de notes similaires pour la requête: {query[:100]}...")
    similar_notes = find_similar_notes(vectorstore, query)

    if similar_notes and len(similar_notes) > 0:
        print("Notes similaires trouvées:")
        for i, note in enumerate(similar_notes, 1):
            print(f"  {i}. ID={note['id']}, Score={note['score']:.4f}, Titre={note['titre']}")
    else:
        print("PROBLÈME: Aucune note similaire trouvée! Vérifiez le seuil de similarité et l'indexation.")
        # Diagnostique supplémentaire
        try:
            # Recherche sans seuil pour voir ce qu'on obtient
            raw_results = vectorstore.similarity_search_with_score(query, k=3)
            print("Résultats bruts (sans seuil):")
            for i, (doc, score) in enumerate(raw_results, 1):
                note_id = doc.metadata.get('numero', 'INCONNU')
                print(f"  {i}. ID={note_id}, Distance={score:.4f}")
        except Exception as e:
            print(f"Erreur lors du diagnostic: {e}")
    
    print(f"Nombre de notes similaires trouvées: {len(similar_notes)}")
    # Génération de la procédure avec ou sans notes similaires
    return generate_procedure(
        llm=llm,
        query=query,
        similar_notes=similar_notes,
        notes_map=data["notes_map"],
        procedures_map=data["procedures_map"],
        num_steps=num_steps
    )

# --- Ajout: simulation pour démo ---
def simulate_procedure_generation(note_circulaire, model_name):
    """Simule la génération d'une procédure pour la démonstration"""
    time.sleep(2)  # Simuler un délai de traitement
    
    banking_keywords = ["crédit", "banque", "PME", "financement", "secteur", "euro", "million"]
    contains_keywords = any(keyword in note_circulaire.lower() for keyword in banking_keywords)

    if not contains_keywords:
        return """
| N° | Activités | Description | Acteurs | Documents | Applications |
| 1 | Réceptionner la demande | Recevoir la demande et vérifier la complétude du dossier initial selon les exigences réglementaires | Agent d'accueil | Formulaire de demande, Pièce d'identité | Système GED |
| 2 | Vérifier l'éligibilité | Analyser la conformité de la demande par rapport aux critères définis dans la note circulaire | Chargé de clientèle | Dossier client, Justificatifs | CRM |
| 3 | Transmettre au service concerné | Envoyer le dossier validé au département responsable du traitement pour analyse approfondie | Agent d'accueil | Fiche de transmission, Dossier complet | Système de workflow |
| 4 | Analyser la demande | Étudier en détail les éléments fournis et évaluer la pertinence selon la réglementation en vigueur | Analyste | Dossier client, Référentiels réglementaires | Logiciel d'analyse |
| 5 | Valider ou rejeter | Prendre la décision finale sur la base de l'analyse effectuée et des critères établis | Responsable de service | Rapport d'analyse, Grille d'évaluation | Système de validation |
| 6 | Notifier le demandeur | Informer le demandeur de la décision prise et des éventuelles étapes suivantes | Chargé de communication | Lettre de notification, Dossier client | Système de messagerie |
| 7 | Archiver le dossier | Conserver l'ensemble des documents traités selon la politique d'archivage en vigueur | Archiviste | Dossier complet, Bordereau d'archivage | Système d'archivage |
"""
    
    # Procédure spécifique crédit bancaire
    return """
| N° | Activités | Description | Acteurs | Documents | Applications |
| 1 | Réceptionner la demande de crédit | Recevoir et enregistrer la demande de financement de la PME en vérifiant la présence de tous les documents requis | Chargé de clientèle | Formulaire de demande, Extrait RNE | Système GED, Core Banking |
| 2 | Vérifier l'éligibilité de la PME | Contrôler que l'entreprise correspond à la définition d'une PME selon le décret n°2017-389 et qu'elle n'opère pas dans un secteur exclu | Analyste conformité | Statuts, États financiers, Attestation fiscale | Système de vérification, CRM |
| 3 | Contrôler le secteur d'activité | S'assurer que le secteur d'activité fait partie des secteurs éligibles mentionnés dans la note circulaire | Responsable conformité | Documentation projet, Code NACE | Système de classification |
| 4 | Vérifier le montant demandé | Confirmer que le montant sollicité respecte le plafond d'un million d'euros par PME défini dans la note | Analyste crédit | Demande de financement, Plan de financement | Logiciel de crédit |
| 5 | Valider l'objet du financement | Contrôler que le financement est destiné à l'acquisition de biens d'équipements ou à une restructuration financière | Service technique | Factures pro forma, Documentation technique | Outil d'évaluation |
| 6 | Examiner l'origine des équipements | Vérifier que les biens à acquérir sont d'origine italienne ou tunisienne conformément aux exigences | Expert technique | Certificats d'origine, Spécifications techniques | Base documentaire |
| 7 | Analyser la capacité financière | Évaluer la capacité de remboursement de la PME et la viabilité du projet d'investissement | Analyste financier | États financiers, Prévisions, Business plan | Outil d'analyse financière |
| 8 | Préparer le dossier de crédit | Constituer le dossier complet avec tous les justificatifs et analyses pour présentation au comité | Chargé de clientèle | Rapport d'analyse, Synthèse du projet | Logiciel de crédit |
| 9 | Soumettre au comité de crédit | Présenter le dossier au comité pour décision finale selon les critères de la ligne de crédit | Directeur d'agence | Dossier de crédit complet, Fiche synthétique | Système de workflow |
| 10 | Notifier la décision au client | Informer la PME de la décision et des conditions de financement accordées | Chargé de clientèle | Lettre de notification, Offre de crédit | CRM, Système de messagerie |
| 11 | Préparer les contrats | Élaborer les contrats et documents juridiques nécessaires à la mise en place du financement | Service juridique | Contrat de prêt, Plan d'amortissement | Logiciel juridique |
| 12 | Débloquer les fonds | Procéder à la mise à disposition des fonds selon le calendrier établi et les conditions | Service opérations | Ordre de virement, Contrat signé | Core Banking |
| 13 | Suivre l'utilisation des fonds | Contrôler que les fonds sont utilisés conformément à l'objet du financement approuvé | Chargé de suivi | Justificatifs d'achat, Rapports de visite | Système de monitoring |
| 14 | Archiver le dossier | Conserver l'ensemble des documents selon la politique d'archivage et les exigences réglementaires | Service archives | Dossier complet, Bordereau d'archivage | Système d'archivage GED |
"""

# Ajoutez cette nouvelle fonction dans votre fichier procedure_gen.py

def generate_io_table_with_model(llm, query, num_io_rows=3):
    """Génère un tableau entrées/sorties dynamique avec le LLM"""
    
    template = """# SYSTEM
Vous êtes un expert en conformité bancaire spécialisé dans l'analyse des processus.

# MISSION
Générez EXACTEMENT {num_rows} événements dans un tableau entrées/sorties au format Markdown.

# SORTIE ATTENDUE - FORMAT STRICT
Le tableau doit commencer obligatoirement par ces 3 lignes exactement :

| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
[Insérez ici EXACTEMENT {num_rows} lignes d'événements]

# CONTRAINTES DE FORMAT
- Le tableau DOIT commencer immédiatement par l'en-tête ci-dessus
- La deuxième ligne DOIT être la ligne de séparation avec des tirets
- Chaque ligne de données DOIT commencer par | et finir par |
- EXACTEMENT {num_rows} lignes de données sont requises après la ligne de séparation
- Types d'événements possibles : Entrée, Traitement, Contrôle, Validation, Sortie, Exception

# NOTE CIRCULAIRE À ANALYSER
{query}

# INSTRUCTIONS DÉTAILLÉES
- Analysez la note pour identifier les points d'entrée et de sortie du processus
- Identifiez les interfaces système et humaines impliquées
- Chaque ligne doit être au format : |Type d'événement|Interface concernée|Description détaillée|
- Remplissez toutes les colonnes, ne laissez aucune cellule vide
- Utilisez "N/A" si une information n'est pas applicable
- Commencez toujours par un événement "Entrée" et finissez par un événement "Sortie"
"""

    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    
    prompt = PromptTemplate(
        input_variables=['query', 'num_rows'],
        template=template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        result = chain.run({
            'query': query[:1000],  # Limiter la taille pour éviter les erreurs
            'num_rows': num_io_rows
        })
        # Si le résultat ne contient pas l'en-tête complet, l'ajouter
        if "| Evènement | Processus en interface | Description du processus en interface |" not in result:
            result = """| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
""" + result.strip()
        # Si le résultat n'a pas la ligne de séparation, l'ajouter
        elif "| --- | --- | --- |" not in result:
            lines = result.split("\n")
            header = lines[0]
            data = lines[1:]
            result = header + "\n| --- | --- | --- |\n" + "\n".join(data)
        return result.strip()
    except Exception as e:
        print(f"Erreur lors de la génération du tableau I/O: {e}")
        # Fallback statique en cas d'erreur
        return """| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | Réception note circulaire | Déclenchement du processus suite à réception de la note |
| Traitement | Analyse et validation | Traitement des exigences de la note circulaire |
| Sortie | Application effective | Mise en place des directives de la note circulaire |"""

# Modifiez également la fonction generate_procedure pour inclure la génération du tableau I/O
def generate_procedure_with_io(llm, query, similar_notes=None, notes_map=None, procedures_map=None, num_steps=None, num_io_rows=3):
    """Génère la procédure ET le tableau I/O avec le LLM"""
    
    # Génération de la procédure principale (votre code existant)
    procedure_result = generate_procedure(llm, query, similar_notes, notes_map, procedures_map, num_steps)
    
    # Génération du tableau I/O séparément
    io_table = generate_io_table_with_model(llm, query, num_io_rows)
    
    # Retourner les deux éléments séparément
    return {
        'procedure': procedure_result,
        'io_table': io_table
    }

# Modifiez la fonction principale generate_procedure_with_model
def generate_procedure_with_model(query, model_id="mistral-saba-24b", api_key=None, vectorstore=None, notes_map=None, procedures_map=None, num_steps=None, num_io_rows=3):
    """Version modifiée qui génère procédure + tableau I/O séparément"""
    
    print("Début de la génération de procédure avec tableau I/O...")
    
    # Initialisation du LLM
    llm = init_llm(model_id, api_key)
    if not llm:
        print("LLM non initialisé, mode simulation activé")
        return {
            'procedure': simulate_procedure_generation(query, model_id),
            'io_table': """| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | Système bancaire | Réception de la demande initiale |
| Traitement | Application métier | Traitement selon les règles de la note |
| Sortie | Base de données | Enregistrement de la décision finale |"""
        }
    
    # Vérification si des paramètres RAG sont déjà fournis
    if vectorstore is not None and notes_map is not None and procedures_map is not None:
        print("Paramètres RAG déjà fournis, utilisation directe")
        similar_notes = find_similar_notes(vectorstore, query)
        result = generate_procedure_with_io(llm, query, similar_notes, notes_map, procedures_map, num_steps, num_io_rows)
        return result
    
    print("Paramètres RAG non fournis, chargement des données...")
    
    # Chargement des données
    data = load_data()
    
    print(f"Données chargées: {len(data['docs'])} documents, {len(data['notes_map'])} notes, {len(data['procedures_map'])} procédures")
    
    # Initialisation de la base vectorielle pour le RAG
    vectorstore = init_vector_store(data["docs"])
    
    if vectorstore is None:
        print("Base vectorielle non initialisée, passage en mode sans RAG")
        result = generate_procedure_with_io(llm, query, num_steps=num_steps, num_io_rows=num_io_rows)
        return result
    
    print("Base vectorielle initialisée. Recherche de notes similaires...")
    similar_notes = find_similar_notes(vectorstore, query)
    
    print(f"Nombre de notes similaires trouvées: {len(similar_notes)}")
    
    # Génération de la procédure avec tableau I/O
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

# --- Extraction des composants de la procédure ---
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
        if "| Evènement | Processus en interface | Description du processus en interface |" in line:
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
            
        # Détecter le début des scénarios
        if ("# Scénarios" in line or "## Scénarios" in line) and not "OK" in line and not "KO" in line:
            if current_section_type and current_section:
                components[current_section_type] = "\n".join(current_section)
            
            current_section = [line]
            current_section_type = "scenarios"
            i += 1
            continue
            
        # Si on est dans une section identifiée, ajouter la ligne
        if current_section_type:
            current_section.append(line)
            
        i += 1
    
    # Sauvegarder la dernière section
    if current_section_type and current_section:
        components[current_section_type] = "\n".join(current_section)
    
    # S'assurer que le tableau I/O est bien formaté
    if components["io"]:
        lines = components["io"].split("\n")
        if len(lines) >= 1:
            header = "| Evènement | Processus en interface | Description du processus en interface |"
            separator = "| --- | --- | --- |"
            data_lines = []
            
            # Ne garder que les lignes de données après l'en-tête et le séparateur
            data_started = False
            for line in lines:
                if "| ---" in line:
                    data_started = True
                    continue
                if data_started and line.strip():
                    data_lines.append(line)
                    
            # Reconstruire le tableau avec un seul en-tête
            components["io"] = "\n".join([header, separator] + data_lines)
    
    return components
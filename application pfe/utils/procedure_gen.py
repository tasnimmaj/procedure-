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
SIMILARITY_THRESHOLD = 0.4  
MAX_NOTE_LENGTH = 300       # Limite la taille des notes de référence
MAX_EXAMPLES = 2            # Limite le nombre d'exemples à utiliser
MIN_PROCEDURE_ROWS = 4      # Nombre minimum de lignes pour la procédure générée
MAX_PROCEDURE_ROWS = 100    # Nombre maximum de lignes pour la procédure générée
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
        # CORRECTION: Utiliser search_documents directement avec un seuil plus bas
        results = vectorstore.similarity_search_with_score(
            query, 
            k=k
        )
        
        similar_notes = []
        for doc, score in results:
            note_id = doc.metadata.get('numero', '')
            note_title = doc.metadata.get('nom', 'Sans titre')
            
            # Convertir le score en similarité (car souvent c'est une distance)
            similarity = 1.0 - min(score, 1.0)  # Convertir distance en similarité
            
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

# --- Génération de la procédure avec exemples ---
def generate_procedure_with_model(query, model_id="mistral-saba-24b", api_key=None, vectorstore=None, notes_map=None, procedures_map=None):
    """Génère une procédure à partir d'une note circulaire et d'un modèle spécifique"""
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
        return generate_procedure(llm, query, similar_notes, notes_map, procedures_map)
    
    print("Paramètres RAG non fournis, chargement des données...")
    
    # Chargement des données
    data = load_data()
    
    print(f"Données chargées: {len(data['docs'])} documents, {len(data['notes_map'])} notes, {len(data['procedures_map'])} procédures")
    
    # Initialisation de la base vectorielle pour le RAG
    vectorstore = init_vector_store(data["docs"])
    
    if vectorstore is None:
        print("Base vectorielle non initialisée, passage en mode sans RAG")
        return generate_procedure(llm, query)
    
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
        # Recherche de notes similaires
        similar_notes = find_similar_notes(vectorstore, query)

    print(f"Nombre de notes similaires trouvées: {len(similar_notes)}")

    # Génération de la procédure avec ou sans notes similaires
    return generate_procedure(llm, query, similar_notes, data["notes_map"], data["procedures_map"])

# --- Génération principale de la procédure ---
def generate_procedure(llm, query, similar_notes=None, notes_map=None, procedures_map=None):
    """Génère la procédure avec le LLM en utilisant des exemples si disponibles"""
    # Tronquer la requête si elle est trop longue
    query_truncated = query[:1200] if len(query) > 1200 else query
    
    # Debug information
    print(f"Génération de procédure pour la requête: {query_truncated[:50]}...")
    print(f"Utilisation du RAG: {'Oui' if similar_notes and len(similar_notes) > 0 else 'Non'}")
    
    # Chemin RAG avec notes similaires
    if similar_notes and len(similar_notes) > 0:
        print(f"Utilisation de {len(similar_notes)} exemples similaires pour la génération RAG")
        
        # Limiter le nombre d'exemples pour économiser des tokens
        similar_notes = similar_notes[:MAX_EXAMPLES]
        
        examples_context = ""
        for i, note in enumerate(similar_notes, 1):
            note_id = note['id']
            procs = procedures_map.get(note_id, []) if procedures_map else []
            
            if procs:
                examples_context += f"\n### EXEMPLE {i} (ID={note_id}) ###\n"
                examples_context += f"TITRE: {note['titre']}\n"
                
                # Tronquer la note circulaire pour économiser des tokens
                note_text = notes_map.get(note_id, '')[:MAX_NOTE_LENGTH] if notes_map else note['content'][:MAX_NOTE_LENGTH]
                if len(notes_map.get(note_id, '') if notes_map else note['content']) > MAX_NOTE_LENGTH:
                    note_text += "... [texte tronqué]"
                examples_context += f"NOTE CIRCULAIRE (extrait):\n{note_text}\n\n"
                
                # Formatage des procédures pour exemples
                proc_table = extract_procedure_from_dossier_format(procs)
                examples_context += f"PROCÉDURES DE RÉFÉRENCE:\n{proc_table}\n"
        
        # Vérifier si on a réellement des exemples formatés
        if examples_context.strip():
            # Template avec exemples
            template = """# SYSTEM
Vous êtes un expert en conformité bancaire, familier avec les bonnes pratiques de procédures internes.

# MISSION
À partir d'une note circulaire fournie, générez :
1. Un **tableau des étapes** détaillé.
2. Un **tableau I/O** synthétique.

# CONTEXTE D'EXEMPLES
Vous disposez de notes circulaires similaires et de leurs procédures associées :
{examples_context}

# NOUVELLE NOTE À TRAITER
{query}

# CONTRAINTES ET INSTRUCTIONS
- **Étapes** : entre {min_rows} et {max_rows}.
- **Entrée** (10–20 mots) : événement déclencheur.
- **Activités** (10–15 mots) : verbe d'action.
- **Description** (30–70 mots) : détails, contrôles, vérifications.
- **Acteurs** : intervenants.
- **Documents** : requis ou générés.
- **Applications** : logiciels/systèmes.
- **Sortie** (10–20 mots) : résultat immédiat.

# SCÉNARIOS DE VALIDATION
Pour chaque scénario, proposez 2 cas :
- **OK** : plan validé – conditions de succès.
- **KO** : plan non validé – points d'échec.

# SORTIE ATTENDUE
1. **Tableau des étapes** au format Markdown :
   | N° | Activités | Description | Acteurs | Documents | Applications |
   | --- | --- | --- | --- | --- | --- |
   | … | … | … | … | … | … |
2. **Tableau I/O** au format Markdown :
| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | … | … |
| Sortie | … | … |


"""
            # Création du prompt et exécution avec la chaîne LangChain
            prompt = PromptTemplate(
                input_variables=['query', 'examples_context', 'min_rows', 'max_rows'],
                template=template
            )
            
            chain = LLMChain(llm=llm, prompt=prompt)
            
            # Exécution avec les paramètres
            try:
                # Vérifier si examples_context n'est pas vide avant de l'utiliser
                if examples_context.strip():
                    return chain.run({
                        'query': query_truncated,
                        'examples_context': examples_context,
                        'min_rows': MIN_PROCEDURE_ROWS,
                        'max_rows': MAX_PROCEDURE_ROWS
                    })
                else:
                    print("Contexte d'exemples vide, basculement vers génération sans RAG")
                    return generate_procedure(llm, query_truncated)
            except Exception as e:
                print(f"Erreur lors de l'exécution de la chaîne LangChain avec RAG: {e}")
                # Repli sur la génération sans RAG
                return generate_procedure(llm, query_truncated)
        else:
            print("Contexte d'exemples vide après traitement, basculement vers génération sans RAG")
            return generate_procedure(llm, query_truncated, None, None, None)
    else:
        # Chemin sans RAG
        print("Génération sans RAG (pas d'exemples similaires trouvés)")
        template = """# SYSTEM
Vous êtes un expert en conformité bancaire.

# MISSION
Générez :
1. Un **tableau des étapes** détaillé à partir de la note :
   {query}
2. Un **tableau I/O** synthétique.

# CONTRAINTES
- **Étapes** : entre {min_rows} et {max_rows}.
- **Entrée** (10–20 mots), **Activités** (10–15 mots), **Description** (30–100 mots), **Acteurs**, **Documents**, **Applications**, **Sortie** (10–20 mots).
- **Scénarios** : 2 cas (OK/KO).

# SORTIE ATTENDUE
1. **Tableau des étapes** :
   | N° | Activités | Description | Acteurs | Documents | Applications | 
   | --- | --- | --- | --- | --- | --- |
   | ... | ... | ... | ... | ... | ... |

2. **Tableau des Entrées/Sorties** :
| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | … | … |
| Sortie | … | … |


## EXEMPLE DE NOTE CIRCULAIRE
Article 1 : Une ligne de crédit de 50 millions d'euros est mise à disposition des PME tunisiennes.
Article 2 : Peuvent bénéficier les PME privées définies par le décret n°2017-389.
Article 3 : Les ressources sont destinées à l'acquisition de biens d'équipements productifs.
Article 4 : Les secteurs éligibles sont l'industrie, l'agriculture, et les services.

## EXEMPLE DE PROCÉDURE RÉSULTANTE
| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |
| 1 | Réceptionner de la demande | Vérifier la complétude du dossier et l'éligibilité du client selon les critères de la ligne de crédit | Chargé de clientèle | Formulaire de demande, Extrait RNE | Système GED, Core Banking |
| 2 | Analyser le dossier | Évaluer la capacité de remboursement et la viabilité du projet selon les ratios bancaires | Analyste crédit | États financiers, Business plan | Outil d'analyse financière |
| 3 | Vérifier l'éligibilité sectorielle | Contrôler que l'activité du demandeur appartient aux secteurs éligibles mentionnés dans la note circulaire | Responsable conformité | Documentation projet, Code NACE | Système de classification |
| 4 | Valider l'origine des équipements | S'assurer que les équipements à financer respectent les critères d'origine définis dans la note | Service technique | Factures pro forma, Certificats d'origine | N/A |
| 5 | Préparer du dossier de financement | Constituer le dossier complet avec tous les justificatifs nécessaires pour la demande de financement | Chargé de clientèle | Contrats, Plan d'amortissement | Logiciel de crédit |

# FORMAT DE SORTIE ATTENDU
Le tableau de procédure au format Markdown avec exactement entre {min_rows} et {max_rows} lignes (étapes), avec toutes les colonnes remplies de manière détaillée:

| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |

Le tableau d'entrées/sorties format Markdown avec exactement 2 lignes , avec toutes les colonnes remplies de manière détaillée:
| Evènement | Processus en interface | Description du processus en interface |
| --- | --- | --- |
| Entrée | … | … |
| Sortie | … | … |

"""

        # Création du prompt et exécution avec la chaîne LangChain
        prompt = PromptTemplate(
            input_variables=['query', 'min_rows', 'max_rows'],
            template=template
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Exécution avec les paramètres
        try:
            return chain.run({
                'query': query_truncated,
                'min_rows': MIN_PROCEDURE_ROWS,
                'max_rows': MAX_PROCEDURE_ROWS
            })
        except Exception as e:
            print(f"Erreur lors de l'exécution de la chaîne LangChain sans RAG: {e}")
            # Fallback en mode démo
            return simulate_procedure_generation(query_truncated, "mistral-saba-24b")

# --- Ajout: simulation pour démo ---
def simulate_procedure_generation(note_circulaire, model_name):
    """Simule la génération d'une procédure pour la démonstration"""
    time.sleep(2)  # Simuler un délai de traitement
    
    banking_keywords = ["crédit", "banque", "PME", "financement", "secteur", "euro", "million"]
    contains_keywords = any(keyword in note_circulaire.lower() for keyword in banking_keywords)

    if not contains_keywords:
        return """
| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |
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
| --- | --- | --- | --- | --- | --- |
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
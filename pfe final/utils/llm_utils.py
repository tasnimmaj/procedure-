import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Constantes
MIN_PROCEDURE_ROWS = 12  # Nombre minimum de lignes pour la procédure générée
MAX_PROCEDURE_ROWS = 30  # Nombre maximum de lignes pour la procédure générée
MAX_NOTE_LENGTH = 300  # Limite la taille des notes de référence
MAX_EXAMPLES = 2  # Limite le nombre d'exemples à utiliser

@st.cache_resource
def get_llm(api_key, model_name="mistral-saba-24b"):
    """
    Initialise et retourne un modèle LLM de Groq.
    Utilise le cache Streamlit pour réutiliser l'instance.
    """
    try:
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=0.7,
            max_tokens=4096,
            top_p=1,
            streaming=True,
        )
        return llm
    except Exception as e:
        st.error(f"Erreur d'initialisation du LLM: {e}")
        return None

def extract_procedure_summary(procedures, max_items=5):
    """
    Extrait un résumé des procédures pour réduire la taille du contexte.
    """
    if not procedures:
        return "Aucune procédure disponible"
    
    summary = []
    for i, proc in enumerate(procedures[:max_items]):
        if isinstance(proc, dict):
            num = proc.get('numero', i+1)
            activity = proc.get('activite', 'N/A')
            desc = proc.get('description', 'N/A')
            actors = proc.get('acteurs', 'N/A')
            docs = proc.get('documents', 'N/A')
            apps = proc.get('applications', 'N/A')
            summary.append(f"| {num} | {activity} | {desc[:50]}... | {actors} | {docs} | {apps} |")
    
    return "\n".join(summary)

def generate_procedure(llm, query, similar_notes=None, notes_map=None, procedures_map=None):
    """
    Génère une procédure à partir d'une note circulaire et d'exemples similaires.
    """
    if not llm:
        return "Erreur: Modèle LLM non initialisé. Vérifiez votre clé API."
        
    # Tronquer la requête si elle est trop longue
    query_truncated = query[:1200] if len(query) > 1200 else query
    
    if similar_notes and len(similar_notes) > 0:
        # Limiter le nombre d'exemples pour économiser des tokens
        similar_notes = similar_notes[:MAX_EXAMPLES]
        
        examples_context = ""
        for i, note in enumerate(similar_notes, 1):
            note_id = note['id']
            procs = procedures_map.get(note_id, [])
            if procs:
                examples_context += f"\n### EXEMPLE {i} (ID={note_id}) ###\n"
                examples_context += f"TITRE: {note['titre']}\n"
                
                # Tronquer la note circulaire pour économiser des tokens
                note_text = notes_map.get(note_id, '')[:MAX_NOTE_LENGTH]
                if len(notes_map.get(note_id, '')) > MAX_NOTE_LENGTH:
                    note_text += "... [texte tronqué]"
                examples_context += f"NOTE CIRCULAIRE (extrait):\n{note_text}\n\n"
                
                # Résumer les procédures au lieu de les inclure en entier
                proc_summary = extract_procedure_summary(procs)
                examples_context += f"PROCÉDURES DE RÉFÉRENCE:\n{proc_summary}\n"
        
        # Template avec instruction explicite pour générer un nombre minimum de lignes
        template = """# MISSION
Expert en conformité bancaire, créer une procédure détaillée et complète à partir d'une note circulaire.

# CONTEXTE
Voici des exemples similaires identifiés dans notre base de données que vous pouvez utiliser comme inspiration:
{examples_context}

# NOUVELLE NOTE CIRCULAIRE À TRAITER
{query}

# INSTRUCTIONS PRÉCISES
1. Analysez en profondeur la note circulaire fournie
2. Générez une procédure bancaire complète avec entre {min_rows} et {max_rows} étapes (lignes du tableau)
3. Chaque étape doit être numérotée séquentiellement
4. Créez un tableau Markdown avec les colonnes: N°, Activités, Description, Acteurs, Documents, Applications
5. Pour chaque étape:
   - Activités: décrivez précisément l'action à réaliser (10-15 mots)
   - Description: détaillez le processus, les contrôles et les vérifications (30-50 mots)
   - Acteurs: identifiez tous les intervenants concernés par l'activité
   - Documents: listez tous les documents nécessaires ou générés
   - Applications: mentionnez les logiciels ou systèmes impliqués

# EXEMPLES D'ÉTAPES (pour vous guider)
| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |
| 1 | Réception et vérification de la demande | Vérifier la complétude du dossier et l'éligibilité du client selon les critères de la ligne de crédit | Chargé de clientèle | Formulaire de demande, Extrait RNE | Système GED, Core Banking |
| 2 | Analyse financière du dossier | Évaluer la capacité de remboursement et la viabilité du projet selon les ratios bancaires | Analyste crédit | États financiers, Business plan | Outil d'analyse financière |

# FORMAT DE SORTIE ATTENDU
Le tableau de procédure au format Markdown avec exactement entre {min_rows} et {max_rows} lignes (étapes), avec toutes les colonnes remplies de manière détaillée:

| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |

"""

        prompt = PromptTemplate(
            input_variables=['query', 'examples_context', 'min_rows', 'max_rows'],
            template=template
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run({
            'query': query_truncated,
            'examples_context': examples_context,
            'min_rows': MIN_PROCEDURE_ROWS,
            'max_rows': MAX_PROCEDURE_ROWS
        })
    else:
        # Template sans exemples, mais avec instruction claire sur le nombre de lignes
        template = """# MISSION
Expert en conformité bancaire, créer une procédure détaillée et complète à partir d'une note circulaire.

# NOUVELLE NOTE CIRCULAIRE À TRAITER
{query}

# INSTRUCTIONS PRÉCISES
1. Analysez en profondeur la note circulaire fournie
2. Générez une procédure bancaire complète avec entre {min_rows} et {max_rows} étapes (lignes du tableau)
3. Chaque étape doit être numérotée séquentiellement
4. Créez un tableau Markdown avec les colonnes: N°, Activités, Description, Acteurs, Documents et Applications
5. Pour chaque étape:
   - Activités: décrivez précisément l'action à réaliser (10-15 mots)
   - Description: détaillez le processus, les contrôles et les vérifications (30-50 mots)
   - Acteurs: identifiez tous les intervenants concernés par l'activité
   - Documents: listez tous les documents nécessaires ou générés
   - Applications: mentionnez les logiciels ou systèmes impliqués

# EXEMPLE DE STRUCTURE DÉTAILLÉE POUR LA LIGNE DE CRÉDIT
Voici un exemple de note circulaire et sa procédure associée:

## EXEMPLE DE NOTE CIRCULAIRE
Article 1 : Une ligne de crédit de 50 millions d'euros est mise à disposition des PME tunisiennes.
Article 2 : Peuvent bénéficier les PME privées définies par le décret n°2017-389.
Article 3 : Les ressources sont destinées à l'acquisition de biens d'équipements productifs.
Article 4 : Les secteurs éligibles sont l'industrie, l'agriculture, et les services.

## EXEMPLE DE PROCÉDURE RÉSULTANTE
| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |
| 1 | Réception et vérification de la demande | Vérifier la complétude du dossier et l'éligibilité du client selon les critères de la ligne de crédit | Chargé de clientèle | Formulaire de demande, Extrait RNE | Système GED, Core Banking |
| 2 | Analyse financière du dossier | Évaluer la capacité de remboursement et la viabilité du projet selon les ratios bancaires | Analyste crédit | États financiers, Business plan | Outil d'analyse financière |
| 3 | Vérification de l'éligibilité sectorielle | Contrôler que l'activité du demandeur appartient aux secteurs éligibles mentionnés dans la note circulaire | Responsable conformité | Documentation projet, Code NACE | Système de classification |
| 4 | Validation de l'origine des équipements | S'assurer que les équipements à financer respectent les critères d'origine définis dans la note | Service technique | Factures pro forma, Certificats d'origine | N/A |
| 5 | Préparation du dossier de financement | Constituer le dossier complet avec tous les justificatifs nécessaires pour la demande de financement | Chargé de clientèle | Contrats, Plan d'amortissement | Logiciel de crédit |

# FORMAT DE SORTIE ATTENDU
Le tableau de procédure au format Markdown avec exactement entre {min_rows} et {max_rows} lignes (étapes), avec toutes les colonnes remplies de manière détaillée:

| N° | Activités | Description | Acteurs | Documents | Applications |
| --- | --- | --- | --- | --- | --- |
"""

        prompt = PromptTemplate(
            input_variables=['query', 'min_rows', 'max_rows'],
            template=template
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run({
            'query': query_truncated,
            'min_rows': MIN_PROCEDURE_ROWS,
            'max_rows': MAX_PROCEDURE_ROWS
        })

def generate_workflow_diagram(llm, procedure_text):
    """
    Génère un logigramme à partir d'une procédure.
    Retourne du code Mermaid pour représenter le workflow.
    """
    if not llm:
        return "graph TD\n    A[Erreur: LLM non initialisé] --> B[Vérifiez votre clé API]"
        
    template = """# MISSION
Convertir une procédure bancaire en logigramme (flowchart) utilisant la syntaxe Mermaid.

# PROCÉDURE
{procedure}

# INSTRUCTIONS
1. Analysez la procédure fournie et identifiez les étapes clés, les décisions et les flux
2. Créez un logigramme clair en utilisant la syntaxe Mermaid (graph TD ou graph LR)
3. Utilisez les formes appropriées:
   - Rectangles pour les actions/étapes: [texte]
   - Losanges pour les décisions: {texte}
   - Flèches pour montrer les flux: -->
4. Limitez-vous aux étapes les plus importantes (max 15 nœuds)
5. Incluez les étapes de validation/décision
6. Utilisez une structure logique du haut vers le bas (TD) ou de gauche à droite (LR)
7. Donnez à chaque nœud un identifiant unique (A, B, C, etc.)

# FORMAT DE SORTIE ATTENDU
Uniquement le code Mermaid sans explications ni commentaires:

```mermaid
graph TD
    A[Début] --> B[Étape 1]
    B --> C{Décision?}
    C -->|Oui| D[Étape 2]
    C -->|Non| E[Étape 3]
    ...
```
"""

    prompt = PromptTemplate(
        input_variables=['procedure'],
        template=template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run({'procedure': procedure_text})
    
    # Nettoyer le résultat pour ne garder que le code Mermaid
    mermaid_pattern = r'```mermaid(.*?)```'
    import re
    match = re.search(mermaid_pattern, result, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return result.strip()
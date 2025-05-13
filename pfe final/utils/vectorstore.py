import os
import json
import streamlit as st
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# Constantes
SIMILARITY_THRESHOLD = 0.6  # Seuil de similarité minimum
MAX_NOTE_LENGTH = 300  # Limite la taille des notes de référence
MAX_EXAMPLES = 2  # Limite le nombre d'exemples à utiliser

@st.cache_resource
def load_embeddings():
    """Charge le modèle d'embeddings"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_data(json_path):
    """
    Charge les données à partir d'un fichier JSON.
    Retourne les documents, les notes et les procédures.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        dossiers = data.get('dossiers') if isinstance(data, dict) else data
        if not isinstance(dossiers, list):
            raise ValueError('Format JSON invalide pour dossiers')

        docs, notes_map, procs_map = [], {}, {}
        for d in dossiers:
            num = d.get('numero')
            note = d.get('note_circulaire', {})
            texte = note.get('texte') if isinstance(note, dict) else ''
            if texte:
                docs.append(Document(page_content=texte, metadata={'numero': num, 'nom': d.get('nom', '')}))
                notes_map[num] = texte
            procs_map[num] = d.get('procedures', [])
        
        return docs, notes_map, procs_map
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return [], {}, {}

@st.cache_resource
def initialize_vectorstore(docs, vs_dir):
    """
    Initialise ou charge la base vectorielle.
    Utilise le cache Streamlit pour éviter de recréer la base à chaque exécution.
    """
    embedder = load_embeddings()
    
    try:
        if os.path.exists(vs_dir) and os.listdir(vs_dir):
            # Charger la base existante
            vs = Chroma(collection_name='notes', persist_directory=vs_dir, embedding_function=embedder)
            return vs
        else:
            # Créer une nouvelle base
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(docs)
            
            # Assurez-vous que le répertoire existe
            os.makedirs(vs_dir, exist_ok=True)
            
            vs = Chroma(collection_name='notes', persist_directory=vs_dir, embedding_function=embedder)
            if chunks:
                vs.add_documents(chunks)
                vs.persist()
            return vs
    except Exception as e:
        st.error(f"Erreur avec la base vectorielle: {e}")
        return None

def find_similar_notes(vectorstore, query, k=2):
    """
    Recherche les notes similaires avec leur score.
    """
    if not vectorstore:
        return []
        
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs={'k': k, 'score_threshold': SIMILARITY_THRESHOLD}
    )
    
    results = retriever.get_relevant_documents(query)
    
    similar_notes = []
    for doc in results:
        note_id = doc.metadata['numero']
        note_title = doc.metadata.get('nom', 'Sans titre')
        score_val = getattr(doc, 'score', 0.0)
        similar_notes.append({
            'id': note_id,
            'titre': note_title,
            'score': score_val,
            'content': doc.page_content
        })
    
    return similar_notes
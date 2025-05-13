import streamlit as st
import os
import pandas as pd
from utils.text_extraction import extract_text_from_pdf
from utils.vectorstore import update_vectorstore, get_document_list
import tempfile

def main():
    st.title("Explorateur de Données et Gestion des Documents")
    st.write("""
    Chargez vos documents de procédures bancaires pour les utiliser dans l'application.
    Les documents chargés seront indexés et disponibles pour la recherche et la génération de réponses.
    """)
    
    # Créer les onglets
    tab1, tab2, tab3 = st.tabs(["📤 Charger des documents", "📚 Documents indexés", "🔍 Recherche de texte"])
    
    with tab1:
        st.header("Charger de nouveaux documents")
        
        # Zone de chargement de fichiers
        uploaded_files = st.file_uploader(
            "Chargez vos documents PDF",
            type=["pdf"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            process_button = st.button("Traiter les documents")
            
            if process_button:
                with st.spinner("Traitement des documents en cours..."):
                    # Créer un dossier temporaire pour stocker les fichiers
                    with tempfile.TemporaryDirectory() as temp_dir:
                        for uploaded_file in uploaded_files:
                            # Enregistrer le fichier dans le dossier temporaire
                            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Extraire le texte du PDF
                            try:
                                extracted_text = extract_text_from_pdf(temp_file_path)
                                
                                # Mettre à jour la base vectorielle
                                update_vectorstore(extracted_text, os.path.basename(temp_file_path))
                                st.success(f"Document '{uploaded_file.name}' traité et indexé avec succès.")
                            except Exception as e:
                                st.error(f"Erreur lors du traitement de '{uploaded_file.name}': {str(e)}")
                
                st.success("Tous les documents ont été traités.")
    
    with tab2:
        st.header("Documents indexés")
        
        try:
            # Récupérer la liste des documents indexés
            documents = get_document_list()
            
            if documents:
                # Créer un DataFrame pour afficher les documents
                docs_df = pd.DataFrame(documents, columns=["Nom du document", "Date d'indexation", "Nombre de chunks"])
                st.dataframe(docs_df, use_container_width=True)
                
                # Option pour supprimer des documents
                if st.button("Supprimer tous les documents"):
                    # Implémenter la suppression de documents
                    # Cette fonctionnalité nécessite une implémentation dans vectorstore.py
                    st.warning("Fonctionnalité non implémentée")
            else:
                st.info("Aucun document n'a été indexé. Veuillez charger des documents dans l'onglet 'Charger des documents'.")
        except Exception as e:
            st.error(f"Erreur lors de la récupération des documents: {str(e)}")
    
    with tab3:
        st.header("Recherche de texte dans les documents")
        
        # Champ de recherche
        search_query = st.text_input("Terme de recherche")
        
        if search_query:
            with st.spinner("Recherche en cours..."):
                try:
                    # Cette fonction doit être implémentée dans vectorstore.py
                    from utils.vectorstore import search_documents
                    results = search_documents(search_query)
                    
                    if results:
                        st.subheader("Résultats de recherche")
                        for i, result in enumerate(results):
                            with st.expander(f"Résultat {i+1} - {result.metadata.get('source', 'Document inconnu')}"):
                                st.write(result.page_content)
                                st.markdown(f"*Score de similarité: {result.metadata.get('score', 'N/A')}*")
                    else:
                        st.info("Aucun résultat trouvé.")
                except Exception as e:
                    st.error(f"Erreur lors de la recherche: {str(e)}")
                    st.info("Assurez-vous que la fonction search_documents est correctement implémentée dans vectorstore.py.")

if __name__ == "__main__":
    main()
import streamlit as st
import os
from utils.vectorstore import get_vectorstore
from utils.llm_utils import get_llm
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

def main():
    st.title("Assistant Questions-Réponses sur les Procédures Bancaires")
    st.write("""
    Posez vos questions sur les procédures bancaires et obtenez des réponses basées sur la documentation disponible.
    """)
    
    # Initialisation de la mémoire de conversation dans la session
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )
    
    # Initialisation de l'historique de chat dans la session
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Récupération de la base vectorielle
    try:
        vectorstore = get_vectorstore()
        
        # Vérification si la base de données vectorielle est vide
        if vectorstore is None:
            st.warning("Aucun document n'a été chargé. Veuillez d'abord charger des documents dans l'explorateur de données.")
            return
        
        # Initialisation du LLM
        llm = get_llm()
        
        # Création de la chaîne de recherche conversationnelle
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            memory=st.session_state.memory,
            return_source_documents=True
        )
        
        # Affichage de l'historique de chat
        for message in st.session_state.chat_history:
            role = "assistant" if message["role"] == "assistant" else "user"
            with st.chat_message(role):
                st.write(message["content"])
        
        # Zone de saisie pour la question
        user_query = st.chat_input("Posez votre question ici...")
        
        if user_query:
            # Ajout de la question à l'historique
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            
            # Affichage de la question
            with st.chat_message("user"):
                st.write(user_query)
            
            # Traitement de la question et récupération de la réponse
            with st.spinner("Recherche en cours..."):
                result = qa_chain({"question": user_query})
                answer = result["answer"]
                source_docs = result.get("source_documents", [])
            
            # Ajout de la réponse à l'historique
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            
            # Affichage de la réponse
            with st.chat_message("assistant"):
                st.write(answer)
                
                # Affichage des sources
                if source_docs:
                    with st.expander("Sources"):
                        for i, doc in enumerate(source_docs):
                            st.markdown(f"**Source {i+1}:**")
                            st.markdown(f"```\n{doc.page_content[:300]}...\n```")
                            st.markdown(f"*Fichier: {doc.metadata.get('source', 'Non spécifié')}*")
        
        # Bouton pour effacer l'historique
        if st.button("Effacer l'historique"):
            st.session_state.memory = ConversationBufferMemory(
                memory_key="chat_history", 
                return_messages=True
            )
            st.session_state.chat_history = []
            st.experimental_rerun()
            
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")
        st.info("Veuillez vérifier que les documents ont été correctement chargés dans l'explorateur de données.")

if __name__ == "__main__":
    main()